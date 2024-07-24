import functools
import inspect
from .logger import critical, error, info, warning
from .model import Model
from .compare import Comparator, compare_once
from .asynchronous import gather, create_task, Queue, Component

class Env:
    """Provides an environment for operation on the DUT."""

    def __init__(self, monitor_step):
        """
        Args:
            monitor_step: Provide a step function for monitor, and monitor will monitor
                          each step.
        """

        self.drive_queue = []
        self.attached_model = []

        self.monitor_step = monitor_step

        # Env will assign self to all monitor methods
        for func_name in self.__all_monitor_method():
            monitor_func = getattr(self, func_name)
            create_task(monitor_func(self, config_env=True))

    def attach(self, model):
        """
        Attach a model to the environment.

        Args:
            model: The model to be attached.

        Returns:
            The environment itself.
        """

        self.__ensure_model_match(model)
        if model.is_attached():
            warning(f"Model {model} is already attached to an environment, the original \
                    environment will be replaced")
            model.attached_env = None

        self.attached_model.append(model)

        return self

    def unattach(self, model):
        """
        Unattach a model from the environment.

        Args:
            model: The model to be unattached.

        Returns:
            The environment itself.
        """

        if model in self.attached_model:
            self.attached_model.remove(model)
            model.attached_env = None
        else:
            error(f"Model {model} is not attached to the environment")

        return self

    async def __get_model_results(self):
        """
        Get the results from the models.
        It will add the results to the drive queue with the key "model_results".
        """

        for item in self.drive_queue:
            driver: Driver = item["driver"]

            results = await driver.forward_to_models(self.attached_model, \
                                                     item["args"], item["kwargs"])
            item["model_results"] = results

    async def __get_dut_results(self):
        """
        Get the results from the DUT.
        It will add the results to the drive queue with the key "dut_result".
        """

        # Group all tasks by function name
        all_tasks = {}
        for index, item in enumerate(self.drive_queue):
            func = item["driver"].drive_func
            func_name = func.__name__

            if func_name not in all_tasks:
                all_tasks[func_name] = []

            all_tasks[func_name].append((index, func(self, *item["args"], **item["kwargs"])))

        # Generate all tasks to be executed
        task_names = []
        task_indexes = []
        tasks_to_exec = []
        for func_name, tasks in all_tasks.items():
            task_names.append(func_name)
            if len(tasks) == 1:
                tasks_to_exec.append(tasks[0][1])
                task_indexes.append([tasks[0][0]])
            else:
                tasks = [item[1] for item in tasks]
                task_indexes.append([item[0] for item in tasks])
                tasks_to_exec.append(self.__sequential_execution_all(*tasks))

        # Execute all tasks
        results = await gather(*tasks_to_exec)

        # Add the results to the drive queue
        for func_results, indexes in zip(results, task_indexes):
            if not isinstance(func_results, list):
                func_results = [func_results]

            for index, result in zip(indexes, func_results):
                print(index, result)
                self.drive_queue[index]["dut_result"] = result

        return dict(zip(task_names, results))

    def __compare_results(self):
        """Compare the results of the DUT and the models."""

        for item in self.drive_queue:
            driver: Driver = item["driver"]
            if driver.result_compare:
                driver.compare_results(item["dut_result"], item["model_results"])

    async def drive_completed(self):
        """Drive all the tasks in the drive queue."""

        await self.__get_model_results()
        dut_result = await self.__get_dut_results()
        self.__compare_results()
        self.drive_queue.clear()

        return dut_result

    @staticmethod
    async def __sequential_execution_all(*tasks):
        """Sequentially execute all tasks."""

        results = []
        for task in tasks:
            results.append(await task)
        return results

    def __ensure_model_match(self, model):
        """
        Make sure the model matches the env.

        Args:
            model: The model to be checked.

        Raises:
            ValueError: If the model does not match the env.
        """

        if not isinstance(model, Model):
            raise ValueError(f"Model {model} is not an instance of Model")

        for driver_method in self.__all_driver_method():
            if getattr(self, driver_method).__is_match_func__:
                if not model.get_driver_func(driver_method):
                    raise ValueError(f"Model {model} does not have driver function {driver_method}")
            else:
                if not model.get_driver_method(driver_method):
                    raise ValueError(f"Model {model} does not have driver method {driver_method}")

        for monitor_method in self.__all_monitor_method():
            if not model.get_monitor_method(monitor_method):
                raise ValueError(f"Model {model} does not have monitor method {monitor_method}")

    def __all_driver_method(self):
        """
        Yields all driver method names in the environment.

        Returns:
            A generator that yields all driver method names in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_driver_decorated__"):
                yield attr

    def __all_monitor_method(self):
        """
        Yields all monitor method names in the environment.

        Returns:
            A generator that yields all monitor method names in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_monitor_decorated__"):
                yield attr

class Driver:
    """
    The Driver is used to drive the DUT and forward the driver information to
    the reference model.
    """

    def __init__(self, drive_func, model_sync, imme_ret, match_func, \
                  result_compare, compare_method):
        self.drive_func = drive_func
        self.model_sync = model_sync
        self.imme_ret = imme_ret
        self.match_func = match_func
        self.result_compare = result_compare
        self.compare_method = compare_method

        self.drive_func.__is_driver_decorated__ = True
        self.drive_func.__is_match_func__ = match_func

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
            target = model.get_driver_func(self.drive_func.__name__)

            if target is None:
                critical(f"Model {model} does not have driver function \
                            {self.drive_func.__name__}")

            if inspect.iscoroutinefunction(target):
                result = await target(*arg_list, **kwarg_list)
            else:
                result = target(*arg_list, **kwarg_list)

            return result
        else:
            target = model.get_driver_method(self.drive_func.__name__)
            if target is not None:
                await target.put(arg_list[0])
            else:
                critical(f"Model {model} does not have driver method \
                            {self.drive_func.__name__}")

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

        print("Comparing results", dut_result, model_results)
        for model_result in model_results:
            compare_once(dut_result, model_result, self.compare_method)

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


def driver_method(*, model_sync=True, imme_ret=True, match_func=False, \
                  result_compare=False, compare_method=None):
    """
    Decorator for driver method.

    Args:
        model_sync: Whether to synchronize the driver method with the model.
        imme_ret: Whether to return immediately.
    """

    def decorator(func):
        driver = Driver(func, model_sync, imme_ret, match_func, \
                        result_compare, compare_method)
        return driver.wrapped_func()
    return decorator


class Monitor:
    """
    The Monitor is used to monitor the DUT and compare the output with the reference.
    """

    def __init__(self, monitor_func, model_compare, auto_monitor, compare_func):
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
                model_ports.append(model.get_monitor_method(self.monitor_func.__name__))
            self.comparator = Comparator(self.compare_queue, model_ports, compare=self.compare_func)

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


def monitor_method(*, model_compare=True, auto_monitor=True, compare_func=None):
    """
    Decorator for monitor method.

    Args:
        model_compare: Whether to compare the output with the reference.
        auto_monitor: Whether to monitor automatically. If True, the monitor will
                      monitor the DUT forever in the background.
        compare_func: The function to implement the comparison. If it is None, the default
                      comparison function will be used.

    Returns:
        The decorator for monitor method.
    """

    def decorator(func):
        monitor = Monitor(func, model_compare, auto_monitor, compare_func)
        return monitor.wrapped_func()
    return decorator
