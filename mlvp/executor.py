from .asynchronous import create_task, gather, add_callback, Event
from .base import MObject


"""
Priority Task Execution
"""

__priority_tasks = []

def add_priority_task(coro, priority):
    __priority_tasks.append((coro, priority))

async def __execute_priority_tasks():
    for coro, _ in sorted(__priority_tasks, key=lambda x: x[1]):
        await coro
    __priority_tasks.clear()

add_callback(__execute_priority_tasks)

"""
Executor
"""

class Executor(MObject):
    def __init__(self, exit="all"):
        self.exit = exit
        self.uncompleted = []
        self.results = {}
        self.coros = {}

        self.__exit_any_event = Event()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.exit == "all":
            return await self.exit_all()
        elif self.exit == "none":
            return await self.exit_none()
        elif self.exit == "any":
            return await self.exit_any()
        else:
            raise ValueError(f"Invalid exit option: {self.exit}")


    def set_results(self, results):
        result_dict = {}
        for i, tasks in enumerate(self.coros.items()):
            if len(tasks[1]) == 1:
                result_dict[tasks[0]] = results[i][0]
            else:
                result_dict[tasks[0]] = results[i]

        self.results = result_dict

    def get_sche_group(self):
        sche_groups = []
        for tasks in self.coros.items():
            sche_groups.append(self.sequential_execution_all(*tasks[1]))
        return sche_groups

    async def exit_all(self):
        sche_groups = self.get_sche_group()
        results = await gather(*sche_groups)
        self.set_results(results)
        return self.results

    async def exit_none(self):
        sche_groups = self.get_sche_group()
        for coro in sche_groups:
            self.uncompleted.append(create_task(coro))

    async def exit_any(self):
        self.__exit_any_event.clear()
        for tasks in self.coros.items():
            self.uncompleted.append(create_task(self.sequential_execution_all(\
                *tasks[1], complete_event=self.__exit_any_event)))
        await self.__exit_any_event.wait()

    async def wait_all(self):
        if len(self.uncompleted) == 0:
            return

        results = []
        for task in self.uncompleted:
            results.append(await task)
        self.set_results(results)

    def get_results(self):
        return self.results

    def __call__(self, coro, priority=None, sche_group=None):
        if sche_group is None:
            sche_group = coro.__name__

        if sche_group not in self.coros:
            self.coros[sche_group] = []

        if priority is not None:
            driver = Executor.get_driver(coro)
            coro_name = coro.__name__
            assert driver is not None, f"{coro_name} is not a driver function, cannot set priority"

        self.coros[sche_group].append((coro, priority))


    @staticmethod
    async def sequential_execution_all(*tasks, complete_event=None):
        """Sequentially execute all tasks."""

        results = []
        for coro, priority in tasks:
            driver = Executor.get_driver(coro)

            if driver is not None:
                if priority is None:
                    priority = 99

                driver.priority = priority

            results.append(await coro)

        if complete_event is not None and not complete_event.is_set():
            complete_event.set()

        return results

    @staticmethod
    def get_driver(coro):
        function_name = coro.__name__
        locals = coro.cr_frame.f_locals
        return locals.get("__driver_object__", None)
