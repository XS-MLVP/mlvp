__all__ = [
    "ClockCycles",
    "Value",
    "AllValid",
    "Condition",
    "Change",
    "RisingEdge",
    "FallingEdge",
]

from .bundle import Bundle


async def ClockCycles(item, ncycles=1):
    """
    Wait for the specified number of clock cycles.

    Args:
        item: The item to be waited for. It can be a dut, a bundle, or an xpin.
        ncycles: The number of clock cycles to be waited for.
    """

    # item is xpin
    if hasattr(item, "event"):
        for _ in range(ncycles):
            await item.event.wait()

    # item is Bundle
    elif isinstance(item, Bundle):
        await item.step(ncycles)

    # item is dut
    else:
        for _ in range(ncycles):
            await item.wait()


async def Value(pin, value: int, delay=1):
    """
    Wait for the pin to have the specified value.

    Args:
        pin: The pin to be checked.
        value: The value to be checked.
        delay: The minimum number of clock cycles to pass before checking.
    """

    for _ in range(delay):
        await pin.event.wait()
    while pin.value != value:
        await pin.event.wait()


async def AllValid(*pins, delay=1):
    """
    Wait for all the pins to be valid.

    Args:
        pins: The pins to be checked.
        delay: The minimum number of clock cycles to pass before checking.
    """

    for _ in range(delay):
        await pins[0].event.wait()

    while not all(pin.value for pin in pins):
        await pins[0].event.wait()


async def Condition(item, func, delay=1):
    """
    Wait for the specified condition to be true.

    Args:
        item: The item to be waited for. It can be a dut, a bundle, or an xpin.
        func: The condition function to be checked, it should accept a single argument 'item' and return a boolean.
        delay: The minimum number of clock cycles to pass before checking.
    """

    await ClockCycles(item, delay)
    while not func(item):
        await ClockCycles(item)


async def Change(pin):
    """
    Wait for the pin value to change.

    Args:
        pin: The pin to be checked.
    """

    old_value = pin.value
    while pin.value == old_value:
        await pin.event.wait()


async def RisingEdge(pin):
    """
    Wait for the pin to have a rising edge. Specifically, the function returns when the pin has a value of 0 in the
    previous cycle and a value of non-0 in the current cycle.

    Args:
        pin: The pin to be checked.
    """

    old_value = pin.value
    while old_value != 0 or pin.value == old_value:
        old_value = pin.value
        await pin.event.wait()


async def FallingEdge(pin):
    """
    Wait for the pin to have a falling edge. Specifically, the function returns when the pin has a value of non-0 in the
    previous cycle and a value of 0 in the current cycle.

    Args:
        pin: The pin to be checked.
    """

    old_value = pin.value
    while pin.value != 0 or pin.value == old_value:
        old_value = pin.value
        await pin.event.wait()
