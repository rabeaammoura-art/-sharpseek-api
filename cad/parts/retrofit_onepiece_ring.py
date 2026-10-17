"""Frame ring for retrofit_onepiece, fixed like the original chrome ring: one hook on top,
one screw at the bottom. A matte-black band round the housing edge (in place of the chrome
trim ring) with a skirt round its outside that wraps the housing's edge: the L-section keeps
the ring stiff and straight so it sits flush all round, and hides the housing's edge and
the TPU gasket's edge behind it.

Fitting: tilt the ring (bottom away from the car), slide its top lip down behind the
housing's top edge, swing the bottom in, then one M3 countersunk self-tapping screw at the
bottom. Removal: the reverse. It covers the car screws.
Same ring for both lights. Prints front-down, skirt up.
"""
import importlib.util
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
op = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(op)
PRINT_ROTATION = ("X", -90)  # ring front down on the bed, skirt pointing up

OUTER = op.base.outline(-(op.RING_GAP + op.SKIRT_T))
BAND = OUTER - op.base.outline(op.FRAME_W)
SKIRT = OUTER - op.base.outline(-op.RING_GAP)
LIP = op._top_band(OUTER - op.base.outline(op.LIP_DEPTH))
SCREW_CLEAR = 3.4
SCREW_CSK = 6.5            # M3 flat head


def make() -> Part:
    front = Plane.XZ.offset(-op.FRAME_H)  # the ring's front face (Y = +FRAME_H)
    with BuildPart() as r:
        with BuildSketch(front):
            add(BAND)
        extrude(amount=op.FRAME_H)
        with BuildSketch(Plane.XZ):
            add(SKIRT)
        extrude(amount=op.FACE_T + op.GASKET_T)  # down the housing's edge and the gasket's
        with BuildSketch(Plane.XZ.offset(op.FACE_T - op.LIP_T)):
            add(LIP)
        extrude(amount=op.LIP_T)
        # Bottom screw: clearance hole + countersink from the front.
        x, z = op.ring_screw()
        with BuildSketch(front):
            with Locations((x, z)):
                Circle(SCREW_CLEAR / 2)
        extrude(amount=op.FRAME_H, mode=Mode.SUBTRACT)
        h = (SCREW_CSK - SCREW_CLEAR) / 2
        with Locations((x, op.FRAME_H - h / 2, z)):
            Cone(SCREW_CSK / 2, SCREW_CLEAR / 2, h, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    return r.part
