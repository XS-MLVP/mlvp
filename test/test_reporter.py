
import os
from mlvp.reporter import generate_pytest_report

import mlvp.funcov as fc
from mlvp.reporter import set_func_coverage

class TextData(object):
    '''Simple class to test funcov with a text value'''
    def __init__(self, value) -> None:
        self.value = value
    def __str__(self):
        return self.value

def test_funcov_error(request): 
    v = TextData(1)
    g = fc.CovGroup("coverage_group_2")

    # 0.use default check functions
    g.add_watch_point(v, {"bin_name_is1":      fc.Eq(1),
                          "bin_name_range3-5": fc.In([3,4,5])
                          }, name="watch_point_1")
    set_func_coverage(request, g)


def sample_report():
    report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.html")
    result = generate_pytest_report(report)
    print(result)


if __name__ == "__main__":
    sample_report()
