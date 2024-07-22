from . import Component, Port

class Driver(Component):
    def __init__(self, bundle):
        super().__init__()
        self.port = Port()
        self.bundle = bundle

    async def main(self):
        while True:
            item = await self.port.get()
            await self.driver_method(item)

    async def driver_method(self, item):
        self.bundle.assign(item)
        await self.bundle.step()

class Monitor(Component):
    def __init__(self, bundle):
        super().__init__()
        self.port = Port()
        self.bundle = bundle

    async def main(self):
        while True:
            if self.condition():
                item = await self.monitor_method()
                await self.port.put(item)
            await self.bundle.step()

    def condition(self):
        return True

    async def monitor_method(self):
        dict = self.bundle.as_dict()
        await self.bundle.step()
        return dict
