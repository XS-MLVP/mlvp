import pytest
import inspect
from ..reporter import process_func_coverage, process_context
from ..reporter import get_template_dir, get_default_report_name, set_output_report
from .. import run
import os

"""
toffee report
"""

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
        "--toffee-report",
        action="store_true",
        default=False,
        help="Generate the report."
    )

    group.addoption(
        "--report-name",
        action="store",
        default=None,
        help="The name of the report."
    )

    group.addoption(
        "--report-dir",
        action="store",
        default=None,
        help="The dir of the report."
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.addinivalue_line("markers", "toffee_async: mark test to run with toffee's event loop")

    if config.getoption("--toffee-report"):
        config.option.template = ["html/toffee.html"]
        config.option.template_dir = [get_template_dir()]

        report_name = config.getoption("--report-name")
        if report_name is None:
            report_name = get_default_report_name()

        report_dir = config.getoption("--report-dir")
        if report_dir is None:
            report_dir = "reports"
        report_name = os.path.join(report_dir, report_name)

        config.option.report = [report_name]
        set_output_report(report_name)

"""
toffee async test
"""

@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if "toffee_async" in pyfuncitem.keywords:
        func = pyfuncitem.obj
        assert inspect.iscoroutinefunction(func), "test marked with toffee_async must be a coroutine function"

        signature = inspect.signature(func)
        filtered_funcargs = {
            k: v for k, v in pyfuncitem.funcargs.items() if k in signature.parameters
        }

        run(func(**filtered_funcargs))

        return True

    return None

from .prerequest import PreRequest

@pytest.fixture()
def toffee_pre_request(request):
    pre_request_info = PreRequest(request)
    pre_request_info.request_name = str(request._pyfuncitem).strip('<').strip('>').split(' ')[-1]
    yield pre_request_info

    pre_request_info.finish(request)
