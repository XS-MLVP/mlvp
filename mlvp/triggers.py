async def Value(pin, value):
    while (pin.value != value):
        await pin.event.wait()

async def ClockCycles(item, ncycles = 1):
    if hasattr(item, "event"):
        for _ in range(ncycles):
            await item.event.wait()
    else:
        for _ in range(ncycles):
            await item.wait()

async def Condition(dut, func):
    while (not func()):
        await dut.event.wait()

async def RisingEdge(pin):
    value = pin.value
    while (value != 0 or pin.value == value):
        value = pin.value
        await pin.event.wait()

async def FallingEdge(pin):
    value = pin.value
    while (pin.value != 0 or pin.value == value):
        value = pin.value
        await pin.event.wait()

async def Change(pin):
    value = pin.value
    while (pin.value == value):
        await pin.event.wait()
