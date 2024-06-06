import sys
sys.path.append("../")

import mlvp
from mlvp import Bundle


class FakePin:
    def __init__(self):
        self.xdata, self.event, self.value, self.mIOType = None, None, None, 0

class FakeDUT:
    def __init__(self):
        self.io_a = FakePin()
        self.io_b = FakePin()
        self.io_c_1 = FakePin()
        self.io_c_2 = FakePin()
        self.io_d_1 = FakePin()
        self.io_d_2 = FakePin()

def test_bundle():
    mlvp.setup_logging(log_level=mlvp.logger.INFO)
    dut = FakeDUT()

    class BundleB(Bundle):
        signals = ["1", "2", "3"]

    class BundleA(Bundle):
        signals = ["a", "b", "e"]

        def __init__(self):
            super().__init__()
            self.c = BundleB.from_prefix(prefix="c_")
            self.d = BundleB.from_prefix(prefix="d_")



    bundle_1 = BundleA().set_name("bundle_1").bind(dut)
    bundle_1.set_prefix("io_")
    bundle_1.bind(dut)

    bundle_2 = BundleA.from_regex(regex="io_(.*)").bind(dut)

    print(bundle_2)

    bundle_3 = BundleA.from_dict({
        "a": "io_a",
        "b": "io_b",
        "c_1": "io_c_1",
        "c_2": "io_c_2",
        "d_1": "io_d_1",
        "abcdefg": "io_abcdefg"
    }).set_name("bundle_3").bind(dut)

    bundle_1.assign({
        "a": 1,
        "b": 2,
        "c.1": 3,
        "c.2": 4
    }, multilevel=False)
    print(bundle_1.as_dict(multilevel=False))

    bundle_1.assign({
        "a": 5,
        "b": 6,
        "c": {
            "1": 7,
            "2": 8
        }
    }, multilevel=True)
    print(bundle_1.as_dict(multilevel=True))


    class BundleC(Bundle):
        signals = ["a", "b"]

        def __init__(self):
            super().__init__()
            self.c = Bundle.new_class_from_list(["1", "2", "3"]).from_prefix("c_")
            self.d = Bundle.new_class_from_list(["1", "2", "3"]).from_prefix("d_")

    bundle_4 = BundleC.from_prefix("io_").set_name("bundle_4").bind(dut)

    for signal in bundle_4.all_signals():
        print(signal)

    bundle_4.set_all(666)
    print(bundle_4.as_dict())

    bundle_4.assign({
        "*": 777,
        "a": 1,
        "c": {
            "1": 3,
            "*": 888,
        },
    }, multilevel=True)
    print(bundle_4.as_dict())

    class BundleD(Bundle):
        signals = ["a", "b"]

        def __init__(self):
            super().__init__()
            self.c = Bundle.new_class_from_list(["1", "2", "3", "4"]).from_dict({
                "1" : "c_1",
                "2" : "c_2",
                "4" : "c_4"
            })
    bundle_5 = BundleD.from_prefix("io_").set_name("bundle_5").bind(dut)




if __name__ == "__main__":
    test_bundle()

