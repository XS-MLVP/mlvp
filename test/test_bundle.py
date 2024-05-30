import sys
sys.path.append("../")

import mlvp
from mlvp import Bundle


class FakePin:
    def __init__(self):
        self.xdata, self.event = None, None



class FakeDUT:
    def __init__(self):
        self.io_a = FakePin()
        self.io_b = FakePin()
        self.io_c_1 = FakePin()
        self.io_c_2 = FakePin()

def test_bundle():
    mlvp.setup_logging(log_level=mlvp.logger.INFO)
    dut = FakeDUT()

    class BundleB(Bundle):
        signals = ["1", "2", "3"]

    class BundleA(Bundle):
        signals = ["a", "b", "d"]

        def __init__(self):
            super().__init__()
            self.c = BundleB.from_prefix(prefix="c_")



    bundle_1 = BundleA.from_prefix(prefix="io_").set_name("bundle_1").bind(dut)
    bundle_2 = BundleA.from_regex(regex="io_(.*)").set_name("bundle_2").bind(dut)

    bundle_3 = BundleA.from_dict({
        "a": "io_a",
        "b": "io_b",
        "c_1": "io_c_1",
        "c_2": "io_c_2"
    }).set_name("bundle_3").bind(dut)


    class BundleC(Bundle):
        signals = ["a", "b"]

        def __init__(self):
            super().__init__()
            self.c = Bundle.new_list(["1", "2", "3"]).from_prefix("c_")

    bundle_4 = BundleC.from_prefix("io_").set_name("bundle_4").bind(dut)


if __name__ == "__main__":
    test_bundle()

