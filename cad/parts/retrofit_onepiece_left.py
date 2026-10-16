"""Mirror of retrofit_onepiece for the other side of the car (aiming posts on the other side,
so both lights have their adjusters toward the fender). Outline and neon lines are symmetric."""
import importlib.util
from pathlib import Path

from build123d import Plane, mirror

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
PRINT_ROTATION = base.PRINT_ROTATION


def make():
    return mirror(base.make(), about=Plane.YZ)
