# MLVP

#### functional coverage （功能覆盖率统计）

功能覆盖率统计，即用户可以定义一些列“条件”，然后统计这些条件是否被触发，触发多少次等。mlvp 提供的功能覆盖率可以对具有 value 的对象（不能是int、str 等非object类型），按照条件进行统计。例如统计 x.value 是否在 [1,2,3]中出现过：

```python
from mlvp.funcov import *

...

x.value = 0

# 当所有观测点都被观察到时，不再进行统计
g = CovGroup("coverage_group_0", 
             disable_sample_when_hinted=False)
...

# 添加观察点
g.add_watch_point(x, {"bin_name_range3-5": In([1,2,3])},
                     name="watch_point_1")

....
# 进行观察
g.sample()

```

默认支持的条件判断有Eq，Gt，Lt，Ge，Le，Ne，In，NotIn，IsInRange。如果现有条件判断不满足需求，可以继承CovCondition进行自定义实现，也可以直接传入检测函数。例如被检测x中没有value，需要通过int(x)进行值转换：

```python
g.add_watch_point(x, {"bin_name_range3-5": lambda x: int(x) in [1,2,3]},
                     name="watch_point_1")
```

一个覆盖组（CovGroup）中可以有多个覆盖点（cover point），当所有覆盖点都hint时，该组标记为hint。一个覆盖点可以由多个 bin 组成，只有但其中所有bin对应的条件都满足时，该覆盖点才会被标记为hint。


#### 生成测试报告

mlvp库提供生成测试报告的功能，具体接口如下：

```python
import mlvp.reporter as rp

# 需要在 master 节点执行

rp.set_user_info(name, code)                    # 设置报告中的user和code信息
rp.set_meta_info(key, value, is_del=False)      # 设置 metadata，当 is_del == True 时，删除 key 对应的数据
rp.generate_pytest_report(report, args=["-s"])  # 运行测试，生成报告。report为生成文件的名字，args为传入pytest的参数

```

测试时，需要在conftest.py中添加如下hook代码进行配置:

```python
import pytest
from mlvp.reporter import process_context, process_func_coverage


@pytest.hookimpl(optionalhook=True)
def pytest_reporter_context(context, config):
    process_context(context, config)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    return process_func_coverage(item, call, report)
```
