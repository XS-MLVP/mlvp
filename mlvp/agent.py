import functools
import inspect
from .compare import Comparator, compare_once
from .asynchronous import create_task, Queue
from .logger import critical

class BaseAgent:
    def __init__(self, func, name_to_match: str):
        self.name = func.__name__
        self.name_to_match = name_to_match

        if self.name_to_match is None:
            self.name_to_match = self.name

        func.__name_to_match__ = self.name_to_match


class Driver(BaseAgent):
    """
    The Driver is used to drive the DUT and forward the driver information to
    the reference model.
    """

    def __init__(self, drive_func, model_sync, imme_ret, match_func, \
                  result_compare, compare_method, name_to_match):
        super().__init__(drive_func, name_to_match)

        self.drive_func = drive_func
        self.model_sync = model_sync
        self.imme_ret = imme_ret

        self.match_func = match_func
        self.result_compare = result_compare
        self.compare_method = compare_method

        assert model_sync or not result_compare, "result_compare can be true only if model_sync is true"
        assert match_func or not result_compare, "result_compare can be true only if match_func is true"
        assert result_compare or compare_method is None, "compare_method takes effect only if result_compare is true"

        self.drive_func.__is_driver_decorated__ = True
        self.drive_func.__is_match_func__ = match_func
        self.drive_func.__is_model_sync__ = model_sync

    def __get_args_dict(self, arg_list, kwarg_list):
        """
        Get the args and kwargs in the form of dictionary.

        Args:
            arg_list: The list of args.
            kwarg_list: The list of kwargs.

        Returns:
            The args and kwargs in the form of dictionary.
        """

        signature = inspect.signature(self.drive_func)
        bound_args = signature.bind(None, *arg_list, **kwarg_list)
        bound_args.apply_defaults()
        arguments = bound_args.arguments
        del arguments["self"]
        return arguments

    async def __drive_single_model(self, model, arg_list, kwarg_list):
        """
        Drive a single model.

        Args:
            model: The model to be driven.
            arg_list: The list of args.
            kwarg_list: The list of kwargs.

        Returns:
            The result of the model.
        """

        if self.match_func:
            target = model.get_driver_func(self.name_to_match)

            if target is None:
                critical(f"Model {model} does not have driver function \
                            {self.name_to_match}")

            if inspect.iscoroutinefunction(target):
                result = await target(*arg_list, **kwarg_list)
            else:
                result = target(*arg_list, **kwarg_list)

            return result
        else:
            target = model.get_driver_method(self.name_to_match)
            if target is not None:
                args_dict = self.__get_args_dict(arg_list, kwarg_list)
                args = next(iter(args_dict.values())) if len(args_dict) == 1 else args_dict
                await target.put(args)
            else:
                critical(f"Model {model} does not have driver method \
                            {self.name_to_match}")

    async def forward_to_models(self, models, arg_list, kwarg_list):
        """
        Forward the item to the models.

        Args:
            models: The models to be forwarded to.
            arg_list: The list of args.
            kwarg_list: The list of kwargs.
        """

        if not self.model_sync:
            return

        results = []
        for model in models:
            results.append(await self.__drive_single_model(model, arg_list, kwarg_list))

        return results

    def compare_results(self, dut_result, model_results):
        """
        Compare the result of the DUT and the models.

        Args:
            dut_result: The result of the DUT.
            model_results: The results of the models.
        """

        if not self.result_compare:
            return

        for model_result in model_results:
            compare_once(dut_result, model_result, self.compare_method, match_detail=True)

    async def __process_driver_call(self, env, arg_list, kwarg_list):
        """
        Process the driver call.

        Args:
            env: The environment of DUT.
            arg_list: The list of args.
            kwarg_list: The list of kwargs.

        Returns:
            The result of the DUT if imme_ret is False, otherwise None.
        """

        if self.imme_ret:
            env.drive_queue.append({
                "driver": self,
                "args": arg_list,
                "kwargs": kwarg_list
            })

        else:
            model_results = await self.forward_to_models(env.attached_model, \
                                                            arg_list, kwarg_list)
            dut_result = await self.drive_func(env, *arg_list, **kwarg_list)

            if self.result_compare:
                self.compare_results(dut_result, model_results)
            return dut_result

    def wrapped_func(self):
        """
        Wrap the original driver function.

        Returns:
            The wrapped driver function.
        """

        driver = self

        @functools.wraps(self.drive_func)
        async def wrapper(self, *args, **kwargs):
            env: Env = self
            return await driver.__process_driver_call(env, args, kwargs)
        return wrapper


class Monitor(BaseAgent):
    """
    The Monitor is used to monitor the DUT and compare the output with the reference.
    """

    def __init__(self, monitor_func, model_compare, auto_monitor, compare_func, name_to_match):
        super().__init__(monitor_func, name_to_match)

        self.compare_queue = Queue()
        self.get_queue = Queue()

        self.monitor_func = monitor_func
        self.model_compare = model_compare
        self.auto_monitor = auto_monitor
        self.compare_func = compare_func

        self.env = None
        self.comparator = None
        self.monitor_task = None

        self.monitor_func.__is_monitor_decorated__ = True
        self.monitor_func.__is_model_compare__ = model_compare

    def __start(self, env):
        """
        Start the monitor.

        Args:
            env: The environment of DUT.
        """

        self.env = env

        if self.auto_monitor:
            self.monitor_task = create_task(self.__monitor_forever())

        if self.model_compare:
            model_ports = []
            for model in env.attached_model:
                model_ports.append(model.get_monitor_method(self.name_to_match))
            self.comparator = Comparator(self.compare_queue, model_ports, compare=self.compare_func, match_detail=True)

    def wrapped_func(self):
        """
        Wrap the original monitor function.

        Returns:
            The wrapped monitor function.
        """

        monitor = self

        @functools.wraps(monitor.monitor_func)
        async def wrapper(self, *args, **kwargs):
            env = self

            if 'config_env' in kwargs and kwargs['config_env']:
                monitor.__start(env)
                return

            if monitor.auto_monitor:
                return await monitor.get_queue.get()
            else:
                item = await monitor.monitor_func(env, *args, **kwargs)
                await monitor.compare_queue.put(item)
                return item
        return wrapper

    async def __monitor_forever(self):
        """Monitor the DUT forever."""

        while True:
            ret = await self.monitor_func(self.env)
            if ret is not None:
                await self.get_queue.put(ret)
                await self.compare_queue.put(ret)
            await self.env.monitor_step()
