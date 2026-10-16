"""Mirror of retrofit_onepiece_bracket for the other side of the car (ears match the
mirrored posts; the 4 light holes are symmetric)."""
import importlib.util
from pathlib import Path

from build123d import Plane, mirror

_spec = importlib.util.spec_from_file_location("retrofit_onepiece_bracket", Path(__file__).with_name("retrofit_onepiece_bracket.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)
PRINT_ROTATION = base.PRINT_ROTATION


def make():
    return mirror(base.make(), about=Plane.YZ)
