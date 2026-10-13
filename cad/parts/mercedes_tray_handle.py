"""Mercedes tray arc handle, laid flat on the bed (printed separately, snaps onto the hinge posts)."""
from build123d import Location

from _mercedes import P, handle

# Fine facets: 0.4 mm gaps between concentric arcs lose < 0.01 mm to faceting.
STL_TOLERANCE = (0.005, 0.05)


def make():
    return handle(P).moved(Location((0, 0, -(P.hinge_z - P.handle_t / 2))))
