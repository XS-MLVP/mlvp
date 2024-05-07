'''
    DUT Package
'''

import os
DUT_PATH = os.path.dirname(os.path.abspath(__file__)) + "/../build"
os.sys.path.append(DUT_PATH)

from UT_Adder_32bits import *

class Adder32(DUTAdder_32bits):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def finalize(self):
        super().finalize()