"""Mercedes tray, print-in-place in one piece, collapsed: frame + 3 x N telescoping rings +
handle ring with hinge pins (handle flat in the flange plane)."""
from build123d import Compound

from _mercedes import P, frame, handle, ring

# Fine facets: 0.4 mm gaps between concentric arcs lose < 0.01 mm to faceting.
STL_TOLERANCE = (0.005, 0.05)


def make():
    bodies = [frame(P), handle(P)]
    bodies += [ring(P, k, th) for th in P.compartment_angles for k in range(1, P.n_rings + 1)]
    return Compound(bodies)
