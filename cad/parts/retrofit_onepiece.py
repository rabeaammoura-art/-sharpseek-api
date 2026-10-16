"""One-piece retrofit housing: the face plate alone, with a tube behind it that holds the light.

Idea from the user's own Fusion sketch: no rear shell. The face plate (traced W114 outline,
curved indicator/fog windows) screws straight onto the car; a tube behind it carries the
5.75" light, which is pushed in from the back against a stop lip at the front.
Prints face-down on the bed, tube pointing up: no supports.
Axes: X = width, Z = height (on the car), Y = depth (front face at Y=0, -Y toward the engine).
"""
import importlib.util
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

FACE_T = 5.0
LIGHT_D = 141              # found 5.75" light: 141 dia x 76 deep
LIGHT_Z = 0
STOP = 3.5                 # front lip overlapping the light's rim, so it can't go through
TUBE_GAP = 0.5             # radial clearance between light and tube (ASA shrink)
TUBE_WALL = 3.0
TUBE_DEPTH = 60            # how far the tube reaches back from the face
# Car fixing holes through the face plate (PLACEHOLDER positions: match the car's screws).
CAR_HOLE_D = 5.5
CAR_HOLE_INSET = 7         # hole centre distance in from the outline edge

WINDOWS = base.crescent_windows((LIGHT_D, LIGHT_Z))


def car_holes():
    z_top, z_bot = base.FLANGE_PROFILE[0][1], base.FLANGE_PROFILE[-1][1]
    x_side = base.half_width(0, 0) - CAR_HOLE_INSET
    return [(0, z_top - CAR_HOLE_INSET), (0, z_bot + CAR_HOLE_INSET), (x_side, 0), (-x_side, 0)]


def make() -> Part:
    r_light = LIGHT_D / 2 + TUBE_GAP
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            add(base.outline())
        extrude(amount=FACE_T)  # Plane.XZ normal is -Y: grows toward the engine
        # Tube for the light.
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            with Locations((0, LIGHT_Z)):
                Circle(r_light + TUBE_WALL)
        extrude(amount=TUBE_DEPTH - FACE_T)
        # Bore: full light diameter behind the face, smaller opening at the front (stop lip).
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            with Locations((0, LIGHT_Z)):
                Circle(r_light)
        extrude(amount=TUBE_DEPTH - FACE_T, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XZ):
            with Locations((0, LIGHT_Z)):
                Circle(LIGHT_D / 2 - STOP)
            for w in WINDOWS:
                add(w)
            with Locations(*car_holes()):
                Circle(CAR_HOLE_D / 2)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
    return p.part
