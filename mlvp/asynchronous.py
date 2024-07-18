import asyncio
from . import reg


# Asynchronous event definition

timestamp = 0
def tick_timestamp():
    global timestamp
    timestamp = (timestamp + 1) % 2**32

def has_unwait_task():
    for task in asyncio.all_tasks():
        task_str = task.__str__()
        if ("start_clock" not in task_str and "wait_for" not in task_str) or ("finished" in task_str):
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

async def start_clock(dut):
    while True:
        await tick_clock_ready()
        dut.Step(1)
        dut.event.set()
        dut.event.clear()
        process_delay()
        reg.update_regs()
        await asyncio.sleep(0)


create_task = asyncio.create_task
run = asyncio.run
wait = asyncio.wait

create_task = asyncio.create_task

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

