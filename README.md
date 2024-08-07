# 简介

**MLVP**(**M**ulti-**L**anguage **V**erification **P**latform)是为多语言硬件验证提供的一套基础验证框架，目前支持 python 语言。其在多语言验证工具 [picker](https://github.com/XS-MLVP/picker) 所生成的 Python DUT 上提供了更为高级的验证特性，例如协程支持、覆盖率收集与报告生成等功能。

# 目录

- [简介](#简介)
- [目录](#目录)
- [安装](#安装)
- [使用说明](#使用说明)
  - [协程支持](#协程支持)
    - [运行协程测试](#运行协程测试)
    - [创建协程任务](#创建协程任务)
    - [创建并使用时钟](#创建并使用时钟)
  - [覆盖率统计与测试报告生成](#覆盖率统计与测试报告生成)
    - [软件依赖](#软件依赖)
    - [功能覆盖率统计](#功能覆盖率统计)
    - [生成测试报告](#生成测试报告)
    - [多进程支持](#多进程支持)
    - [测试执行](#测试执行)
  - [日志输出 (logger)](#日志输出-logger)
  - [接口 (Bundle)](#接口-bundle)
    - [定义接口](#定义接口)
    - [接口实例化 \& 连接](#接口实例化--连接)
    - [子接口使用](#子接口使用)
    - [参数](#参数)
    - [实用函数](#实用函数)
    - [利用Bundle中的process\_requests函数驱动dut](#利用bundle中的process_requests函数驱动dut)
  - [验证实用模块](#验证实用模块)
    - [两比特饱和计数器 （TwoBitsCounter）](#两比特饱和计数器-twobitscounter)
    - [伪 LRU 算法 （PLRU）](#伪-lru-算法-plru)
    - [64位 随机数生成器 （LFSR\_64）](#64位-随机数生成器-lfsr_64)



# 安装

使用以下命令安装 mlvp

```bash
git clone https://github.com/XS-MLVP/mlvp.git
cd mlvp
sudo python3 setup.py install
```

# 使用说明

## 协程支持

mlvp 中提供了若干使用的协程方法，以支持在 python 中更方便地使用协程进行硬件验证。

### 运行协程测试

在协程的编程模式中，需要使用 `async` 标记一个函数为协程函数，使用 `run` 进入事件循环。例如，在 mlvp 中总是会使用如下的方式来运行一项测试：

```python
import mlvp

async def my_test():
    # do something
    pass

mlvp.run(my_test())
```

### 创建协程任务

我们使用两种方式来处理程序中的协程任务：

- `await` 用于等待一个协程运行完成，并获取其返回值
- `mlvp.create_task` 用于创建一个协程任务并加入循环，但不会等待其运行完成

```python
import mlvp

async def my_test():
    # do something
    pass

async def main():
    # 等待 my_test 运行完成
    await my_test()

    # 创建新的协程任务，但不等待其运行完成
    mlvp.create_task(my_test())

    # do something

mlvp.run(main())
```

### 创建并使用时钟

在 MLVP 中我们提供了创建时钟的方法，以便在验证中使用时钟信号，可以通过如下方式进行创建：

```python
mlvp.create_task(mlvp.start_clock(picker_dut))
```

这会在后台创建一个不断运行的时钟，并自动关联到 dut 当中，我们可以通过这些方法在协程函数中使用时钟：

- `ClockCycles(item, ncycles)` 等待时钟信号运行 ncycles 个周期。item 可以是 dut，也可以是 dut 的某个信号
- `RisingEdge(pin)` 等待 pin 信号上升沿
- `FallingEdge(pin)` 等待 pin 信号下降沿
- `Change(pin)` 等待 pin 信号的值发生变化
- `Value(pin, value)` 等待 pin 信号的值变为 value
- `Condition(dut, func)` 等待 func() 返回 True

例如，这是一个等待时钟运行 10 个周期的例子：

```python
async def my_test(dut):
    mlvp.create_task(mlvp.start_clock(picker_dut))
    await mlvp.ClockCycles(dut, 10)

mlvp.run(my_test)
```


## 覆盖率统计与测试报告生成

### 软件依赖

mlvp 依赖以下软件包和工具

报告依赖包： pytest, pytest-reporter-html1. 如果需要支持多进程，要安装 pytest-xdist

覆盖率工具： verilator_coverage, genhtml (from lcov)

```bash
pip install pytest pytest-reporter-html1 pytest-xdist
```

### 功能覆盖率统计

功能覆盖率统计，即用户可以定义一些列“条件”，然后统计这些条件是否被触发，触发多少次等。mlvp 提供的功能覆盖率可以对具有 value 的对象（不能是int、str 等非object类型），按照条件进行统计。例如统计 x.value 是否在 [1,2,3]中出现过：

```python
from mlvp.funcov import *

...

x.value = 0

 当所有观测点都被观察到时，不再进行统计
g = CovGroup("coverage_group_0",
             disable_sample_when_hinted=False)
...

 添加观察点
g.add_watch_point(x, {"bin_name_range3-5": In([1,2,3])},
                     name="watch_point_1")

....
 进行观察
g.sample()

```

默认支持的条件判断有Eq，Gt，Lt，Ge，Le，Ne，In，NotIn，IsInRange。如果现有条件判断不满足需求，可以继承CovCondition进行自定义实现，也可以直接传入检测函数。例如被检测x中没有value，需要通过int(x)进行值转换：

```python
g.add_watch_point(x, {"bin_name_range3-5": lambda x: int(x) in [1,2,3]},
                     name="watch_point_1")
```

一个覆盖组（CovGroup）中可以有多个覆盖点（cover point），当所有覆盖点都hint时，该组标记为hint。一个覆盖点可以由多个 bin 组成，只有但其中所有bin对应的条件都满足时，该覆盖点才会被标记为hint。

```python

def test_funcov_error(request):
    ...
    g = CovGroup("coverage_group_2")
    g3 = CovGroup("coverage_group_3")
    ...
    # 添加多个group
    set_func_coverage(request, [g,g3])
    # or 添加一个group
    set_func_coverage(request, g,)
    # 一个 test_* 只能调用一次 set_func_coverage，多次调用结果会被覆盖
```

最后通过set_func_coverage接口收集Coverage Group，其group参数可以是CovGroup或者CovGroup的数组。


### 生成测试报告

mlvp库提供生成测试报告的功能，具体接口如下：

```python
import mlvp.reporter as rp

# 设置报告中的user和code信息
rp.set_user_info(name, code)

# 设置 metadata，当 is_del == True 时，删除 key 对应的数据
rp.set_meta_info(key, value, is_del=False)

# 设置当line覆盖率大于等于90%时，为绿色，否则为红色
rp.set_line_good_rate(90)

# 运行测试，生成报告。report为生成文件的名字，args为传入pytest的参数, -s时显示tests中的输出
rp.generate_pytest_report(report, args=["-s"])
```

测试时，需要在[conftest.py](https://docs.pytest.org/en/7.1.x/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files)中添加如下hook代码进行配置:

```python
import pytest
from mlvp.reporter import process_context, process_func_coverage


@pytest.hookimpl(trylast=True, optionalhook=True)
def pytest_reporter_context(context, config):
    process_context(context, config)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    return process_func_coverage(item, call, report)
```

### 多进程支持

默认情况下pytest中的test是顺序执行的，为了提高测试效率，可安装插件pytest-xdist插件支持test多进程执行。安装完插件后，通过参数-n设置并发度：

```python
# 设置为自动配置，通常情况下有多少个cpu，自动开启
rp.generate_pytest_report(report, args=["-s", "-n=auto"])

# 设置4进程并发执行
rp.generate_pytest_report(report, args=["-s", "-n 4"])
```

### 测试执行

```bash
git clone mlvp-git-url
cd mlvp
PYTHONPATH=. python test/test_reporter.py
```

将会在test/report目录中生成测试报告


## 日志输出 (logger)

MLVP 库内置了一个 logger，并设置好了默认的输出格式，MLVP 中的输出信息都将会通过 logger 进行输出。其中 logger 中还添加了一个 Handler 以便统计各类型日志信息的数量，日志可以设置一个 id 以进行分类。

logger 默认设置了一个 handler 用于输出到控制台，用户可以通过如下函数对 logger 进行配置，该函数支持更改日志级别、日志格式、设置日志输出文件。

```python
def setup_logging(log_level =logging.INFO, format=default_format, console_display=True, log_file=None)
```

用户可以通过如下方式使用内置记录器输出日志信息：

```python
import mlvp
mlvp.debug("This is a debug message", extra={"log_id": "dut"})
mlvp.info("This is an info message")
mlvp.warning("This is a warning message", extra={"log_id": "bundle"})
mlvp.error("This is an error message")
mlvp.critical("This is a critical message")
```

## 接口 (Bundle)

MLVP 中提供了一个接口类，用于为软件模块的编写提供虚拟接口。用户可以在不获取到 DUT 的情况下，通过定义一个虚拟接口，编写软件模块进行驱动。获取 DUT 后，只需要将 DUT 与虚拟接口进行连接，软件模块即可直接驱动 DUT。这方便了我们定义一组用于完成某个特定功能的接口集合，同时也使得软件模块的编写与 DUT 的具体实现解耦。

### 定义接口

用户可以通过如下方式定义一个接口：

```python
class MyBundle(Bundle):
    signal_list = ["signal1", "signal2", "signal3"]
```
只需要继承 `Bundle` 类，并定义 `signal_list` 即可。

### 接口实例化 & 连接

接口实例化的过程即是连接的过程，Bundle 类提供了多种方式用于连接接口，方法如下:

1. 通过字典方式连接

    ```python
    bundle = MyBundle({
        signal1: dut.io_signal1,
        signal2: dut.io_signal2,
        signal3: dut.io_signal3,
    })
    ```

2. 通过前缀方式连接

    ```python
    bundle = MyBundle.from_prefix(dut, "io_")
    ```

3. 通过正则表达式连接

    ```python
    bundle = MyBundle.from_regex(dut, r"io_(signal\d)")
    ```

    此时，signal_list 中的信号会与正则表达式中的捕获组进行匹配，匹配成功的信号会被连接，如果有多个捕获组，会将它们捕获到的字符串连接在一起进行匹配。

如此一来，用户可以在自定义的软件模块中，通过如下的方式访问接口，而无需关心 DUT 的接口名称。

```python
def my_module(bundle):
    bundle.signal1.value = 1
    print(bundle.signal2.value)
```

### 子接口使用

Bundle 提供了子接口的功能，可以在将一个 Bundle 作为另一个 Bundle 的子接口，这样可以更方便地对接口进行管理。

添加子接口只需要在定义时将接口的创建方法放入 `sub_bundles` 中，并指定名称即可，例如：

```python
class MyBundle2:
    signal_list = ["signal4", "signal5"]
    sub_bundles = [
        ("signal_set1", lambda dut: MyBundle.from_prefix(dut, "")),
    ]
```

访问子接口时通过子接口名称进行访问，例如：

```python
def my_module(bundle):
    bundle.signal_set1.signal1.value = 1
    print(bundle.signal_set1.signal2.value)
```

### 参数

可在 Bundle 实例化时传入某些参数以开启某些特性：

- `without_check` 默认为 False，当为 True 时，不会对接口的信号进行检查
- `allow_unconnected` 默认为 True, 当为 False 时，不能存在未连接的信号
- `allow_unconnected_access` 默认为 True, 当为 False 时，无法访问未连接的信号

### 实用函数

Bundle 提供了一些实用函数，用于方便地对接口进行操作：

- `collect` 用于收集接口中的信号值，返回一个字典
- `assign` 用于将一个字典中的值赋给接口中的信号
- `Step` 可等待的时钟信号，用于等待若干个时钟周期

### 利用Bundle中的process_requests函数驱动dut

Boundle通过make_requset_response_for绑定dut后，可以通过process_requests函数对dut进行驱动，如下所示：

```python
# define vars
# ...
bundle_a.make_requset_response_for(dut_a)
ret = bundle_a.process_requests([d1, d2, d3, ....])
```

函数process_requests接受一个数组，按顺序在每一个cycle对dut进行赋值（第一个cycle赋值d1，第二个赋值d2, ...）。赋值数据为dict类型或者callable类型（如果为callable类型，其返回值需要为dict）。
如果需要得到赋值时刻dut的io值，可以提过 "\_\_return_bundles__"进行指定(1个或者多个bundle)。例如：

```python

ret = bundle_a.process_requests([{"reset":1},                                             # data1
                                 {"reset":0, "__return_bundles__": dut.bundle_ready},     # data2
                                 ])

print(ret) # [{"data": {"ready": 1}, "cycle":1}]                                          # return of data2
```

其他特定功能key有：

1. **\_\_funcs__**， 可以在data中指定函数（或者函数list），完成赋值后被调用，参数为（cycle， bundle）。
1. **\_\_condition_func__**，指定条件函数，当其返回为true时才开始赋值，否者在下一个cycle再继续检测，直到条件满足。参数为（cycle，bundle，custom_args=None）。
1. **\_\_condition_args__**，条件函数自定义参数，（可选）。

*注释：process_requests 适合简单的条件判断驱动，如果需要处理多个条件，建议使用异步模式。

## 验证实用模块

MLVP 提供了一些验证实用模块，用于方便用户编写验证代码，这些模块被放置在 `mlvp.modules` 中。

### 两比特饱和计数器 （TwoBitsCounter）

`TwoBitsCounter` 是一个两比特饱和计数器，用于分支预测器的验证。用户可以通过如下方式使用：

```python
from mlvp.modules import TwoBitsCounter

# 创建一个两比特饱和计数器
counter = TwoBitsCounter()

# 获取预测结果
result = counter.get_prediction()

# 更新计数器，参数为本次更新是否 Taken
counter.update(True)
```

### 伪 LRU 算法 （PLRU）

`PLRU` 是伪 LRU 算法的软件实现，常用于替换策略的验证。用户可以通过如下方式使用：

```python
from mlvp.modules import PLRU

# 创建一个伪 LRU 算法，参数为行数
plru = PLRU(32)

# 获取替换行
replace_line = plru.get()

# 更新，参数为更新时访问的行
plru.update(5)
```

### 64位 随机数生成器 （LFSR_64）

`LFSR_64` 是64位随机数生成器的软件实现，用于模拟硬件中随机数的生成。用户可以通过如下方式使用：

```python
from mlvp.modules import LFSR_64

# 创建一个64位随机数生成器，参数为随机数种子
lfsr = LFSR_64(1) # 随机数种子默认为1

# 获取随机数，如果不更新状态，返回的值不会发生变化
random = lfsr.rand

# 更新生成器的状态
lfsr.step()
```
