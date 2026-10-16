"""Aiming bracket for retrofit_onepiece: bolts to the 4 M5 holes on the back of the 5.75" light
and rides on the housing's 3 posts with a spring screw on each.

Ring around the heatsink fins + 3 arms out to the posts. Print flat.
Light pad positions are estimated from an angled product photo: print this small part first
and check it against the light before printing the housing.
"""
import importlib.util
import math
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_onepiece", Path(__file__).with_name("retrofit_onepiece.py"))
op = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(op)

T = 5.0
RING_IN_R = 50             # clears the heatsink fins (they reach ~47 mm from centre)
RING_OUT_R = 62
PAD_R = 54                 # PLACEHOLDER (photo estimate): M5 holes on the light's back
PAD_ANGLES = (26, -26, 154, 206)  # degrees from +X; two pairs either side of the cable
ARM_W = 16
EAR_HOLE_D = 6.5           # oversized so the bracket can tilt on the screws


def pad_points():
    return [(PAD_R * math.cos(math.radians(a)), op.LIGHT_Z + PAD_R * math.sin(math.radians(a)))
            for a in PAD_ANGLES]


def make() -> Part:
    plane = Plane.XZ.offset(op.PAD_DEPTH)  # front face of the bracket against the light's pads
    with BuildPart() as b:
        with BuildSketch(plane):
            with Locations((0, op.LIGHT_Z)):
                Circle(RING_OUT_R)
            for x, z in op.POSTS.values():
                # Arm from the centre out to the post, then a round ear on the post.
                length = math.hypot(x, z - op.LIGHT_Z)
                angle = math.degrees(math.atan2(z - op.LIGHT_Z, x))
                with Locations(Location((x / 2, (z + op.LIGHT_Z) / 2), angle)):
                    Rectangle(length, ARM_W)
                with Locations((x, z)):
                    Circle(ARM_W / 2 + 2)
            with Locations((0, op.LIGHT_Z)):
                Circle(RING_IN_R, mode=Mode.SUBTRACT)
            with Locations(*pad_points()):
                Circle(op.M5_CLEAR / 2, mode=Mode.SUBTRACT)
            with Locations(*op.POSTS.values()):
                Circle(EAR_HOLE_D / 2, mode=Mode.SUBTRACT)
        extrude(amount=T)
    return b.part
