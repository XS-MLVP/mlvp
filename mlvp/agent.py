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


def driver_method(*, sche_order="model_first", model_priority=99):
    """
    Decorator for driver method.

    Args:
        sche_order:     The order to schedule the driver method. It can be "model_first" or "driver_first".
        model_priority: The default priority to call the model. When multiple model hook calls occur in a cycle, the
                        one with the lowest priority value is called first

    Returns:
        The decorator for driver method.
    """

    def decorator(func):
        driver = Driver(func, sche_order, model_priority)
        return driver.wrapped_func()
    return decorator

def monitor_method():
    """
    Decorator for monitor method.

    Returns:
        The decorator for monitor method.
    """

    def decorator(func):
        monitor = Monitor(func)
        return monitor.wrapped_func()
    return decorator
