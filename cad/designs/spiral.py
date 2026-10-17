"""Spinning-spiral illusion: base, rotor and top ring shared by every payload.

How the trick works: an object that is rotationally symmetric about the spin axis
(ball, flame, drop...) is glued to the inside of a one-turn helix. Helix + top ring +
hub spin together on a 608 bearing. The object spins about its own axis, so it looks
perfectly still while the spiral sweeps "through" it -> it seems to float.

Parts (all print without supports except the rotor's helix, which needs tree supports):
  base  - weighted foot with a fixed 8 mm axle for the bearing's inner race
  rotor - hub (608 bearing pressed in from below) + helix + glue saddle for the payload
  ring  - top ring, pinned and glued onto the helix's top end
"""
from dataclasses import dataclass
from math import cos, radians, sin

from build123d import *

# Bought parts
BEARING_OD = 22.0       # 608 skateboard bearing: 8 x 22 x 7
BEARING_ID = 8.0
BEARING_H = 7.0
FIT = 0.15              # press-fit clearance per side; tune for your printer

# Base
BASE_H = 20.0
AXLE_D = BEARING_ID - 0.1
SHOULDER_D = 11.0       # touches only the inner race, so the outer race spins freely
SHOULDER_H = 1.0
WEIGHT_POCKET_H = 10.0  # underside pocket for coins/steel washers -> stable when flicked

# Rotor
HUB_H = BEARING_H + 3.0
RIBBON_W = 12.0         # vertical height of the ribbon
RIBBON_T = 4.0          # radial thickness
PIN_D = 4.0
PIN_H = 6.0

RING_H = 10.0
HUB_Z = BASE_H + SHOULDER_H  # hub underside rests on the bearing


@dataclass
class Spiral:
    payload_r: float        # largest radius of the payload; the ribbon's inner face kisses it
    helix_h: float          # height of the one full turn
    contact_t: float = 0.5  # fraction of the turn where the payload's widest point touches
    saddle_h: float = 18.0  # height of the glue pad

    @property
    def helix_r(self) -> float:
        return self.payload_r + RIBBON_T / 2

    @property
    def hub_d(self) -> float:
        return 2 * (self.helix_r + RIBBON_T / 2) + 4

    @property
    def base_d(self) -> float:
        return self.hub_d + 8

    @property
    def ring_od(self) -> float:
        return 2 * (self.helix_r + RIBBON_T / 2) + 4

    @property
    def ring_id(self) -> float:
        return 2 * (self.helix_r - RIBBON_T / 2) - 4

    @property
    def helix_z0(self) -> float:
        """Assembly height of the helix start (z = 0 on the table)."""
        return HUB_Z + HUB_H

    @property
    def contact_z(self) -> float:
        """Assembly height where the payload's widest point touches the ribbon."""
        return self.helix_z0 + self.helix_h * self.contact_t

    @property
    def top_z(self) -> float:
        return self.helix_z0 + self.helix_h

    def helix_point(self, t: float) -> Vector:
        a = radians(360 * t)
        return Vector(self.helix_r * cos(a), self.helix_r * sin(a), self.helix_h * t)

    def base(self) -> Part:
        with BuildPart() as p:
            Cylinder(self.base_d / 2, BASE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            chamfer(p.edges().group_by(Axis.Z)[-1], 1.5)
            chamfer(p.edges().group_by(Axis.Z)[0], 0.8)
            with Locations((0, 0, BASE_H)):
                Cylinder(SHOULDER_D / 2, SHOULDER_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
                Cylinder(AXLE_D / 2, SHOULDER_H + BEARING_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            chamfer(p.edges().group_by(Axis.Z)[-1], 0.6)
            Cylinder(self.base_d / 2 - 7, WEIGHT_POCKET_H, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        return p.part

    def rotor(self, payload: Part) -> Part:
        """Modelled in print orientation: hub on the bed, z = 0 at the hub underside.

        `payload` is the object in assembly position; it carves the glue saddle.
        """
        with BuildPart() as p:
            Cylinder(self.hub_d / 2, HUB_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            chamfer(p.edges().group_by(Axis.Z)[-1], 1.0)
            # Bearing pocket opens onto the bed, so it prints without support.
            Cylinder(BEARING_OD / 2 + FIT, BEARING_H, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
            Cylinder(SHOULDER_D / 2 + 0.5, HUB_H, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))

            path = Wire([Edge.make_helix(self.helix_h, self.helix_h, self.helix_r, center=(0, 0, HUB_H))])
            with BuildSketch(Plane(origin=path @ 0, x_dir=(1, 0, 0), z_dir=path % 0)):
                Rectangle(RIBBON_T, RIBBON_W)
            sweep(path=path, is_frenet=True)

            # Flatten the ribbon's top end and give it a pin for the ring.
            top = self.helix_point(1) + Vector(0, 0, HUB_H)
            with Locations((0, 0, top.Z)):
                Box(400, 400, 50, mode=Mode.SUBTRACT, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((top.X, top.Y, top.Z - RIBBON_W / 2)):
                Box(RIBBON_T, RIBBON_W, RIBBON_W / 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((top.X, top.Y, top.Z)):
                Cylinder(PIN_D / 2, PIN_H, align=(Align.CENTER, Align.CENTER, Align.MIN))

            # Glue saddle: a pad on the inner face, hollowed to the payload's shape.
            c = self.helix_point(self.contact_t) + Vector(0, 0, HUB_H)
            k = (self.payload_r - 1) / self.helix_r
            with Locations(Location((c.X * k, c.Y * k, c.Z), (0, 0, 360 * self.contact_t))):
                Box(6, 14, self.saddle_h)
            add(payload.moved(Location((0, 0, -HUB_Z))), mode=Mode.SUBTRACT)
            # Trim anything that grew below the bed.
            with Locations((0, 0, -50)):
                Box(400, 400, 100, mode=Mode.SUBTRACT)
        return p.part

    def ring(self) -> Part:
        """Printed flat; the pin hole sits over the helix's top end."""
        with BuildPart() as p:
            Cylinder(self.ring_od / 2, RING_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            Cylinder(self.ring_id / 2, RING_H, mode=Mode.SUBTRACT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
            fillet(p.edges().filter_by(GeomType.CIRCLE).group_by(Axis.Z)[-1], 1.5)
            top = self.helix_point(1)
            with Locations((top.X, top.Y, 0)):
                Cylinder(PIN_D / 2 + FIT, PIN_H + 0.5, mode=Mode.SUBTRACT,
                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        return p.part

    def assembly(self, rotor: Part, *payload: Part) -> Compound:
        """Everything in place, payload included - for previews only, not for printing."""
        return Compound(children=[
            self.base(),
            rotor.moved(Location((0, 0, HUB_Z))),
            self.ring().moved(Location((0, 0, self.top_z))),
            *payload,
        ])
