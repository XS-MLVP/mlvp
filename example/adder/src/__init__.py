from mlvp.reporter import *

# Start of the test case here！
if __name__ == '__main__':
    set_meta_info('test_case', 'adder_32')
    report = "report/report.html"
    generate_pytest_report(report, ['-s'])

    print('Hello, MLVP! :D')