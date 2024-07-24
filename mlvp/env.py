import functools
from .logger import critical, error, info, warning
from .model import Model
from .compare import Comparator
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

    async def drive_completed(self):
        """Drive all the tasks in the drive queue."""

        # Group all tasks by function name
        all_tasks = {}
        for item in self.drive_queue:
            func_name = item["func"].__name__
            if func_name not in all_tasks:
                all_tasks[func_name] = []
            all_tasks[func_name].append(item["func"](self, *item["args"], **item["kwargs"]))

        # Generate all tasks to be executed
        task_names = []
        tasks_to_exec = []
        for func_name, tasks in all_tasks.items():
            task_names.append(func_name)
            if len(tasks) == 1:
                tasks_to_exec.append(tasks[0])
            else:
                tasks_to_exec.append(self.__sequential_execution_all(*tasks))

        # Execute all tasks
        results = await gather(*tasks_to_exec)
        self.drive_queue.clear()

        return dict(zip(task_names, results))

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

    def __init__(self, drive_func, model_sync, imme_ret):
        self.drive_func = drive_func
        self.model_sync = model_sync
        self.imme_ret = imme_ret

        self.drive_func.__is_driver_decorated__ = True

    async def __forward_to_model(self, item, models):
        """
        Forward the item to the models.

        Args:
            item: The item to be forwarded.
            models: The models to be forwarded to.
        """

        if not self.model_sync:
            return

        for model in models:
            target = model.get_driver_method(self.drive_func.__name__)
            if target is not None:
                await target.put(item)
            else:
                critical(f"Model {model} does not have driver method \
                            {self.drive_func.__name__}")

    async def __drive_dut(self, env, args_list, kwargs_list):
        """
        Drive the DUT.

        Args:
            args_list: The list of args.
            kwargs_list: The list of kwargs.
        """

        if self.imme_ret:
            env.drive_queue.append({
                "func": self.drive_func,
                "args": args_list,
                "kwargs": kwargs_list
            })
        else:
            await self.drive_func(env, *args_list, **kwargs_list)

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

            await driver.__forward_to_model(args[0], env.attached_model)
            await driver.__drive_dut(env, args, kwargs)
        return wrapper


def driver_method(*, model_sync=True, imme_ret=True):
    """
    Decorator for driver method.

    Args:
        model_sync: Whether to synchronize the driver method with the model.
        imme_ret: Whether to return immediately.
    """

    def decorator(func):
        driver = Driver(func, model_sync=model_sync, imme_ret=imme_ret)
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
