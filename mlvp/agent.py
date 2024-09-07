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

        print("hahahh")

        # TODO: forward driver_method call to drivers
        self.drivers = {}
        self.monitors = {}
        self.__create_all_drivers()

        # Env will assign self to all monitor methods
        for monitor_func in self.all_monitor_method():
            create_task(monitor_func(self, config_agent=True))

    def __create_all_drivers(self):
        """
        Create a driver for each driver method in the agent.
        """

        for driver_method in self.all_driver_method():
            driver = Driver(driver_method.__original_func__)
            self.drivers[driver_method.__name__] = driver

    def __create_all_monitors(self):
        """
        Create a monitor for each monitor method in the agent.
        """

        for monitor_method in self.all_monitor_method():
            monitor = Monitor(monitor_method)
            self.monitors[monitor_method.__name__] = monitor

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

import functools

def __driver_wrapped_func(func):
    func.__is_driver_decorated__ = True

    @functools.wraps(func)
    async def wrapper(agent, *args, **kwargs):
        driver = agent.drivers[func.__name__]
        return await driver.process_driver_call(agent, args, kwargs)

    wrapper.__original_func__ = func
    return wrapper

def driver_method():
    """
    Decorator for driver method.

    Returns:
        The decorator for driver method.
    """

    def decorator(func):
        return __driver_wrapped_func(func)
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
