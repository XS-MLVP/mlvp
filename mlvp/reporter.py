#coding=utf8

import pytest
import os
from .funcov import CovGroup


def get_template_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def generate_pytest_report(report):
    result = pytest.main(
        [
            "--template=html/mlvp.html",
            "--template-dir=" + get_template_dir(),
            "--report=" + report,
            "-s"
        ]
    )
    return result

__user_info__ = None
__line_coverage__ = None
__func_coverage__ = None


def __update_line_coverage__():
    return {
        "hints": 100,
        "total": 1000,
        "grate": 90,
    }


def __update_func_coverage__():
    global __func_coverage__
    if __func_coverage__ is None:
        return None
    coverage = {}
    group_num_hints = 0
    group_num_total = 0
    point_num_hints = 0
    point_num_total = 0
    bin_num_hints = 0
    bin_num_total = 0
    has_once = False
    def parse_group(g):
        nonlocal group_num_hints, group_num_total, point_num_hints, point_num_total, bin_num_hints, bin_num_total, has_once
        data = g.as_dict()
        group_num_total += 1
        if data["hinted"]:
            group_num_hints += 1
        if data["has_once"]:
            has_once = True
        point_num_hints += data["point_num_hints"]
        point_num_total += data["point_num_total"]
        bin_num_hints += data["bin_num_hints"]
        bin_num_total += data["bin_num_total"]
        return data
    coverage["groups"] = [parse_group(g) for g in __func_coverage__]
    coverage["group_num_total"] = group_num_total
    coverage["group_num_hints"] = group_num_hints
    coverage["point_num_total"] = point_num_total
    coverage["point_num_hints"] = point_num_hints
    coverage["bin_num_total"] = bin_num_total
    coverage["bin_num_hints"] = bin_num_hints
    coverage["grate"] = 100
    coverage["has_once"] = has_once
    return coverage


def process_context(context, config):
    global __user_info__
    if __user_info__ is not None:
        context["user"] = __user_info__
    for k in ["Plugins", "Packages"]:
        context["metadata"].pop(k, None)
    context["title"] = "XiangShan-BPU UT-Test Report"
    context["coverages"] = {
        "line": __update_line_coverage__(),
        "functional": __update_func_coverage__()
    }
    print(context["coverages"])


def set_func_coverage(request, g):
    assert isinstance(g, CovGroup), "g should be an instance of CovGroup"
    request.node.__coverage_group__ = g


def process_func_coverage(item, call):

    if call.when != 'teardown':
        return
    
    func_coverage_group = getattr(item, '__coverage_group__', None)
    if func_coverage_group is None:
        return None

    assert isinstance(func_coverage_group, CovGroup), "func_coverage_group should be an instance of CovGroup"
    global __func_coverage__
    if __func_coverage__ is None:
        __func_coverage__ = []

    if func_coverage_group in __func_coverage__:
        return
    __func_coverage__.append(func_coverage_group)


def set_user_info(name, code):
    global __user_info__
    __user_info__ = {"name": name, "code": code}
