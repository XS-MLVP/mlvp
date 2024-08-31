import pytest
import mlvp
from mlvp import PreRequest
from dut import DUTAdder
from env import AdderEnv, AdderBundle

@pytest.mark.mlvp_async
async def test_add(mlvp_request):
    env = mlvp_request()

    for i in range(10):
        await env.add_agent.exec_add(i, i+1)

@pytest.mark.mlvp_async
async def test_sub(mlvp_request):
    env = mlvp_request()

    for i in range(10):
        await env.add_agent.exec_add(i, -i-i)

@pytest.fixture()
def mlvp_request(mlvp_pre_request: PreRequest):
    mlvp.setup_logging(mlvp.INFO)
    dut = mlvp_pre_request.create_dut(DUTAdder)

    def start_code():
        mlvp.start_clock(dut)
        return AdderEnv(AdderBundle.from_prefix("io_").bind(dut))

    return start_code

