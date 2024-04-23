import math

class PLRU:
    """Pseudo Least Recently Used replacement policy"""

    def __init__(self, ways_num):
        self.ways_num = ways_num
        self.bits_layer_num = math.ceil(math.log2(ways_num))
        self.bits = [[0 for _ in range(2 ** layer)] for layer in range(self.bits_layer_num)]

    def update(self, way):
        pos = 0
        for i in range(self.bits_layer_num):
            self.bits[i][pos] = 0 if way & (1 << (self.bits_layer_num - i - 1)) else 1
            pos = pos * 2 + (0 if self.bits[i][pos] else 1)

    def get(self):
        pos = 0
        for i in range(self.bits_layer_num):
            pos = pos * 2 + self.bits[i][pos]
        return pos

class TwoBitsCounter:
    """Two bit saturation counter
    00 <-> 01 <-> 10 <-> 11

    00: Strongly not taken
    01: Weakly not taken
    10: Weakly taken
    11: Strongly taken
    """

    def __init__(self, init_value=2):
        self.counter = init_value

    def update(self, taken):
        if taken:
            self.counter = min(self.counter + 1, 3)
        else:
            self.counter = max(self.counter - 1, 0)

    def get_prediction(self):
        return 1 if self.counter > 1 else 0
