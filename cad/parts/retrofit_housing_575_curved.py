"""Variant of retrofit_housing: one 5.75" light, curved indicator (top) and fog (bottom)
windows wrapping around it like the original amber indicator.

Same shell and screw positions as the 2 x 4.5" variant, so switching later means printing
only a new face plate.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

WINDOWS = base.crescent_windows(base.SINGLE_575[0])


def make():
    return base.make(lights=base.SINGLE_575, top_window=(0, 0, 0), bottom_window=(0, 0, 0),
                     extra_cuts=WINDOWS)
