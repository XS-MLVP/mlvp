# MLVP

#### functional coverage （功能覆盖率统计）


对具有 value 的对象（不能是int、str 等非object类型），按照条件进行统计。例如统计 x.value 是否在 [1,2,3]中出现过：

```python
from funcov import *

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

#### 功能测试测试

测试代码参考 tests/test_funcov.py

```
bash run.sh
```
