from . import Component, Port

class Driver(Component):
    def __init__(self, bundle, driver_method=None):
        super().__init__()
        self.port = Port()
        self.bundle = bundle

        self.driver_method = Driver.__default_driver_method \
                                if driver_method is None else driver_method

    async def main(self):
        while True:
            item = await self.port.get()
            await self.driver_method(self.bundle, item)

    @staticmethod
    async def __default_driver_method(bundle, item):
        bundle.assign(item)
        await bundle.step()

class Monitor(Component):
    def __init__(self, bundle, condition=None, monitor_method=None):
        super().__init__()
        self.port = Port()
        self.bundle = bundle

        self.condition = Monitor.__default_condition if condition is None else condition
        self.monitor_method = Monitor.__default_monitor_method \
                                if monitor_method is None else monitor_method

    async def main(self):
        while True:
            if self.condition(self.bundle):
                item = await self.monitor_method(self.bundle)
                await self.port.put(item)
            else:
                await self.bundle.step()

    @staticmethod
    def __default_condition(bundle):
        return True

    @staticmethod
    async def __default_monitor_method(bundle):
        dict = bundle.as_dict()
        await bundle.step()
        return dict
