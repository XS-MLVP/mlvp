import pytest
import random
import mlvp
from mlvp import PreRequest
from UT_Adder import DUTAdder
from env import AdderEnv, AdderBundle

"""
Test cases
"""

@pytest.mark.mlvp_async
async def test_random(mlvp_request):
    env = mlvp_request()

    for _ in range(1000):
        a = random.randint(0, 2**64-1)
        b = random.randint(0, 2**64-1)
        cin = random.randint(0, 1)
        await env.add_agent.exec_add(a, b, cin)

@pytest.mark.mlvp_async
async def test_boundary(mlvp_request):
    env = mlvp_request()

    for cin in [0, 1]:
        for a in [0, 2**64-1]:
            for b in [0, 2**64-1]:
                await env.add_agent.exec_add(a, b, cin)

"""
Coverage definition
"""

import mlvp.funcov as fc
from mlvp.reporter import CovGroup

def adder_cover_point(adder):
    g = CovGroup("Adder addition function")

    g.add_watch_point(adder.io_cout, {"io_cout is 0": fc.Eq(0)}, name="Cout is 0")
    g.add_watch_point(adder.io_cout, {"io_cout is 1": fc.Eq(1)}, name="Cout is 1")
    g.add_watch_point(adder.io_cin, {"io_cin is 0": fc.Eq(0)}, name="Cin is 0")
    g.add_watch_point(adder.io_cin, {"io_cin is 1": fc.Eq(1)}, name="Cin is 1")
    g.add_watch_point(adder.io_a, {"a > 0": fc.Gt(0)}, name="signal a set")
    g.add_watch_point(adder.io_b, {"b > 0": fc.Gt(0)}, name="signal b set")
    g.add_watch_point(adder.io_sum, {"sum > 0": fc.Gt(0)}, name="signal sum set")

    return g

"""
Initialize before each test
"""

@pytest.fixture()
def mlvp_request(mlvp_pre_request: PreRequest):
    mlvp.setup_logging(mlvp.INFO)
    dut = mlvp_pre_request.create_dut(DUTAdder)
    mlvp_pre_request.add_cov_groups(adder_cover_point(dut))

    def start_code():
        mlvp.start_clock(dut)
        return AdderEnv(AdderBundle.from_prefix("io_").bind(dut))

    return start_code
