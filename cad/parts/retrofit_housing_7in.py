"""Variant of retrofit_housing: one 7" light raised to the widest part, indicator + fog below.

The 7" rim (177.8) is wider than the shell, so it sits on the face plate's front; only the
rear body passes through. Top screws move up out from under the rim.
"""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

INDICATOR_WINDOW = (110, 18, -78)
FOG_WINDOW = (100, 20, -105)
SCREW_Z = (110, -95)


def make():
    return base.make(lights=base.SEVEN_IN, top_window=INDICATOR_WINDOW, bottom_window=FOG_WINDOW,
                     screw_z=SCREW_Z)
