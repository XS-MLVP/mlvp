import sys
import asyncio
from .bundle import Bundle

# Asynchronous event definition

timestamp = 0
def tick_timestamp():
    global timestamp
    timestamp = (timestamp + 1) % 2**32

def has_unwait_task():
    for task in asyncio.all_tasks():

        if task.get_name() == "__clock_loop":
            continue

        if task._fut_waiter is None or task._fut_waiter._state == "FINISHED":
            return True

    return False

async def tick_clock_ready():
    global timestamp
    timestamp_old = timestamp
    while has_unwait_task() or timestamp_old != timestamp:
        await asyncio.sleep(0)
        timestamp_old = timestamp

class Event(asyncio.Event):
    def __init__(self):
        super().__init__()

    async def wait(self):
        await super().wait()
        tick_timestamp()

class Queue(asyncio.Queue):
    def __init__(self):
        super().__init__()

    async def put(self, item):
        await super().put(item)
        tick_timestamp()

    async def get(self):
        ret = await super().get()
        tick_timestamp()
        return ret


async def sleep(delay: float):
    await asyncio.sleep(delay)
    tick_timestamp()


# Processing delay

delay_assign_list = []
delay_func_list = []
def process_delay():
    for item in delay_assign_list:
        if item[2] == 0:
            item[0].value = item[1]
            delay_assign_list.remove(item)
        else:
            item[2] -= 1

    for item in delay_func_list:
        if item[1] == 0:
            item[0]()
            delay_func_list.remove(item)
        else:
            item[1] -= 1


def delay_assign(pin, value, delay = 1):
    assert(delay >= 1)
    delay_assign_list.append([pin, value, delay])

def delay_func(func, delay = 1):
    assert(delay >= 1)
    delay_func_list.append([func, delay])

# Asynchronous core function

create_task = asyncio.create_task

async def __clock_loop(dut):
    while True:
        await tick_clock_ready()
        dut.Step(1)
        dut.event.set()
        dut.event.clear()
        process_delay()
        await asyncio.sleep(0)

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

