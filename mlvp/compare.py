from . import Component, Port
from .logger import *

class Comparator(Component):
    def __init__(self, dut_port, model_ports, compare=None, match_detail=False):
        super().__init__()
        self.dut_port = dut_port
        self.model_port = model_ports
        self.compare = Comparator.__default_compare if compare is None else compare
        self.match_detail = match_detail

    async def main(self):
        while True:
            dut_item = await self.dut_port.get()
            for model in self.model_port:
                std_item = await model.get()

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

