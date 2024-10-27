class LFSR_64:
    def __init__(self, seed: int = 1):
        self._state = seed & ((1 << 64) - 1)

    def step(self):
        def get_bit(x):
            return (self._state >> x) & 1

        new_bit = get_bit(0) ^ get_bit(1) ^ get_bit(3) ^ get_bit(4)
        self._state = (self._state >> 1) | (new_bit << 63)

    @property
    def rand(self):
        return self._state
