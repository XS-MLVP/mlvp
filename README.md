# toffee

> mlvp 已更名为 toffee

**toffee** 是一款基于 Python 的硬件验证框架，旨在帮助用户更加便捷、规范地使用 Python 构建硬件验证环境。

**toffee** 是一个使用 Python 语言编写的硬件验证框架，依托多语言转换工具 [picker](https://github.com/XS-MLVP/picker)，该工具能够将硬件设计的 Verilog 代码转换为 Python Package，使得用户可以使用 Python 来驱动并验证硬件设计。

**toffee** 吸收了部分 UVM 验证方法学，确保验证环境的规范性与可复用性。此外，toffee 对验证环境的构建方式进行了重新设计，使其更符合软件开发者的使用习惯，从而让软件开发者能够轻松上手硬件验证工作。

更多关于 toffee 的介绍，请参阅 [toffee 文档](https://open-verify.cc/mlvp/docs/mlvp)。

## 安装

toffee 需要的依赖有：

- Python 3.6.8+
- Picker 0.9.0+

当安装好上述依赖后，可通过 pip 安装 toffee：

```bash
pip3 install pytoffee
```

或通过以下命令安装最新版本的 toffee：

```bash
pip3 install pytoffee@git+https://github.com/XS-MLVP/toffee@master
```

通过以下方式可进行本地安装：

```bash
git clone https://github.com/XS-MLVP/toffee.git
cd toffee
pip3 install .
```

## 使用

我们使用一个简单的加法器示例来演示 toffee 的使用方法，该示例位于 `example/adder` 目录下。

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

使用 toffee 搭建验证环境之前，需要使用 picker 将设计转换为 Python Package。安装好依赖后，可以直接在 `example/adder` 目录下运行以下命令来完成转换：

```bash
make dut
```

为了验证加法器的功能，需要使用 toffee 提供的方法来建立验证环境。

首先需要为其创建加法器接口的驱动方法，这里用到了 `Bundle` 来描述需要驱动的某类接口，`Agent` 用于编写对该接口的驱动方法。如下所示：

```python
class AdderBundle(Bundle):
    a, b, cin, sum, cout = Signals(5)


class AdderAgent(Agent):
    @driver_method()
    async def exec_add(self, a, b, cin):
        self.bundle.a.value = a
        self.bundle.b.value = b
        self.bundle.cin.value = cin
        await self.bundle.step()
        return self.bundle.sum.value, self.bundle.cout.value
```

为了验证加法器的功能，还需要为其创建一个参考模型，用于验证加法器的输出是否正确。在 toffee 中，我们使用 `Model` 来定义参考模型。如下所示：

```python
class AdderModel(Model):
    @driver_hook(agent_name="add_agent")
    def exec_add(self, a, b, cin):
        result = a + b + cin
        sum = result & ((1 << 64) - 1)
        cout = result >> 64
        return sum, cout
```

接下来，需要创建一个顶层的测试环境，将上述的驱动方法与参考模型相关联，如下所示：

```python
class AdderEnv(Env):
    def __init__(self, adder_bundle):
        super().__init__()
        self.add_agent = AdderAgent(adder_bundle)

        self.attach(AdderModel())
```

此时，验证环境已经搭建完成，toffee 会自动驱动参考模型并收集结果，并将结果与加法器的输出进行比对。

之后，需要编写多个测试用例来验证加法器的功能，如下所示：

```python
@toffee_test.case
async def test_random(adder_env):
    for _ in range(1000):
        a = random.randint(0, 2**64 - 1)
        b = random.randint(0, 2**64 - 1)
        cin = random.randint(0, 1)
        await adder_env.add_agent.exec_add(a, b, cin)

@toffee_test.case
async def test_boundary(adder_env):
    for cin in [0, 1]:
        for a in [0, 2**64 - 1]:
            for b in [0, 2**64 - 1]:
                await adder_env.add_agent.exec_add(a, b, cin)
```

toffee 集成了 pytest 框架，用户可直接使用 pytest 的功能来对测试用例进行管理。toffee 会自动完成 dut 的驱动与参考模型的比对工作，并生成验证报告。

可以直接在 `example/adder` 目录下运行以下命令来运行该示例：

```bash
make run
```

运行结束后报告将自动在`reports`目录下生成。

更加详细的使用方法，请参考 [toffee 文档](https://open-verify.cc/mlvp/docs/mlvp)。

## 其他信息

本项目隶属 **万众一芯(UnityChip)** 开放验证，更多信息请访问 [open-verify.cc](https://open-verify.cc)
