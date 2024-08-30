from .logger import error, warning
from .model import Model
from .asynchronous import gather, create_task
from .base_agent import Monitor, Driver

class Agent:
    """Provides an agent for operation on the DUT."""

    def __init__(self, monitor_step):
        """
        Args:
            monitor_step: Provide a step function for monitor, and monitor will monitor
                          each step.
        """

        self.monitor_step = monitor_step

        # Env will assign self to all monitor methods
        for monitor_func in self.all_monitor_method():
            create_task(monitor_func(self, config_agent=True))

    def all_driver_method(self):
        """
        Yields all driver method in the agent.

        Returns:
            A generator that yields all driver method in the agent.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_driver_decorated__"):
                yield getattr(self, attr)

    def all_monitor_method(self):
        """
        Yields all monitor methods in the agent.

        Returns:
            A generator that yields all monitor method in the agent.
        """

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_monitor_decorated__"):
                yield getattr(self, attr)

    def get_driver_method(self, name):
        """Get the driver method by name."""

        if hasattr(self, name):
            driver_method = getattr(self, name)

            if hasattr(driver_method, "__is_driver_decorated__"):
                return driver_method

    def get_monitor_method(self, name):
        """Get the monitor method by name."""

        if hasattr(self, name):
            monitor_method = getattr(self, name)

            if hasattr(monitor_method, "__is_monitor_decorated__"):
                return monitor_method


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
        sche_order:    The order to schedule the driver method. If it is "model_first", the model will be scheduled
                       first. If it is "driver_first", the driver method will be scheduled first.

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
