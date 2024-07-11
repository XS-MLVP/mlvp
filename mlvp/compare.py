from . import Component, Port
from .logger import *

class Comparator(Component):
    def __init__(self, dut_port: Port, std_port: Port, compare=None):
        super().__init__()

        self.dut_port = Port()
        self.std_port = Port()
        self.dut_port.connect(dut_port)
        self.std_port.connect(std_port)

        self.compare = Comparator.__default_compare if compare is None else compare

    async def main(self):
        while True:
            dut_item = await self.dut_port.get()
            std_item = await self.std_port.get()

            if not self.compare(dut_item, std_item):
                error(f"Mismatch: {dut_item}, {std_item}")
                break
            else:
                info(f"Match: {dut_item}, {std_item}")


    @staticmethod
    def __default_compare(item1, item2):
        return item1 == item2

all_comp_rules = []


def add_comparison(port1: Port, port2: Port):
    comp = Comparator(port1, port2)
    all_comp_rules.append(comp)
    return comp
