import mlvp
from mlvp import Bundle


def gen_bundle_code(bundle_name: str, dut, prefix: str = "", max_width: int = 120):
    """
    Generates a bundle using all the signals with the specified prefix.

    Args:
        bundle_name: The name of the bundle.
        dut: The DUT.
        prefix: The prefix of the signals.

    Returns:
        The bundle code.
    """

    signals = []

    for dict in Bundle.dut_all_signals(dut):
        name = dict["name"]
        if name.startswith(prefix):
            signals.append(name[len(prefix):])

    signals.sort()
    signals_num = len(signals)

    assert signals_num > 0, f"No signals found with prefix {prefix}"


    if signals_num == 0:
        end_code = f" = Signal()"
    else:
        end_code = f" = Signals({signals_num})"

    code = f"from mlvp import Bundle\nfrom mlvp import Signals, Signal\n\nclass {bundle_name}(Bundle):\n"
    code_line = "\t"
    index = 0

    TAB_SIZE = 4
    while index < signals_num:
        code_line = "\t"

        code_line += f"{signals[index]}, "
        current_width = TAB_SIZE + len(signals[index]) + 2 + 1
        index += 1

        while index < signals_num and current_width + len(signals[index]) + 2 <= max_width:
            code_line += f"{signals[index]}, "
            current_width += len(signals[index]) + 2
            index += 1

        if index == signals_num:
            code_line = code_line[:-2]
            current_width -= 3

            if current_width + len(end_code) <= max_width:
                code_line += end_code + "\n"
            else:
                code_line += " \\\n\t" + end_code[1:] + "\n"
        else:
            code_line += "\\\n"

        code += code_line

    return code
