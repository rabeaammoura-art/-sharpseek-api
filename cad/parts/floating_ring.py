"""Floating-ball spiral illusion: ring. Geometry lives in designs/floating_ball.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "designs"))
import floating_ball


def make():
    return floating_ball.ring()
