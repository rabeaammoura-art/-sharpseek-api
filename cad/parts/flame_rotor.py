"""Floating flame: rotor. Geometry lives in designs/floating_flame.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "designs"))
import floating_flame


def make():
    return floating_flame.rotor()
