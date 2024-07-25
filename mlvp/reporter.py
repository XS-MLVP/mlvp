#coding=utf8

import json
import pytest
import os
import sys
import uuid
from .funcov import CovGroup
from .base import convert_line_coverage


def get_template_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


__output_report_dir__ = None
def generate_pytest_report(report, args=["-s"]):
    report_dir = os.path.dirname(os.path.abspath(report))
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    global __output_report_dir__
    __output_report_dir__ = report_dir
    defualt_args = [
            "--template=html/mlvp.html",
            "--template-dir=" + get_template_dir(),
            "--report=" + report,
    ]
    if args is not None:
        defualt_args.extend(args)
    result = pytest.main(defualt_args)
    return result


def __update_line_coverage__(__line_coverage__=None):
    if __line_coverage__ is None:
        return None
    if len(__line_coverage__) == 0:
        return None
    hint, all = convert_line_coverage(__line_coverage__, os.path.join(__output_report_dir__, "line_dat"))
    assert os.path.exists(os.path.join(__output_report_dir__, "line_dat/index.html")), "Failed to convert line coverage"

    return {
        "hints": hint,
        "total": all,
        "grate": __report_info__.get("line_grate", 90),
    }


def __update_func_coverage__(__func_coverage__):
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
        nonlocal point_num_hints, point_num_total, bin_num_hints, bin_num_total, has_once
        data = json.loads(g)
        if data["has_once"]:
            has_once = True
        point_num_hints += data["point_num_hints"]
        point_num_total += data["point_num_total"]
        bin_num_hints += data["bin_num_hints"]
        bin_num_total += data["bin_num_total"]
        return data
    def merge_dicts(dict1, dict2):
        """Recursively merge two dictionaries."""
        result = dict1.copy()  # Start with keys and values of dict1
        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dicts(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    result[key] += value
                elif isinstance(result[key], bool) and isinstance(value, bool):
                    result[key] = result[key] and value
                elif isinstance(result[key], int) and isinstance(value, int):
                    result[key] += value
                elif result[key] == value:
                    continue  # Same value, do nothing
                else:
                    raise ValueError(f"Conflict at key '{key}': {result[key]} vs {value}")
            else:
                result[key] = value
        return result
    def merge_dicts_list(dicts: list):
        """Merge a list of dictionaries."""
        result = {}
        for d in dicts:
            if d["name"] in result:
                result[d["name"]] = merge_dicts(result[d["name"]], d)
            else:
                result[d["name"]] = d
        return [v for _, v in result.items()]
    coverage["groups"] = merge_dicts_list([parse_group(g) for g in __func_coverage__])
    for data in coverage["groups"]:
        group_num_total += 1
        if data["hinted"]:
            group_num_hints += 1
    coverage["group_num_total"] = group_num_total
    coverage["group_num_hints"] = group_num_hints
    coverage["point_num_total"] = point_num_total
    coverage["point_num_hints"] = point_num_hints
    coverage["bin_num_total"] = bin_num_total
    coverage["bin_num_hints"] = bin_num_hints
    coverage["grate"] = 100
    coverage["has_once"] = has_once
    return coverage


__report_info__ = {
    "user": None,
    "title": "XiangShan-BPU UT-Test Report",
    "meta": {},
}


def process_context(context, config):
    def set_ctx(key, value):
        if value is None:
            return
        context[key] = value

    for k in ["Plugins", "Packages"]:
        context["metadata"].pop(k, None)

    set_ctx("user", __report_info__["user"])
    set_ctx("title",  __report_info__["title"])
    context["metadata"].update(__report_info__["meta"])

    coverage_func_list = []
    coverage_func_keys = []
    coverage_line_list = []
    coverage_line_keys = []

    for t in context["tests"]:
        for p in t["phases"]:
            if hasattr(p["report"], "__coverage_group__"):
                for fc_data in p["report"].__coverage_group__:
                    key = "%s-%s" % (fc_data["hash"], fc_data["id"])
                    if key in coverage_func_keys:
                        continue
                    coverage_func_keys.append(key)
                    coverage_func_list.append(fc_data["data"])
            if hasattr(p["report"], "__line_coverage__"):
                lc_data = p["report"].__line_coverage__
                key = "%s-%s" % (lc_data["hash"], lc_data["id"])
                if key in coverage_line_keys:
                    continue
                coverage_line_keys.append(key)
                coverage_line_list.append(lc_data["data"])

    context["coverages"] = {
        "line": __update_line_coverage__(coverage_line_list),
        "functional": __update_func_coverage__(coverage_func_list)
    }


def set_func_coverage(request, g):
    if not isinstance(g, list):
        g = [g]
    for i in g:
        assert isinstance(i, CovGroup), "g should be an instance of CovGroup or list of CovGroup"
    request.node.__coverage_group__ = [str(x) for x in g]


def set_line_coverage(request, datfile):
    assert isinstance(datfile, str), "datfile should be a string"
    request.node.__line_coverage__ = datfile


def process_func_coverage(item, call, report):
    if call.when != 'teardown':
        return
    if hasattr(item, "__coverage_group__"):
        groups = []
        for g in item.__coverage_group__:
            assert isinstance(g, str), "item.__coverage_group__ should be an instance of CovGroup"
            groups.append({
                "hash": "%s" % hash(g),
                "id": "H%s-P%s" % (uuid.getnode(), os.getpid()),
                "data": g
            })
        report.__coverage_group__ = groups
    if hasattr(item, "__line_coverage__"):
        assert isinstance(item.__line_coverage__, str), "item.__line_coverage__ should be a string"
        report.__line_coverage__ = {
            "hash": "%s" % hash(item.__line_coverage__),
            "id": "H%s-P%s" % (uuid.getnode(), os.getpid()),
            "data": item.__line_coverage__
        }
    return report


def set_user_info(name, code):
    global __report_info__
    __report_info__["user"] = {"name": name, "code": code}

def set_title_info(title):
    global __report_info__
    __report_info__["title"] = title

def set_meta_info(key, value, is_del=False):
    global __report_info__
    if is_del:
        del __report_info__["meta"][key]
    else:
        __report_info__["meta"][key] = value

def set_line_good_rate(rate):
    global __report_info__
    __report_info__["line_grate"] = rate
