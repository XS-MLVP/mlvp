import sys
sys.path.append("../")

import mlvp
from mlvp import Port


a = Port()
b = Port()
c = Port()

a.connect(b)
a.connect(c)


async def listener():
    print("b:", await b.get())
    print("c:", await c.get())


async def test_port():
    mlvp.create_task(listener())
    await a.put("hahah")


mlvp.run(test_port())
