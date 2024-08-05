from .logger import error, warning
from .model import Model
from .asynchronous import gather, create_task
from .agent import Monitor, Driver

class Env:
    """Provides an environment for operation on the DUT."""

    def __init__(self, monitor_step):
        """
        Args:
            monitor_step: Provide a step function for monitor, and monitor will monitor
                          each step.
        """

        self.attached_model = []

        self.monitor_step = monitor_step

        # Env will assign self to all monitor methods
        for monitor_func in self.__all_monitor_method():
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
            if not driver_method.__is_model_sync__:
                continue

            if driver_method.__is_match_func__:
                if not model.get_driver_func(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver function {driver_method.__name_to_match__}")
            else:
                if not model.get_driver_method(driver_method.__name_to_match__):
                    raise ValueError(f"Model {model} does not have driver method {driver_method.__name_to_match__}")

        for monitor_method in self.__all_monitor_method():
            if not monitor_method.__need_compare__:
                continue

            if not model.get_monitor_method(monitor_method.__name_to_match__):
                raise ValueError(f"Model {model} does not have monitor method {monitor_method.__name_to_match__}")

    def __all_driver_method(self):
        """
        Yields all driver method in the environment.

        Returns:
            A generator that yields all driver method in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_driver_decorated__"):
                yield getattr(self, attr)

    def __all_monitor_method(self):
        """
        Yields all monitor methods in the environment.

        Returns:
            A generator that yields all monitor method in the environment.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_monitor_decorated__"):
                yield getattr(self, attr)


def driver_method(*, model_sync=True, match_func=False, \
                  need_compare=False, compare_func=None, name_to_match=None, sche_order="model_first"):
    """
    Decorator for driver method.

    Args:
        model_sync:    Whether to synchronize the driver method with the model.
        match_func:    Whether to match the function.
        need_compare:  Whether to compare the output with the reference.
        compare_func:  The function to implement the comparison. If it is None, the default.
        name_to_match: The name to match the driver method or function in the model.

    Returns:
        The decorator for driver method.
    """

    def decorator(func):
        driver = Driver(func, model_sync, match_func, \
                        need_compare, compare_func, name_to_match, sche_order)
        return driver.wrapped_func()
    return decorator

def monitor_method(*, need_compare=True, auto_monitor=True, compare_func=None, name_to_match=None):
    """
    Decorator for monitor method.

    Args:
        need_compare:  Whether to compare the output with the reference.
        auto_monitor:  Whether to monitor automatically. If True, the monitor will monitor the DUT forever in the
                       background.
        compare_func:  The function to implement the comparison. If it is None, the default
                       comparison function will be used.
        name_to_match: The name to match the monitor method.

    Returns:
        The decorator for monitor method.
    """

    def decorator(func):
        monitor = Monitor(func, need_compare, auto_monitor, compare_func, name_to_match)
        return monitor.wrapped_func()
    return decorator
