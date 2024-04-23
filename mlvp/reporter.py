
from mlvp.base import MObject
import os

def get_template_dir():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


class Report(MObject):
    pass

