"""Variant of retrofit_housing: 5.75" headlight on top + 3.5" round fog/DRL below, no windows."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

# Screw pairs between the lights' outer edges and the wall: top pair beside the 5.75",
# bottom pair beside the 3.5".
SCREW_Z = (110, -100)


def make():
    return base.make(lights=base.COMBO_575_35, top_window=(0, 0, 0), bottom_window=(0, 0, 0),
                     screw_z=SCREW_Z)
