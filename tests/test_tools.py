from toffee.base import *
from toffee.reporter import set_line_coverage


def test_cmd_echo():
    success, stdout, stderr = exe_cmd(["echo", "Hello, World!"])
    assert success
    assert stdout == "Hello, World!\n"
    assert stderr == ""


def test_line_coverage_data(request):
    # set_line_coverage(request, "path_to_coverage.dat")
    pass
