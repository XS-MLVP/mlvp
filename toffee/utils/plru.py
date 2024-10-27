import math


class PLRU:
    """Pseudo Least Recently Used replacement policy"""

    def __init__(self, ways_num):
        self.ways_num = ways_num
        self.bits_layer_num = math.ceil(math.log2(ways_num))
        self.bits = [
            [0 for _ in range(2**layer)] for layer in range(self.bits_layer_num)
        ]

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
