import sys
sys.path.append("../")

import mlvp
from mlvp import Port


def test_async():
    a = Port()
    b = Port(end_port=False)
    c = Port()
    d = Port()

    a.connect(b)
    b.connect(c)
    b.connect(d)


    async def listener():
        print("c:", await c.get())
        print("d:", await d.get())


    async def test_port():
        mlvp.create_task(listener())
        await a.put("hahah")

    mlvp.run(test_port())


def test_sync():
    a = Port()
    b = Port(end_port=False)
    c = Port(end_port=False)
    d = Port()

    a.connect(b)
    b.connect(c)
    c.set_sync_get(lambda: 123456)
    c.set_sync_put(lambda x: print(f"C: Get {x}"))
    d.set_sync_put(lambda x: print(f"D: Get {x}"))
    d.set_sync_get(lambda: "D sync_get")
    d.set_sync_peek(lambda: "D sync_peek")
    d.set_try_get(lambda: "D try_get")
    d.set_try_put(lambda x: print(f"D: Try put {x}"))
    d.set_try_peek(lambda: "D try_peek")
    d.set_can_get(lambda: "D can_get")
    d.set_can_put(lambda: "D can_put")
    d.set_can_peek(lambda: "D can_peek")

    print(a.sync_get())
    b.connect(d)
    print(a.sync_put(123))
    b.disconnect(c)
    print(a.sync_get())
    print(a.sync_peek())
    print(a.try_get())
    print(a.try_put(123))
    print(a.try_peek())
    print(a.can_get())
    print(a.can_put())
    print(a.can_peek())



# test_async()
test_sync()
