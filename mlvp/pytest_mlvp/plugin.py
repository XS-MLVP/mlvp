import pytest
from ..reporter import process_func_coverage, process_context
from ..reporter import get_template_dir, get_default_report_name, set_output_report
import os

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
        "--mlvp-report",
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
    if config.getoption("--mlvp-report"):
        config.option.template = ["html/mlvp.html"]
        config.option.template_dir = [get_template_dir()]

        report_name = config.getoption("--report-name")
        if report_name is None:
            report_name = get_default_report_name()

        report_dir = config.getoption("--report-dir")
        if report_dir is not None:
            report_name = os.path.join(report_dir, report_name)
        config.option.report = [report_name]

        set_output_report(report_name)


from .prerequest import PreRequest

@pytest.fixture()
def mlvp_pre_request(request):
    pre_request_info = PreRequest()
    pre_request_info.request_name = str(request._pyfuncitem).strip('<').strip('>').split(' ')[-1]
    yield pre_request_info

    pre_request_info.finish(request)
