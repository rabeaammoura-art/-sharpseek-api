"""Variant of retrofit_onepiece with "frame" neon DRL lines (see NEON_STYLES there)."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)


def make():
    return base.make(style="frame")
