from .asynchronous import Component, Queue

class Model(Component):
    """
    The Model is used to provide a reference model for the DUT.
    """

    def __init__(self):
        super().__init__()
        self.attached_agent = None

    def is_attached(self):
        """
        Check if the model is attached to an agent.
        """

        return self.attached_agent is not None

    def get_driver_method(self, name: str):
        """
        Get the driver method by name.
        """

        if hasattr(self, name) and isinstance(getattr(self, name), DriverMethod):
            return getattr(self, name)
        return None

    def get_monitor_method(self, name: str):
        """
        Get the monitor method by name.
        """

        if hasattr(self, name) and isinstance(getattr(self, name), MonitorMethod):
            return getattr(self, name)
        return None

    def get_driver_func(self, name: str):
        """
        Get the driver function by name.
        """

        if hasattr(self, name) and callable(getattr(self, name)) and \
            not isinstance(getattr(self, name), DriverMethod):
            return getattr(self, name)
        return None

    async def main(self):
        ...


class DriverMethod(Queue):
    """
    A The DriverMethod is used to match the drivermethod of the agent, and it is used to accept requests from the agent.
    """

    async def __call__(self):
        return await self.get()

class MonitorMethod(Queue):
    """
    The MonitorMethod is used to match the monitormethod in the agent, and it is used for the Model to send the results
    out and compare them with the results in the agent.
    """

    async def __call__(self, item):
        return await self.put(item)
