
import os
import sys
from mlvp.reporter import generate_pytest_report, set_line_good_rate, set_meta_info, set_user_info

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
    g3 = fc.CovGroup("coverage_group_3")

    # 0.use default check functions
    g.add_watch_point(v, {"bin_name_is1":      fc.Eq(1),
                          "bin_name_range3-5": fc.In([3,4,5])
                          }, name="watch_point_1")
    set_func_coverage(request, [g,g3])
    print("test_funcov_error pid: ", os.getpid(), file=sys.stderr)


def test_must_fail():
    assert False


def sample_report():
    set_line_good_rate(10)
    set_meta_info("test_key", "test_value")
    set_user_info("test_user", "USER001122334")
    report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report/report.html")
    result = generate_pytest_report(report, ["-s", "test"])
    print("sample_report pid: ", os.getpid())


if __name__ == "__main__":
    sample_report()
