"""Ø120 test coupon of the Mercedes tray: identical walls, lips, gaps and ring height,
fewer rings, and the same in-place hinge and handle. Print it first to confirm your printer frees the rings."""
from build123d import Compound

from _mercedes import Params, handle, tray_bodies

# handle_gap 0.6: the tighter Ø120 ring needs it to keep >= 0.4 mm through the swing (pin/hole identical)
COUPON = Params(tray_d=120.0, flange_w=8.0, floor_inradius_min=8.0, handle_gap=0.6,
                twist_lock=False, decor=False)  # no base, no decoration: tests the mechanism
STL_TOLERANCE = (0.005, 0.05)


def make():
    return Compound(list(tray_bodies(COUPON).values()) + [handle(COUPON)])
