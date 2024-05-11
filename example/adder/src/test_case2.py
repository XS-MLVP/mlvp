from Adder import *

import mlvp.reporter as rp
import mlvp

import random

async def adder_test_2(dut):
    dut:Adder32 = dut

    mlvp.create_task(mlvp.start_clock(dut))
    print('\n')
    for i in range(10):
        dut.a.value   = random.randint(0, 10000)
        dut.b.value   = random.randint(0, 10000)
        dut.cin.value = random.randint(0, 1)

        await mlvp.ClockCycles(dut, 1)

        sum = dut.sum.value

        # check
        print("a: ", dut.a.value, " b: ", dut.b.value, " cin: ", dut.cin.value, " sum: ", sum, "expected: ", dut.a.value + dut.b.value + dut.cin.value)

        assert(sum == dut.a.value + dut.b.value + dut.cin.value)


def test_case2(request):
    dut = Adder32(
        waveform_filename = "report/adder_t2.fst",
        coverage_filename = "report/adder_t2.dat"
    )
    mlvp.run(adder_test_2(dut))
    dut.finalize()
    rp.set_line_coverage(request, "report/adder_t2.dat")
