"""Snap-on frame ring for retrofit_onepiece: a flat matte-black ring round the housing edge
(in place of the chrome trim ring) with 8 hooks on its back. Press it on until the hooks
click into the keepers behind the face plate; no screws. It covers the car screws.
To take it off, push each catch out of its keeper window from behind.
Same ring for both lights (hook pattern is symmetric). Prints front-down, hooks up.
"""
import importlib.util
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
op = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(op)
PRINT_ROTATION = ("X", -90)  # ring front down on the bed, hooks pointing up


def make() -> Part:
    with BuildPart() as r:
        with BuildSketch(Plane.XZ.offset(-op.FRAME_H)):  # sketch at the ring's front (Y=+h)
            add(op.FRAME)
        extrude(amount=op.FRAME_H)
        for pl in op.snap_planes():
            with BuildPart(pl, mode=Mode.ADD):
                # Hook beam from the ring's back (face plate front, z=0) backward.
                with Locations((0, 0, -op.SNAP_LEN / 2)):
                    Box(op.SNAP_W, op.SNAP_T, op.SNAP_LEN)
            # Catch: flat face toward the front, ramp toward the tip. Built directly in global
            # coordinates from pl (a sketch nested in the BuildPart(pl) gets re-located).
            y1, w = op.SNAP_T / 2, op.SNAP_W
            tri = [pl.from_local_coords(Vector(-w / 2, y, z)) for y, z in
                   ((y1 - 0.01, -op.SNAP_CATCH_Z), (y1 + op.SNAP_CATCH, -op.SNAP_CATCH_Z),
                    (y1 - 0.01, -op.SNAP_LEN))]
            add(Solid.extrude(Face(Wire.make_polygon(tri, close=True)), pl.x_dir * w))
    return r.part
