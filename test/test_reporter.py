import pytest
import os
from mlvp.reporter import get_template_dir

pytest_plugins = ["pytester"]

def test_sample_report(testdir):
    report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report.html")
    print(report)
    result = testdir.runpytest(
        "--template=html/mlvp.html",
        "--template-dir=" + get_template_dir(),
        "--report=" + report
    )
    print(result)


if __name__ == "__main__":
    test_sample_report()
