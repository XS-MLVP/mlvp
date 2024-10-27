import pytest

"""
Test cases
"""
import random
from env import AdderEnv, AdderBundle

@pytest.mark.toffee_async
async def test_random(start_entry):
    env = start_entry()

    for _ in range(1000):
        a = random.randint(0, 2**64-1)
        b = random.randint(0, 2**64-1)
        cin = random.randint(0, 1)
        await env.add_agent.exec_add(a, b, cin)

@pytest.mark.toffee_async
async def test_boundary(start_entry):
    env = start_entry()

    for cin in [0, 1]:
        for a in [0, 2**64-1]:
            for b in [0, 2**64-1]:
                await env.add_agent.exec_add(a, b, cin)

"""
Coverage definition
"""
import toffee.funcov as fc
from toffee.funcov import CovGroup

def adder_cover_point(adder):
    g = CovGroup("Adder addition function")

    g.add_cover_point(adder.io_cout, {"io_cout is 0": fc.Eq(0)}, name="Cout is 0")
    g.add_cover_point(adder.io_cout, {"io_cout is 1": fc.Eq(1)}, name="Cout is 1")
    g.add_cover_point(adder.io_cin, {"io_cin is 0": fc.Eq(0)}, name="Cin is 0")
    g.add_cover_point(adder.io_cin, {"io_cin is 1": fc.Eq(1)}, name="Cin is 1")
    g.add_cover_point(adder.io_a, {"a > 0": fc.Gt(0)}, name="signal a set")
    g.add_cover_point(adder.io_b, {"b > 0": fc.Gt(0)}, name="signal b set")
    g.add_cover_point(adder.io_sum, {"sum > 0": fc.Gt(0)}, name="signal sum set")

    return g

"""
Initialize before each test
"""
import toffee
from UT_Adder import DUTAdder
from toffee_test.plugin import ToffeeRequest

@pytest.fixture()
def start_entry(toffee_request: ToffeeRequest):
    toffee.setup_logging(toffee.INFO)
    dut = toffee_request.create_dut(DUTAdder)
    toffee_request.add_cov_groups(adder_cover_point(dut))

    def start_code():
        toffee.start_clock(dut)
        return AdderEnv(AdderBundle.from_prefix("io_").bind(dut))

    return start_code
