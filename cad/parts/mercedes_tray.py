"""Mercedes tray body: flange + dividers + 3 x N telescoping rings, collapsed (print-in-place state)."""
from build123d import Compound

from _mercedes import P, tray_bodies

# Fine facets: 0.4 mm gaps between concentric arcs lose < 0.01 mm to faceting.
STL_TOLERANCE = (0.005, 0.05)


def make():
    return Compound(list(tray_bodies(P).values()))
