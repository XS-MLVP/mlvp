from . import Component, Port
from .logger import *

class Comparator(Component):
    def __init__(self, dut_port: Port, std_port: Port, compare=None, match_detail=False):
        super().__init__()

        self.dut_port = Port(max_size=-1)
        self.std_port = Port(max_size=-1)
        self.dut_port.connect(dut_port)
        self.std_port.connect(std_port)

        self.compare = Comparator.__default_compare if compare is None else compare
        self.match_detail = match_detail

    async def main(self):
        while True:
            dut_item = await self.dut_port.get()
            std_item = await self.std_port.get()

            if not self.compare(dut_item, std_item):
                error(f"Mismatch\n----- STDOUT -----\n{std_item}\n----- DUTOUT -----\n{dut_item}\n------------------")
            else:
                if self.match_detail:
                    info(f"Match\n----- STDOUT -----\n{std_item}\n----- DUTOUT -----\n{dut_item}\n------------------")
                else:
                    info("Match")


    @staticmethod
    def __default_compare(item1, item2):
        return item1 == item2

all_comp_rules = []


def add_comparison(dut_port: Port, std_port: Port, compare=None, *, match_detail=False):
    comp = Comparator(dut_port, std_port, compare, match_detail)
    all_comp_rules.append(comp)
    return comp
