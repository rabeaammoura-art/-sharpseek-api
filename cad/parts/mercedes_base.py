"""Mercedes tray base plate (separate print). Its two pockets catch the handle's legs and stop
them just past vertical, locking the tray open."""
from build123d import Location

from _mercedes import P, base

STL_TOLERANCE = (0.01, 0.1)


def make():
    return base(P).moved(Location((0, 0, P.base_t)))  # flat on the bed
