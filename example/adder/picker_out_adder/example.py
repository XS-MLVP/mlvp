from UT_Adder import *

if __name__ == "__main__":
    dut = DUTAdder()
    # dut.init_clock("clk")

    dut.Step(1)

    dut.Finish()