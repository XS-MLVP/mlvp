from .asynchronous import create_task, gather, add_callback
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

add_callback(__execute_priority_tasks)

"""
Executor
"""

class Executor(MObject):
    def __init__(self, exit="all"):

        import asyncio
        self.exit = exit
        self.results = {}
        self.coros = {}


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._wait_for_all()

    async def _wait_for_all(self):
        sche_groups = []
        for tasks in self.coros.items():
            sche_groups.append(self.sequential_execution_all(*tasks[1]))

        results = await gather(*sche_groups)

        result_dict = {}
        for i, tasks in enumerate(self.coros.items()):
            if len(tasks[1]) == 1:
                result_dict[tasks[0]] = results[i][0]
            else:
                result_dict[tasks[0]] = results[i]

        self.results = result_dict


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
    async def sequential_execution_all(*tasks):
        """Sequentially execute all tasks."""

        results = []
        for coro, priority in tasks:
            driver = Executor.get_driver(coro)

            if driver is not None:
                if priority is None:
                    priority = 99

                driver.priority = priority

            results.append(await coro)

        return results

    @staticmethod
    def get_driver(coro):
        function_name = coro.__name__
        locals = coro.cr_frame.f_locals
        return locals.get("__driver_object__", None)
