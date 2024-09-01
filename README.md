# mlvp: multi-language verification platform

**mlvp** 是一套基于 Python 的硬件验证框架，帮助用户更加方便、规范地使用 Python 建立起硬件验证环境。

## 介绍

**mlvp** 是使用 Python 语言编写的一套硬件验证框架，它依赖于多语言转换工具 [picker](https://github.com/XS-MLVP/picker)，该工具能够将硬件设计的 Verilog 代码转换为 Python Package，使得用户可以使用 Python 来驱动并验证硬件设计。

**mlvp** 吸收了部分 UVM 验证方法学，以保证验证环境的规范性和可复用性。并且，mlvp 重新设计了整套验证环境的搭建方式，使其更符合软件领域开发者的使用习惯，使得软件开发者可以轻易地上手硬件验证工作。

更多关于 mlvp 的介绍，请参考 [mlvp 文档](https://open-verify.cc/mlvp/docs/mlvp)


## 安装

mlvp 需要的依赖有：

- Python 3.6.8+
- Picker 0.9.0+

当安装好上述依赖后，可运行以下命令安装最新版本的 mlvp：

```bash
pip3 install mlvp@git+https://github.com/XS-MLVP/mlvp@master
```

或通过以下方式进行本地安装：

```bash
git clone https://github.com/XS-MLVP/mlvp.git
cd mlvp
pip3 install .
```

## 使用

我们使用一个简单的加法器示例来演示 mlvp 的使用方法，该示例位于 `example/adder` 目录下。

加法器的设计如下：

```verilog
module Adder #(
    parameter WIDTH = 64
) (
    input  [WIDTH-1:0] io_a,
    input  [WIDTH-1:0] io_b,
    input              io_cin,
    output [WIDTH-1:0] io_sum,
    output             io_cout
);

assign {io_cout, io_sum}  = io_a + io_b + io_cin;

endmodule
```

首先使用 picker 将其转换为 Python Package，再使用 mlvp 来为其建立验证环境。安装好依赖后，可以直接在 `example/adder` 目录下运行以下命令来完成转换：

```bash
make dut
```

为了验证加法器的功能，我们使用 mlvp 提供的方法来建立验证环境。

首先需要为其创建加法器接口的驱动方法，这里用到了 `Bundle` 来描述需要驱动的某类接口，`Agent` 用于编写对该接口的驱动方法。如下所示：

```python
class AdderBundle(Bundle):
	a, b, cin, sum, cout = Signals(5)

class AdderAgent(Agent):
    def __init__(self, bundle):
        super().__init__(bundle.step)
        self.bundle = bundle

    @driver_method()
    async def exec_add(self, a, b, cin):
        self.bundle.a.value = a
        self.bundle.b.value = b
        self.bundle.cin.value = cin
        await self.bundle.step()
        return self.bundle.sum.value, self.bundle.cout.value
```

为了验证加法器的功能，我们还需要为其创建一个参考模型，用于验证加法器的输出是否正确。在 mlvp 中，我们使用 `Model` 来定义参考模型。如下所示：

```python
class AdderModel(Model):
    @driver_hook(agent_name="add_agent")
    def exec_add(self, a, b, cin):
        result = a + b + cin
        sum = result & ((1 << 64) - 1)
        cout = result >> 64
        return sum, cout
```

接下来，我们需要创建一个顶层的测试环境，将上述的驱动方法与参考模型相关联，如下所示：

```python
class AdderEnv(Env):
    def __init__(self, adder_bundle):
        super().__init__()
        self.add_agent = AdderAgent(adder_bundle)

        self.attach(AdderModel())
```

此时，验证环境已经搭建完成，mlvp 会自动驱动参考模型并收集结果，并将结果与加法器的输出进行比对。

之后，我们可以编写多个测试用例来验证加法器的功能，如下所示：

```python
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
```

mlvp 集成了 pytest 框架，用户可直接使用 pytest 的功能来对测试用例进行管理。mlvp 会自动完成 dut 的驱动与参考模型的比对工作，并生成验证报告。

可以直接在 `example/adder` 目录下运行以下命令来运行该示例：

```bash
make run
```

运行结束后报告将自动在`reports`目录下生成。

更加详细的使用方法，请参考 [mlvp 文档](https://open-verify.cc/mlvp/docs/mlvp)。

## 其他信息

本项目隶属于 **万众一芯(UnityChip)** 开源验证项目，更多信息请访问 [open-verify.cc](https://open-verify.cc)
