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
