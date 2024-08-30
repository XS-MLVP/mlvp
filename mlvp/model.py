from .asynchronous import Component, Queue
from .logger import warning

def agent_hook(agent_name: str = ""):
    """
    Decorator for agent hook.

    Args:
        agent_name: The name of the agent to be hooked. If it is empty, the name of the function will be used.
    """

    def decorator(func):
        nonlocal agent_name

        if agent_name == "":
            agent_name = func.__name__

        func.__is_agent_hook__ = True
        func.__agent_name__ = agent_name
        func.__matched__ = False

        return func

    return decorator

def driver_hook(driver_path: str = "", agent_name: str = "", driver_name: str = ""):
    """
    Decorator for driver hook.

    Args:
        driver_path: The path of the driver.
        agent_name:  The name of the agent to be hooked.
        driver_name: The name of the driver to be hooked.
    """

    assert driver_path != "" or (agent_name == "" and driver_name == ""), \
        "agent_name and driver_name must be empty when driver_path is set"

    assert agent_name != "" or driver_name == "", \
        "agent_name must not be empty when driver_name is set"

    def decorator(func):
        nonlocal driver_path, agent_name, driver_name

        if driver_path == "":
            if agent_name == "":
                if driver_name != "":
                    driver_path = f"{driver_path}.{driver_name}"
                else:
                    driver_path = f"{driver_path}.{func.__name__}"
            else:
                driver_path = func.__name__.replace("_", ".")

        func.__is_driver_hook__ = True
        func.__driver_path__ = driver_path
        func.__matched__ = False

        return func

    return decorator

class Port(Queue):
    def __init__(self, name: str = ""):
        super().__init__()

        self.name = name
        self.matched = False

class DriverPort(Port):
    """
    A The DriverPort is used to match the DriverPort of the agent, and it is used to accept requests from the agent.
    """

    async def __call__(self):
        return await self.get()

class AgentPort(DriverPort):
    ...

class MonitorPort(Port):
    """
    The MonitorPort is used to match the MonitorPort in the agent, and it is used for the Model to send the results
    out and compare them with the results in the agent.
    """

    async def __call__(self, item):
        return await self.put(item)

class Model(Component):
    """
    The Model is used to provide a reference model for the DUT.
    """

    def __init__(self):
        super().__init__()
        self.attached_agent = None

        self.all_agent_ports = []
        self.all_driver_ports = []
        self.all_monitor_ports = []
        self.all_driver_hooks = []
        self.all_agent_hooks = []

        self.__collect_all()

    def __collect_all(self):
        """
        Collect all driver ports, monitor ports, driver hooks, and agent hooks.
        """

        self.all_agent_ports.clear()
        self.all_driver_ports.clear()
        self.all_monitor_ports.clear()
        self.all_driver_hooks.clear()
        self.all_agent_hooks.clear()

        for attr in dir(self):
            attr_value = getattr(self, attr)

            if isinstance(attr_value, Port):
                if attr_value.name == "":
                    attr_value.name = attr

                if isinstance(attr_value, DriverPort):
                    self.all_driver_ports.append(attr_value)
                elif isinstance(attr_value, MonitorPort):
                    self.all_monitor_ports.append(attr_value)
                elif isinstance(attr_value, AgentPort):
                    self.all_agent_ports.append(attr_value)

            elif callable(attr_value) and hasattr(attr_value, "__is_driver_hook__"):
                self.all_driver_hooks.append(attr_value)

            elif callable(attr_value) and hasattr(attr_value, "__is_agent_hook__"):
                self.all_agent_hooks.append(attr_value)

    def is_attached(self):
        """
        Check if the model is attached to an agent.
        """

        return self.attached_agent is not None

    def check_unmatched(self):
        """
        Check if all driver hooks and agent hooks are matched.
        """

        for driver_hook in self.all_driver_hooks:
            if not driver_hook.__matched__:
                warning(f"Driver hook {driver_hook.__driver_path__} is not matched")

        for agent_hook in self.all_agent_hooks:
            if not agent_hook.__matched__:
                warning(f"Agent hook {agent_hook.__agent_name__} is not matched")

        for driver_port in self.all_driver_ports:
            if not driver_port.matched:
                warning(f"Driver port {driver_port.name} is not matched")

        for monitor_port in self.all_monitor_ports:
            if not monitor_port.matched:
                warning(f"Monitor port {monitor_port.name} is not matched")

    def get_driver_port(self, name: str):
        """
        Get the driver port by name.
        """

        for driver_port in self.all_driver_ports:
            if driver_port.name == name:
                return driver_port

    def get_monitor_port(self, name: str):
        """
        Get the monitor port by name.
        """

        for monitor_port in self.all_monitor_ports:
            if monitor_port.name == name:
                return monitor_port

    def get_driver_hook(self, driver_path: str):
        """
        Get the driver hook by name.
        """

        for driver_hook in self.all_driver_hooks:
            if driver_hook.__driver_path__ == driver_path:
                return driver_hook

    def get_agent_port(self, name: str):
        """
        Get the agent port by name.
        """

        for agent_port in self.all_agent_ports:
            if agent_port.name == name:
                return agent_port

    def get_agent_hook(self, name: str):
        """
        Get the agent hook by name.
        """

        for agent_hook in self.all_agent_hooks:
            if agent_hook.__agent_name__ == name:
                return agent_hook

    async def main(self):
        ...
