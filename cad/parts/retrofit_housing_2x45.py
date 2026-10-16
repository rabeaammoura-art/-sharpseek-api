"""Variant of retrofit_housing: two 4.5" round lights stacked, no windows."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


def make():
    return base.make(lights=base.TWIN_45, top_window=(0, 0), bottom_window=(0, 0))
