"""TPU gasket between the one-piece housing's back and the fender: a flat band round the
housing edge, out to the rear rib, with holes for the 4 car screws and a soft sealing bead
on the fender side. Same gasket for both lights. Print flat in TPU 95A, ~1.6 mm.
"""
import importlib.util
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
op = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(op)
PRINT_ROTATION = ("X", 90)  # housing side down on the bed, bead up

HOLE_D = 6.0
BEAD_W, BEAD_H = 1.2, 0.6  # sealing bead, pressed flat when the car screws are tight
BAND = op.base.outline() - op.base.outline(op.GASKET_IN)
_mid = (op.GASKET_IN) / 2
BEAD = op.base.outline(_mid - BEAD_W / 2) - op.base.outline(_mid + BEAD_W / 2)


def make() -> Part:
    back = Plane.XZ.offset(op.FACE_T)  # housing back = gasket's front
    with BuildPart() as g:
        with BuildSketch(back):
            add(BAND)
            with Locations(*op.car_holes()):
                Circle(HOLE_D / 2, mode=Mode.SUBTRACT)
        extrude(amount=op.GASKET_T)
        with BuildSketch(back.offset(op.GASKET_T)):
            add(BEAD)
            with Locations(*op.car_holes()):
                Circle(HOLE_D / 2 + 1.5, mode=Mode.SUBTRACT)
        extrude(amount=BEAD_H)
    return g.part
