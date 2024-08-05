import functools
import inspect
from .compare import Comparator, compare_once
from .asynchronous import create_task, Queue
from .executor import add_priority_task
from .logger import critical

class BaseAgent:
    def __init__(self, func, name_to_match: str, need_compare, compare_func):
        self.func = func
        self.name = func.__name__
        self.name_to_match = name_to_match
        self.need_compare = need_compare
        self.compare_func = compare_func

        if self.name_to_match is None:
            self.name_to_match = self.name

        func.__name_to_match__ = self.name_to_match


class Driver(BaseAgent):
    """
    The Driver is used to drive the DUT and forward the driver information to
    the reference model.
    """

    def __init__(self, drive_func, model_sync, match_func, \
                  need_compare, compare_func, name_to_match, sche_order):
        super().__init__(drive_func, name_to_match, need_compare, compare_func)

        self.model_sync = model_sync
        self.match_func = match_func
        self.sche_order = sche_order

        self.priority = 99

        assert model_sync or not need_compare, "need_compare can be true only if model_sync is true"
        assert match_func or not need_compare, "need_compare can be true only if match_func is true"
        assert need_compare or compare_func is None, "compare_func takes effect only if need_compare is true"

        self.func.__driver__ = self
        self.func.__is_driver_decorated__ = True
        self.func.__is_match_func__ = match_func
        self.func.__is_model_sync__ = model_sync

    def __get_args_dict(self, arg_list, kwarg_list):
        """
        Get the args and kwargs in the form of dictionary.

        Args:
            arg_list: The list of args.
            kwarg_list: The list of kwargs.

        Returns:
            The args and kwargs in the form of dictionary.
        """

        signature = inspect.signature(self.func)
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

        if not self.need_compare:
            return

        for model_result in model_results:
            compare_once(dut_result, model_result, self.compare_func, match_detail=True)

    async def model_exec_wrapper(self, model_coro, results, compare_func):
        results["model_results"] = await model_coro

        if results["dut_result"] is not None:
            compare_func(results["dut_result"], results["model_results"])

    async def process_driver_call(self, agent, arg_list, kwarg_list):
        """
        Process the driver call.

        Args:
            agent: The agent of DUT.
            arg_list: The list of args.
            kwarg_list: The list of kwargs.

        Returns:
            The result of the DUT if imme_ret is False, otherwise None.
        """

        results = {"dut_result": None, "model_results": None}

        model_coro = self.model_exec_wrapper(
            self.forward_to_models(agent.attached_model, arg_list, kwarg_list),
            results,
            self.compare_results
        )

        if self.sche_order == "model_first":
            add_priority_task(model_coro, self.priority)

            results["dut_result"] = await self.func(agent, *arg_list, **kwarg_list)
            if results["model_results"] is not None:
                self.compare_results(results["dut_result"], results["model_results"])

        elif self.sche_order == "dut_first":
            results["dut_result"] = await self.func(agent, *arg_list, **kwarg_list)
            add_priority_task(model_coro, self.priority)

        else:
            raise ValueError(f"Invalid sche_order: {self.sche_order}")

        return results["dut_result"]

    def wrapped_func(self):
        """
        Wrap the original driver function.

        Returns:
            The wrapped driver function.
        """

        # In executor, we use __driver_object__ to get the driver object.
        __driver_object__ = self

        @functools.wraps(self.func)
        async def wrapper(agent, *args, **kwargs):
            return await __driver_object__.process_driver_call(agent, args, kwargs)
        return wrapper


class Monitor(BaseAgent):
    """
    The Monitor is used to monitor the DUT and compare the output with the reference.
    """

    def __init__(self, monitor_func, need_compare, auto_monitor, compare_func, name_to_match):
        super().__init__(monitor_func, name_to_match, need_compare, compare_func)

        self.compare_queue = Queue()
        self.get_queue = Queue()
        self.auto_monitor = auto_monitor

        self.agent = None
        self.comparator = None
        self.monitor_task = None

        self.func.__is_monitor_decorated__ = True
        self.func.__need_compare__ = need_compare

    def __start(self, agent):
        """
        Start the monitor.

        Args:
            agent: The agent of DUT.
        """

        self.agent = agent

        if self.auto_monitor:
            self.monitor_task = create_task(self.__monitor_forever())

        if self.need_compare:
            model_ports = []
            for model in agent.attached_model:
                model_ports.append(model.get_monitor_method(self.name_to_match))
            self.comparator = Comparator(self.compare_queue, model_ports, compare=self.compare_func, match_detail=True)

    def get_queue_size(self):
        """
        Get the size of the get queue.

        Returns:
            The size of the get queue.
        """

        return self.get_queue.qsize()

    def wrapped_func(self):
        """
        Wrap the original monitor function.

        Returns:
            The wrapped monitor function.
        """

        monitor = self

        @functools.wraps(monitor.func)
        async def wrapper(agent, *args, **kwargs):
            if 'config_agent' in kwargs and kwargs['config_agent']:
                monitor.__start(agent)
                return

            if monitor.auto_monitor:
                return await monitor.get_queue.get()
            else:
                item = await monitor.func(agent, *args, **kwargs)
                await monitor.compare_queue.put(item)
                return item

        wrapper.size = self.get_queue_size

        return wrapper

    async def __monitor_forever(self):
        """Monitor the DUT forever."""

        while True:
            ret = await self.func(self.agent)
            if ret is not None:
                await self.get_queue.put(ret)
                await self.compare_queue.put(ret)
            await self.agent.monitor_step()
