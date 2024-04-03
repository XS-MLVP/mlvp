import asyncio

timestamp = 0
def tick_timestamp():
    global timestamp
    timestamp = (timestamp + 1) % 2**32

def has_unwait_task():
    for task in asyncio.all_tasks():
        if "start_clock" not in task.__repr__() and "wait_for" not in task.__repr__():
            return True
    return False

async def tick_clock_ready():
    global timestamp
    timestamp_old = timestamp
    await asyncio.sleep(0)
    while has_unwait_task() or timestamp_old != timestamp:
        await asyncio.sleep(0)
        timestamp_old = timestamp

async def start_clock(dut):
    while True:
        await tick_clock_ready()
        dut.Step(1)
        dut.event.set()
        dut.event.clear()
        await asyncio.sleep(0)

def create_task(func):
    return asyncio.create_task(func)

def run(func):
    asyncio.run(func)


class Event:
    def __init__(self):
        self.event = asyncio.Event()

    async def wait(self):
        await self.event.wait()
        tick_timestamp()

    def set(self):
        self.event.set()

    def clear(self):
        self.event.clear()


class Queue:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def put(self, value):
        await self.queue.put(value)
        tick_timestamp()

    async def get(self):
        ret = await self.queue.get()
        tick_timestamp()
        return ret

    def put_nowait(self, value):
        self.queue.put_nowait(value)

    def get_nowait(self):
        return self.queue.get_nowait()

async def sleep(delay: float):
    await asyncio.sleep(delay)
    tick_timestamp()
