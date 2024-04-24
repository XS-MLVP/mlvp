
import pytest
from mlvp.reporter import process_context, process_func_coverage


@pytest.hookimpl(optionalhook=True)
def pytest_reporter_context(context, config):
    process_context(context, config)


@pytest.hookimpl(optionalhook=True)
def pytest_runtest_makereport(item, call):
    process_func_coverage(item, call)
