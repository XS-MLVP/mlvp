import mlvp
from mlvp import *
from mlvp.agent import *
from mlvp.model import *

import asyncio
class DUT:
    def __init__(self):
        self.event = asyncio.Event()

    def Step(self, cycles):
        ...

class MyAgent(Agent):
    def __init__(self, dut, infos):
        self.infos = infos
        self.dut = dut
        super().__init__(lambda: None)

    @driver_method()
    async def driver1(self):
        self.infos.append("driver1")
        await self.dut.event.wait()
        await self.dut.event.wait()

    @driver_method()
    async def driver2(self):
        self.infos.append("driver2")
        await self.dut.event.wait()
        await self.dut.event.wait()


class MyModel(Model):
    def __init__(self, infos):
        super().__init__()

        self.infos = infos

    @driver_hook(agent_name="my_agent")
    def driver1(self):
        self.infos.append("model1")

    @driver_hook(agent_name="my_agent")
    def driver2(self):
        self.infos.append("model2")

class MyEnv(Env):
    def __init__(self, dut, infos):
        super().__init__()
        self.my_agent = MyAgent(dut, infos)


def test_executor():
    async def my_test():
        dut = DUT()
        mlvp.start_clock(dut)

        infos = []

        env = MyEnv(dut, infos)
        env.attach(MyModel(infos))

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="model_first")
        assert infos == ["model1", "driver1"]
        infos.clear()

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="dut_first")
        assert infos == ["driver1", "model1"]
        infos.clear()

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="parallel")
        assert infos == ["driver1", "model1"]
        infos.clear()

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="dut_first")
            exec(env.my_agent.driver2(), sche_order="dut_first")
        assert infos == ["driver1", "driver2", "model1", "model2"]
        infos.clear()

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="dut_first")
            exec(env.my_agent.driver2(), sche_order="dut_first", priority=1)
        assert infos == ["driver1", "driver2", "model2", "model1"]
        infos.clear()

        async with Executor() as exec:
            exec(env.my_agent.driver1(), sche_order="model_first", priority=3)
            exec(env.my_agent.driver2(), sche_order="model_first", priority=2)
        assert infos == ["model2", "model1", "driver2", "driver1"]
        infos.clear()

    mlvp.run(my_test())
