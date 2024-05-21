import mlvp
from mlvp import Bundle


class FakePin:
    def __init__(self):
        self.xdata, self.event = None, None

class FakeDUT:
    def __init__(self):
        self.a = FakePin()
        self.b = FakePin()
        self.c_1 = FakePin()
        self.c_2 = FakePin()

def test_bundle():
    mlvp.setup_logging(log_level=mlvp.logger.INFO)
    dut = FakeDUT()

    class BundleA(Bundle):
        signals_list = ["a", "b", "c_1", "c_2"]
    bundle_a = BundleA.from_prefix(dut)

    class BundleB(Bundle):
        signals_list = ["a", "b"]
    bundle_b = BundleB.from_prefix(dut)


    class BundleC(Bundle):
        signals_list = ["1", "2"]
    # dict
    bundle_c_2 = BundleC(dut_ports={"1": dut.c_1, "2": dut.c_2})
    # prefix
    bundle_c_1 = BundleC.from_prefix(dut, prefix="c_")
    # regex
    bundle_c_3 = BundleC.from_regex(dut, regex=r"c_(\d)")

    class BundleD(Bundle):
        sub_bundles = [
            ("c", lambda dut: BundleC.from_prefix(dut, prefix="c_"))
        ]
        signals_list = ["a", "b"]
    bundle_d = BundleD.from_prefix(dut)

    class BundleE(Bundle):
        sub_bundles = [
            ("c", lambda dut: BundleC.from_prefix(dut, prefix="c_"))
        ]
    bundle_e = BundleE.from_prefix(dut)

    try:
        class BundleF(Bundle):
            pass
        bundle_f = BundleF.from_prefix(dut)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    test_bundle()

