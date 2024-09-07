import mlvp
from mlvp.agent import *
from mlvp.model import *
from mlvp.env import *

"""
Case 1
"""

class MyAgent(Agent):
    def __init__(self):
        super().__init__(lambda: None)

    @driver_method()
    async def driver1():
        ...

    @driver_method()
    async def driver2():
        ...

    @driver_method()
    async def driver3():
        ...

    @driver_method()
    async def driver4():
        ...

    @driver_method()
    async def driver5():
        ...

    @driver_method()
    async def driver6():
        ...

    @driver_method()
    async def driver7():
        ...

    @driver_method()
    async def driver8():
        ...

class MyModel(Model):
    def __init__(self):
        super().__init__()

        self.driver6 = DriverPort(agent_name="my_agent")
        self.my_driver7 = DriverPort("my_agent.driver7")
        self.my_agent__driver8 = DriverPort()

    @driver_hook(agent_name="my_agent")
    def driver1():
        ...

    @driver_hook(agent_name="my_agent")
    def driver2():
        ...

    @driver_hook(agent_name="my_agent", driver_name="driver3")
    def my_driver3():
        ...

    @driver_hook("my_agent.driver4")
    def my_driver4():
        ...

    @driver_hook()
    def my_agent__driver5():
        ...

class MyEnv(Env):
    def __init__(self):
        super().__init__()
        self.my_agent = MyAgent()

def test_env1():
    async def my_test():
        env = MyEnv()
        env.attach(MyModel())

    mlvp.run(my_test())


"""
Case 2
"""

class MyAgent2(Agent):
    def __init__(self):
        super().__init__(lambda: None)

    @driver_method()
    async def driver1():
        ...

    @driver_method()
    async def driver2():
        ...


class MyModel2(Model):
    @agent_hook("my_agent")
    def my_agent_mark():
        ...

    @driver_hook(agent_name="my_agent")
    def driver1():
        ...

    @driver_hook(agent_name="my_agent")
    def driver2():
        ...

class MyEnv2(Env):
    def __init__(self):
        super().__init__()
        self.my_agent = MyAgent2()

def test_env2():
    async def my_test():
        env = MyEnv2()
        env.attach(MyModel2())

    mlvp.run(my_test())

"""
Case 3
"""

class MyModel3(Model):
    def __init__(self):
        super().__init__()

        self.my_agent = AgentPort()

def test_env3():
    async def my_test():
        env = MyEnv2()
        env.attach(MyModel3())

    mlvp.run(my_test())


"""
Case 4
"""

class MyModel4(Model):
    def __init__(self):
        super().__init__()

        self.my_agent__driver1 = DriverPort()
        self.my_agent__driver2 = DriverPort()

def test_env4():
    async def my_test():
        env = MyEnv2()
        env.attach(MyModel4())

    mlvp.run(my_test())

"""
Case 5
"""

class MyAgent5(Agent):
    def __init__(self):
        super().__init__(lambda: None)

    @driver_method()
    async def driver1():
        ...

    @monitor_method()
    async def monitor1():
        ...

    @monitor_method()
    async def monitor2():
        ...

    @monitor_method()
    async def monitor3():
        ...

    @monitor_method()
    async def monitor4():
        ...

class MyModel5(Model):
    def __init__(self):
        super().__init__()

        self.my_agent__monitor1 = MonitorPort()
        self.monitor2 = MonitorPort(agent_name="my_agent")
        self.monitor3_mark = MonitorPort("my_agent.monitor3")
        self.monitor4_mark = MonitorPort(agent_name="my_agent", monitor_name="monitor4")

    @agent_hook("my_agent")
    def my_agent_mark():
        ...

    @driver_hook(agent_name="my_agent")
    def driver1():
        ...


class MyEnv5(Env):
    def __init__(self):
        super().__init__()
        self.my_agent = MyAgent5()

def test_env5():
    async def my_test():
        env = MyEnv5()
        env.attach(MyModel5())

    mlvp.run(my_test())

"""
Case 6
"""

class MyAgent6(Agent):
    def __init__(self):
        super().__init__(lambda: None)

    @driver_method()
    async def driver1(self, a, b, c=5):
        ...

    @driver_method()
    async def driver2():
        ...

class MyModel6(Model):
    def __init__(self):
        super().__init__()

        self.my_agent = AgentPort()

    async def main(self):
        req = await self.my_agent()
        assert req == ("my_agent", {"a": 1, "b": 2, "c": 5})

class MyEnv6(Env):
    def __init__(self):
        super().__init__()
        self.my_agent = MyAgent6()

import asyncio
class DUT:
    def __init__(self):
        self.event = asyncio.Event()

    def Step(self, cycles):
        ...

def test_env6():
    async def my_test():
        dut = DUT()
        mlvp.start_clock(dut)

        env = MyEnv6()
        env.attach(MyModel6())

        await env.my_agent.driver1(1, b=2)

    mlvp.run(my_test())

"""
Case 7
"""

class MyModel7(Model):
    def __init__(self):
        super().__init__()

        self.my_agent__driver1 = DriverPort()
        self.my_agent__driver2 = DriverPort()

    async def main(self):
        req = await self.my_agent__driver1()

        assert req == {"a": 1, "b": 2, "c": 5}


def test_env7():
    async def my_test():
        dut = DUT()
        mlvp.start_clock(dut)

        env = MyEnv6()
        env.attach(MyModel7())

        await env.my_agent.driver1(1, b=2)

    mlvp.run(my_test())

"""
Case 8
"""

class MyModel8(Model):
    @agent_hook("my_agent")
    def my_agent_mark(self, name, args):
        assert name == "driver1"
        assert args == {"a": 1, "b": 2, "c": 5}

    @driver_hook(agent_name="my_agent")
    def driver1(self, a, b, c=3):
        assert a == 1
        assert b == 2
        assert c == 3


def test_env7():
    async def my_test():
        dut = DUT()
        mlvp.start_clock(dut)

        env = MyEnv6()
        env.attach(MyModel8())

        await env.my_agent.driver1(1, b=2)

    mlvp.run(my_test())