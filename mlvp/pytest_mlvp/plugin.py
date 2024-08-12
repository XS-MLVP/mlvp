import os
import pytest
from ..reporter import process_func_coverage, process_context
from ..reporter import get_template_dir, get_default_report_name, set_output_report

@pytest.hookimpl(trylast=True, optionalhook=True)
def pytest_reporter_context(context, config):
    process_context(context, config)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    return process_func_coverage(item, call, report)

def pytest_addoption(parser):
    group = parser.getgroup("reporter")
    group.addoption(
        "--gen-report",
        action="store_true",
        default=False,
        help="Generate the report."
    )

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if config.getoption("--gen-report"):
        config.option.template = ["html/mlvp.html"]
        config.option.template_dir = [get_template_dir()]

        default_report_name = get_default_report_name()
        config.option.report = [default_report_name]
        print(default_report_name)

        set_output_report(default_report_name)
