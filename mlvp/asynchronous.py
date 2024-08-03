import sys
import asyncio
from .bundle import Bundle

"""Asynchronous event definition

This section implements specific asynchronous event requirements to meet the clock requirements in the circuit.
Specifically, we need to complete all executable tasks before the next clock event arrives.
"""

# Flags whether new tasks have been run in this round
new_task_run = False

def task_run():
    """
    Set the flag to indicate that a new task has been run.
    """

    global new_task_run
    new_task_run = True

def __has_unwait_task():
    """
    Detects whether a task exists, is not waiting, or is waiting for an event that has already been triggered.
    """

    for task in asyncio.all_tasks():

        if task.get_name() == "__clock_loop":
            continue

        if task._fut_waiter is None or task._fut_waiter._state == "FINISHED":
            return True

    return False

async def __run_once():
    """
    The event loop executes one round.
    """

    global new_task_run

    new_task_run = False
    await asyncio.sleep(0)

async def other_tasks_done():
    """
    Wait for all tasks to complete. This means that all tasks are waiting at this time, and there are no tasks that
    can be executed.
    """

    global new_task_run
    await __run_once()
    while __has_unwait_task() or new_task_run:
        await __run_once()
class Event(asyncio.Event):
    """
    Change the function in the Event to meet the asynchronous requirements.
    """

    def __init__(self):
        super().__init__()

    async def wait(self):
        await super().wait()
        task_run()
class Queue(asyncio.Queue):
    """
    Change the function in the Queue to meet the asynchronous requirements.
    """

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
    """
    Change the implementation of the sleep function to meet the asynchronous requirements.
    """

    await asyncio.sleep(delay)
    task_run()

"""Asynchronous primary interface

Using the asynchronous event logic defined above, the external asynchronous interface in mlvp library is implemented.
"""

create_task = asyncio.create_task

async def __clock_loop(dut):
    """
    The clock loop function, which is the main loop of the asynchronous event.
    """

    global new_task_run

    while True:
        await other_tasks_done()
        dut.Step(1)
        dut.event.set()
        dut.event.clear()

def start_clock(dut):
    """
    Start a clock loop on a DUT.
    """

    task = create_task(__clock_loop(dut))
    task.set_name("__clock_loop")

def set_clock_event(dut, loop):
    """
    Set the clock event for the DUT.

    In earlier versions of python, the original Event definition cannot be used in the new event loop.
    """

    new_event = asyncio.Event(loop=loop)
    dut.xclock._step_event = new_event
    dut.event = new_event

    for xpin_info in Bundle.dut_all_signals(dut):
        xpin = xpin_info["signal"]
        xpin.event = new_event
        print(xpin.event, new_event)

def run(coro, dut=None):
    """
    Start the asynchronous event loop and run the coroutine.

    Args:
        coro: The coroutine to be run.
        dut: The DUT object.

    Returns:
        The result of the coroutine.
    """

    if sys.version_info >= (3, 10, 1):
        return asyncio.run(coro)

    assert dut is not None, "Your current version of python is less than 3.10.1, need to provide the dut parameter"

    loop = asyncio.get_event_loop()
    set_clock_event(dut, loop)
    result = loop.run_until_complete(coro)
    return result

async def gather(*coros):
    """
    Gather multiple coroutines and run them at the same time.
    """

    all_tasks = []
    for coro in coros:
        all_tasks.append(create_task(coro))

    results = []
    for task in all_tasks:
        results.append(await task)

    return results

"""
Component definition
"""

from .base import MObject

class Component(MObject):
    """
    A Component is a component that has its own execution flow.
    """

    def __init__(self):
        create_task(self.main())

    async def main(self):
        raise NotImplementedError("main function not implemented")
