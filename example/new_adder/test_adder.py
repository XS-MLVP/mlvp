import mlvp
import pytest
from mlvp import PreRequest
from dut import DUTAdder
from env import AdderEnv, AdderBundle

async def async_test_add(adder):
    adder_bundle = AdderBundle.from_prefix("io_").bind(adder)
    env = AdderEnv(adder_bundle)
    mlvp.start_clock(adder)
    for i in range(10):
        await env.add_agent.exec_add(i, i+1)

async def async_test_sub(adder):
    adder_bundle = AdderBundle.from_prefix("io_").bind(adder)
    env = AdderEnv(adder_bundle)
    mlvp.start_clock(adder)
    for i in range(10):
        await env.add_agent.exec_add(i, 1-i)

def test_add(mlvp_request):
    mlvp.run(async_test_add(mlvp_request))

def test_sub(mlvp_request):
    mlvp.run(async_test_sub(mlvp_request))

@pytest.fixture()
def mlvp_request(mlvp_pre_request: PreRequest):
    mlvp.setup_logging(mlvp.INFO)
    return mlvp_pre_request.create_dut(DUTAdder)
