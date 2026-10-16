"""One-piece retrofit housing: the face plate alone, no rear shell and no light tube.

Idea from the user's own Fusion sketch. The face plate (traced W114 outline, curved
indicator/fog windows) screws straight onto the car. The 5.75" light hangs from a separate
aiming bracket (retrofit_onepiece_bracket.py) bolted to the 4 M5 holes on its back; the
bracket rides on 3 posts behind the face plate with a spring screw on each post, like the
original headlight's adjusters. Turning the screws tilts the light up/down and left/right.
Prints face-down on the bed, posts pointing up: no supports.
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
TILT_GAP = 4.0             # radial gap around the light so it can tilt ~3 deg each way
OPENING_D = LIGHT_D + 2 * TILT_GAP

# Car fixing holes through the face plate (PLACEHOLDER positions: match the car's screws).
CAR_HOLE_D = 5.5
CAR_HOLE_INSET = 7         # hole centre distance in from the outline edge

# --- Aiming: 3 posts behind the face plate, one spring screw (M5) on each ---
# P = pivot corner (set once), V above it = up/down, H beside it = left/right.
POSTS = {"P": (-74, -70), "V": (-74, 70), "H": (74, -70)}
PAD_DEPTH = 62             # PLACEHOLDER: light front face -> mounting-pad face on its back
SPRING_GAP = 10            # spring length between post end and bracket (reuse the old ones)
POST_D = 14
POST_END_Y = -(PAD_DEPTH - SPRING_GAP)  # posts stop here; the bracket sits at -PAD_DEPTH
M5_CLEAR = 5.5
M5_NUT_AF = 8.0 + 0.3      # trapped M5 nut in each post end
M5_NUT_H = 4.0 + 0.4
NUT_FROM_END = 4.0

WINDOWS = base.crescent_windows((OPENING_D - base.LIGHT_CLEARANCE, LIGHT_Z))


def car_holes():
    z_top, z_bot = base.FLANGE_PROFILE[0][1], base.FLANGE_PROFILE[-1][1]
    x_side = base.half_width(0, 0) - CAR_HOLE_INSET
    return [(0, z_top - CAR_HOLE_INSET), (0, z_bot + CAR_HOLE_INSET), (x_side, 0), (-x_side, 0)]


def make() -> Part:
    post_len = -POST_END_Y - FACE_T
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            add(base.outline())
        extrude(amount=FACE_T)  # Plane.XZ normal is -Y: grows toward the engine
        # Aiming posts.
        back = Plane.XZ.offset(FACE_T)
        with BuildSketch(back):
            with Locations(*POSTS.values()):
                Circle(POST_D / 2)
        extrude(amount=post_len)
        with BuildSketch(back.offset(post_len)):
            with Locations(*POSTS.values()):
                Circle(M5_CLEAR / 2)
        extrude(amount=-25, mode=Mode.SUBTRACT)
        # Nut trap near each post end, slot opening toward the light so the nut slides in.
        with BuildSketch(back.offset(post_len - NUT_FROM_END - M5_NUT_H)):
            for x, z in POSTS.values():
                with Locations((x, z)):
                    RegularPolygon(M5_NUT_AF / 3 ** 0.5, 6)
                with Locations((x - (POST_D / 2) * (1 if x > 0 else -1), z)):
                    Rectangle(POST_D, M5_NUT_AF)
        extrude(amount=M5_NUT_H, mode=Mode.SUBTRACT)
        # Light opening, windows, car holes.
        with BuildSketch(Plane.XZ):
            with Locations((0, LIGHT_Z)):
                Circle(OPENING_D / 2)
            for w in WINDOWS:
                add(w)
            with Locations(*car_holes()):
                Circle(CAR_HOLE_D / 2)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
    return p.part
