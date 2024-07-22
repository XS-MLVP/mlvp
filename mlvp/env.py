import functools
from .asynchronous import gather, create_task, Queue, Component

class Env:
    def __init__(self, monitor_step):
        self.drive_queue = []
        self.__attached_model = []

        self.monitor_step = monitor_step

        for attr in dir(self):
            if hasattr(getattr(self, attr), "__is_monitor_decorated__"):
                monitor_func = getattr(self, attr)
                create_task(monitor_func(self, config_env=True))


    def attach(self, model):
        self.__attached_model.append(model)

    async def drive_completed(self):
        all_tasks = []
        for item in self.drive_queue:
            all_tasks.append(item["func"](self, *item["args"], **item["kwargs"]))
        await gather(*all_tasks)




def driver_method(*, model_sync=True, imme_ret=True):
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
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

def monitor_method(*, model_compare=True, keep_monitor=True):
    queue = Queue()
    monitor = None

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
                monitor = Monitor(self, func)
                return

            await func(self, *args, **kwargs)

        return wrapper
    return decorator
