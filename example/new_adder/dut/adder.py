from .fakedut import *

class DUTAdder(FakeDUT):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.io_a = FakeXPin(self.event)
        self.io_b = FakeXPin(self.event)
        self.io_sum = FakeXPin(self.event)

    def eval(self):
        self.io_sum.value = self.io_a.value + self.io_b.value
