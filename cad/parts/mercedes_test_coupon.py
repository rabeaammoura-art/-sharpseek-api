"""Ø120 test coupon of the Mercedes tray: identical walls, lips, gaps and ring height,
fewer rings, no hinge posts. Print it first (~1.5 h, 55 g) to confirm your printer frees the rings."""
from build123d import Compound

from _mercedes import Params, tray_bodies

COUPON = Params(tray_d=120.0, flange_w=8.0, floor_inradius_min=8.0, hinge_posts=False)
STL_TOLERANCE = (0.005, 0.05)


def make():
    return Compound(list(tray_bodies(COUPON).values()))
