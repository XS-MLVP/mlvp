from .asynchronous import Component, Queue

class Model(Component):
    def __init__(self):
        super().__init__()
        self.attached_agent = None

    def is_attached(self):
        return self.attached_agent is not None

    def get_driver_method(self, name: str):
        if hasattr(self, name) and isinstance(getattr(self, name), DriverMethod):
            return getattr(self, name)
        return None

    def get_monitor_method(self, name: str):
        if hasattr(self, name) and isinstance(getattr(self, name), MonitorMethod):
            return getattr(self, name)
        return None

    def get_driver_func(self, name: str):
        if hasattr(self, name) and callable(getattr(self, name)) and \
            not isinstance(getattr(self, name), DriverMethod):
            return getattr(self, name)
        return None

    async def main(self):
        ...


class DriverMethod(Queue):
    async def __call__(self):
        return await self.get()


class MonitorMethod(Queue):
    async def __call__(self, item):
        return await self.put(item)



