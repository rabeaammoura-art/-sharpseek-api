"""Floating-ball spiral illusion (shared geometry for parts/floating_*.py).

How the trick works: a 40 mm ping-pong ball sits exactly on the spin axis and is
glued to the inside of a one-turn helix. Helix + top ring + hub spin together on a
608 bearing. A sphere spinning about its own centre looks perfectly still, so the
eye sees a motionless ball while the spiral sweeps "through" it -> it seems to float.

Parts (all print without supports except the rotor's helix, which needs tree supports):
  base  - weighted foot with a fixed 8 mm axle for the bearing's inner race
  rotor - hub (608 bearing pressed in from below) + helix + glue saddle for the ball
  ring  - top ring, pinned and glued onto the helix's top end
"""
from math import cos, radians, sin

from build123d import *

# Bought parts
BALL_D = 40.0           # standard ping-pong ball
BEARING_OD = 22.0       # 608 skateboard bearing: 8 x 22 x 7
BEARING_ID = 8.0
BEARING_H = 7.0
FIT = 0.15              # press-fit clearance per side; tune for your printer

# Base
BASE_D = 64.0
BASE_H = 20.0
AXLE_D = BEARING_ID - 0.1
SHOULDER_D = 11.0       # touches only the inner race, so the outer race spins freely
SHOULDER_H = 1.0
WEIGHT_POCKET_D = 50.0  # underside pocket for coins/steel washers -> stable when flicked
WEIGHT_POCKET_H = 10.0

# Rotor
HUB_D = 56.0
HUB_H = BEARING_H + 3.0
RIBBON_W = 12.0         # vertical height of the ribbon
RIBBON_T = 4.0          # radial thickness
HELIX_R = BALL_D / 2 + RIBBON_T / 2   # inner face of ribbon kisses the ball
HELIX_H = 90.0          # one full turn
PIN_D = 4.0
PIN_H = 6.0

# Top ring
RING_OD = 60.0
RING_ID = 36.0
RING_H = 10.0

# Assembly heights (z = 0 on the table)
HUB_Z = BASE_H + SHOULDER_H                 # hub underside rests on the bearing
HELIX_Z0 = HUB_Z + HUB_H
BALL_Z = HELIX_Z0 + HELIX_H / 2
TOP_Z = HELIX_Z0 + HELIX_H


def base() -> Part:
    with BuildPart() as p:
        Cylinder(BASE_D / 2, BASE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(p.edges().group_by(Axis.Z)[-1], 1.5)
        chamfer(p.edges().group_by(Axis.Z)[0], 0.8)
        with Locations((0, 0, BASE_H)):
            Cylinder(SHOULDER_D / 2, SHOULDER_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            Cylinder(AXLE_D / 2, SHOULDER_H + BEARING_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(p.edges().group_by(Axis.Z)[-1], 0.6)
        Cylinder(WEIGHT_POCKET_D / 2, WEIGHT_POCKET_H, mode=Mode.SUBTRACT,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def _helix_point(t: float) -> Vector:
    a = radians(360 * t)
    return Vector(HELIX_R * cos(a), HELIX_R * sin(a), HELIX_H * t)


def rotor() -> Part:
    """Modelled in print orientation: hub on the bed, z = 0 at the hub underside."""
    with BuildPart() as p:
        Cylinder(HUB_D / 2, HUB_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(p.edges().group_by(Axis.Z)[-1], 1.0)
        # Bearing pocket opens onto the bed, so it prints without support.
        Cylinder(BEARING_OD / 2 + FIT, BEARING_H, mode=Mode.SUBTRACT,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(SHOULDER_D / 2 + 0.5, HUB_H, mode=Mode.SUBTRACT,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

        path = Wire([Edge.make_helix(HELIX_H, HELIX_H, HELIX_R, center=(0, 0, HUB_H))])
        with BuildSketch(Plane(origin=path @ 0, x_dir=(1, 0, 0), z_dir=path % 0)):
            Rectangle(RIBBON_T, RIBBON_W)
        sweep(path=path, is_frenet=True)

        # Sink the ribbon's ends into the hub and give the top a pin for the ring.
        top = _helix_point(1) + Vector(0, 0, HUB_H)
        with Locations((0, 0, top.Z)):
            Box(200, 200, 50, mode=Mode.SUBTRACT, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((top.X, top.Y, top.Z - RIBBON_W / 2)):
            Box(RIBBON_T, RIBBON_W, RIBBON_W / 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((top.X, top.Y, top.Z)):
            Cylinder(PIN_D / 2, PIN_H, align=(Align.CENTER, Align.CENTER, Align.MIN))

        # Glue saddle: a small pad on the inner face, hollowed to the ball's curvature.
        mid = _helix_point(0.5) + Vector(0, 0, HUB_H)
        k = (BALL_D / 2 - 1) / HELIX_R
        with Locations((mid.X * k, mid.Y * k, mid.Z)):
            Box(6, 14, 18)
        with Locations((0, 0, mid.Z)):
            Sphere(BALL_D / 2, mode=Mode.SUBTRACT)
        # Trim anything that grew below the bed.
        with Locations((0, 0, -50)):
            Box(200, 200, 100, mode=Mode.SUBTRACT)
    return p.part


def ring() -> Part:
    """Printed flat; the pin hole sits over the helix's top end."""
    with BuildPart() as p:
        Cylinder(RING_OD / 2, RING_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(RING_ID / 2, RING_H, mode=Mode.SUBTRACT,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(p.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 1.5)
        top = _helix_point(1)
        with Locations((top.X, top.Y, 0)):
            Cylinder(PIN_D / 2 + FIT, PIN_H + 0.5, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def assembly() -> Part:
    """Everything in place, ball included - for previews only, not for printing."""
    parts = [
        base(),
        rotor().moved(Location((0, 0, HUB_Z))),
        ring().moved(Location((0, 0, TOP_Z))),
        Sphere(BALL_D / 2).moved(Location((0, 0, BALL_Z))),
    ]
    return Compound(children=parts)
