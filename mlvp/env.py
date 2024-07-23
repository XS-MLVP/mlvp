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

        all_tasks = []
        for item in self.drive_queue:
            all_tasks.append(item["func"](self, *item["args"], **item["kwargs"]))
        self.drive_queue.clear()
        await gather(*all_tasks)

        # TODO: Return the result of all tasks


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



def driver_method(*, model_sync=True, imme_ret=True):
    def decorator(func):
        func.__is_driver_decorated__ = True

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            env = self
            for model in env.attached_model:
                target = model.get_driver_method(func.__name__)
                if target is not None:
                    await target.put(args[0])
                else:
                    critical(f"Model {model} does not have driver method {func.__name__}")

            if imme_ret:
                self.drive_queue.append({
                    "func": func,
                    "args": args,
                    "kwargs": kwargs
                })
            else:
                await func(self, *args, **kwargs)
        return wrapper

    return decorator




def monitor_method(*, model_compare=True, keep_monitor=True, compare_func=None):
    queue = Queue()
    monitor = None
    comparator = None

    class Monitor(Component):
        def __init__(self, env, func):
            super().__init__()
            self.env = env
            self.func = func

        async def main(self):
            while True:
                ret = await self.func(self.env)
                if ret is not None:
                    await queue.put(ret)
                await self.env.monitor_step()

    def decorator(func):
        func.__is_monitor_decorated__ = True

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            if 'config_env' in kwargs and kwargs['config_env']:
                global monitor
                global comparator
                monitor = Monitor(self, func)

                model_ports = []
                for model in self.attached_model:
                    model_ports.append(model.get_monitor_method(func.__name__))
                comparator = Comparator(queue, model_ports, compare=compare_func)

                return

            return await func(self, *args, **kwargs)

        return wrapper
    return decorator
