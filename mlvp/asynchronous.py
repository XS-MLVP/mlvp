import sys
import asyncio
from .bundle import Bundle

# Asynchronous event definition

new_task_run = False

def task_run():
    global new_task_run
    new_task_run = True

def __has_unwait_task():
    for task in asyncio.all_tasks():

        if task.get_name() == "__clock_loop":
            continue

        if task._fut_waiter is None or task._fut_waiter._state == "FINISHED":
            return True

    return False

async def __run_once():
    global new_task_run

    new_task_run = False
    await asyncio.sleep(0)

async def other_tasks_done():
    global new_task_run
    await __run_once()
    while __has_unwait_task() or new_task_run:
        await __run_once()

class Event(asyncio.Event):
    def __init__(self):
        super().__init__()

    async def wait(self):
        await super().wait()
        task_run()

class Queue(asyncio.Queue):
    def __init__(self):
        super().__init__()

    async def put(self, item):
        await super().put(item)
        task_run()

    async def get(self):
        ret = await super().get()
        task_run()
        return ret


async def sleep(delay: float):
    await asyncio.sleep(delay)
    task_run()

# Asynchronous core function

create_task = asyncio.create_task

async def __clock_loop(dut):
    global new_task_run

    while True:
        await other_tasks_done()
        dut.Step(1)
        dut.event.set()
        dut.event.clear()

def start_clock(dut):
    task = create_task(__clock_loop(dut))
    task.set_name("__clock_loop")


def set_clock_event(dut, loop):
    new_event = asyncio.Event(loop=loop)
    dut.xclock._step_event = new_event
    dut.event = new_event

    for xpin_info in Bundle.dut_all_signals(dut):
        xpin = xpin_info["signal"]
        xpin.event = new_event
        print(xpin.event, new_event)

def run(coro, dut=None):
    if sys.version_info >= (3, 10, 1):
        return asyncio.run(coro)

    assert dut is not None, "Your current version of python is less than 3.10.1, need to provide the dut parameter"

    loop = asyncio.get_event_loop()
    set_clock_event(dut, loop)
    result = loop.run_until_complete(coro)
    return result


async def gather(*tasks):
    all_tasks = []
    for task in tasks:
        all_tasks.append(create_task(task))

    results = []
    for task in all_tasks:
        results.append(await task)

    return results


from .base import MObject

class Component(MObject):

    def __init__(self):
        create_task(self.main())


    async def main(self):
        raise NotImplementedError("main function not implemented")

