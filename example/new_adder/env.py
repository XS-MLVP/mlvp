from mlvp import *
from mlvp.triggers import *
from mlvp.agent import *
from mlvp.model import *

class AdderBundle(Bundle):
	a, b, sum = Signals(3)

class AdderAgent(Agent):
    def __init__(self, bundle):
        super().__init__(bundle.step)

        self.bundle = bundle

    @driver_method()
    async def exec_add(self, a, b):
        self.bundle.a.value = a
        self.bundle.b.value = b
        await self.bundle.step()
        return self.bundle.sum.value

class AdderModel(Model):
    @driver_hook(agent_name="add_agent")
    def exec_add(self, a, b):
        return a + b

class AdderEnv(Env):
    def __init__(self, adder_bundle):
        super().__init__()
        self.add_agent = AdderAgent(adder_bundle)

        self.attach(AdderModel())
