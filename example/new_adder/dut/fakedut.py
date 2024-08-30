import asyncio

class FakeXData:
    ...

class FakeXPin:
    def __init__(self, event):
        self.value = 0
        self.xdata = FakeXData()
        self.event = event

class FakeDUT:
    def __init__(self, waveform_filename=None, coverage_filename=None):
        self.event = asyncio.Event()

    def eval(self):
        raise NotImplementedError("eval() not implemented")

    def Step(self, cycles=1):
        for _ in range(cycles):
            self.eval()
