#coding=utf8

class MObject(object):
    pass



####################  Tools  ####################
import subprocess
import os
import sys


def exe_cmd(cmd):
    # If cmd is a list, join it into a string
    if isinstance(cmd, list):
        cmd = ' '.join(cmd)
    # Run the command
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Check if the command was successful
    success = result.returncode == 0
    # Get the standard output and standard error
    stdout = result.stdout.decode('utf-8')
    stderr = result.stderr.decode('utf-8')
    return success, stdout, stderr

def parse_lines(text: str):
    pre_flage = False
    for line in text.split('\n'):
        line = line.strip()
        if line == "Overall coverage rate:":
            pre_flage = True
            continue
        if pre_flage:
            info = line.split("(")[-1].split(" ")
            return int(info[0]), int(info[2])
    return -1, -1


def convert_line_coverage(dat_file, output_dir):
    if isinstance(dat_file, list):
        for f in dat_file:
            assert os.path.exists(f), f"File not found: {f}"
        dat_file = ' '.join(dat_file)
    else:
        assert os.path.exists(dat_file), f"File not found: {dat_file}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    merged_info = os.path.join(output_dir, "merged.info")
    su, so, se = exe_cmd([
        "verilator_coverage  -write-info", merged_info, dat_file
    ])
    assert su, f"Failed to convert line coverage: {se}"
    su, so, se = exe_cmd([
        "genhtml", merged_info, "-o", output_dir
    ])
    assert su, f"Failed to convert line coverage: {se}"
    return parse_lines(so)
