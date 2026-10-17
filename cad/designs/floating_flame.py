"""Floating flame: a glowing candle flame hovering inside the spinning spiral.

The flame is a surface of revolution, so like the ball it looks still while it spins.
A standard LED tea light (38 mm, CR2032, built-in flicker) sits inside it and spins
with it, so no wires cross the bearing.

  flame_shell - translucent upper shell, glued to the rotor's saddle (print opening-down)
  flame_cup   - bottom cup that holds the tea light; friction-fits into the shell's collar
                (print split-face-down). Pull it off to switch the tea light on/off.
Print both in translucent / natural PLA or PETG; 1.2 mm walls let the flicker glow through.
"""
import numpy as np
from build123d import *

from spiral import Spiral

# LED tea light (measure yours: most are 38 mm across, 16-18 mm body, ~45 mm with the fake flame)
TEALIGHT_D = 38.0
TEALIGHT_BODY_H = 18.0
TEALIGHT_H = 45.0

WALL = 1.2
FLOOR_Z = 8.0            # cup floor height above the flame's bottom tip
SPLIT_Z = 13.0           # shell/cup split, a little below the widest point
COLLAR_H = 6.0
SLIDE_FIT = 0.1          # per side, for the cup's sleeve in the shell's collar
POCKET_R = TEALIGHT_D / 2 + 0.5

# Outer silhouette (radius, height) from the bottom tip to the pointed top.
PROFILE = [(0, 0), (14, 1.5), (21, 6), (25.5, 13), (27, 21), (26, 31), (21.5, 42),
           (15.5, 53), (10, 64), (6, 76), (3, 88), (0, 102)]
HEIGHT = PROFILE[-1][1]


def _outline() -> Edge:
    return Spline(*[(r, 0, z) for r, z in PROFILE], tangents=[(1, 0, 0), (-0.15, 0, 1)])


def _samples(n=2000) -> np.ndarray:
    e = _outline()
    return np.array([[(p := e @ (i / n)).X, p.Z] for i in range(n + 1)])


_S = _samples()
MAX_R = float(_S[:, 0].max())
WIDEST_Z = float(_S[_S[:, 0].argmax(), 1])


def radius_at(z: float) -> float:
    rising = _S[: _S[:, 0].argmax() + 1]
    falling = _S[_S[:, 0].argmax():]
    part = rising if z <= WIDEST_Z else falling[::-1]
    return float(np.interp(z, part[:, 1], part[:, 0]))


# Flame bottom sits 15 mm above the hub; helix tall enough to clear the tip.
SPIRAL = Spiral(payload_r=MAX_R, helix_h=130.0, contact_t=(15 + WIDEST_Z) / 130.0, saddle_h=14.0)
FLAME_Z = SPIRAL.contact_z - WIDEST_Z   # assembly height of the flame's bottom tip


def _revolve(*edges: Edge) -> Part:
    """Revolve an outline that runs from the axis, out and back to the axis."""
    z0, z1 = (edges[0] @ 0).Z, (edges[-1] @ 1).Z
    face = Face(Wire([*edges, Edge.make_line((0, 0, z1), (0, 0, z0))]))
    return revolve(face, Axis.Z)


def _solid() -> Part:
    return _revolve(_outline())


def _cavity() -> Part:
    """Outline pushed WALL inward along its 2D normal (a 3D offset fails at the tip)."""
    d = np.gradient(_S, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], axis=1)
    pts = _S + WALL * n / np.linalg.norm(n, axis=1, keepdims=True)
    pts = pts[pts[:, 0] > 3.5][::40]
    z0, z1 = pts[0, 1], pts[-1, 1]
    # Turn onto the axis almost horizontally, so the spline can't bulge out through the tip.
    pts = np.vstack([[0, z0], pts, [0, z1 + 1]])
    return _revolve(Spline(*[(r, 0, z) for r, z in pts], tangents=[(1, 0, 0), (-1, 0, 0.3)]))


def _slab(z0: float, z1: float) -> Part:
    return Pos(0, 0, z0) * Cylinder(200, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _tube(r_out: float, r_in: float, z0: float, h: float) -> Part:
    return Pos(0, 0, z0) * (Cylinder(r_out, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
                            - Cylinder(r_in, h, align=(Align.CENTER, Align.CENTER, Align.MIN)))


COLLAR_R = radius_at(SPLIT_Z) - WALL - 0.3   # bore of the shell's collar


def shell(placed=False) -> Part:
    outer = _solid()
    # Leave a collar of material at the bottom of the cavity for the cup's sleeve.
    cavity = _cavity() - _tube(MAX_R + 1, COLLAR_R, SPLIT_Z - 1, COLLAR_H + 1)
    part = (outer & _slab(SPLIT_Z, HEIGHT + 1)) - cavity
    return Pos(0, 0, FLAME_Z) * part if placed else Pos(0, 0, -SPLIT_Z) * part


def cup(placed=False) -> Part:
    part = _solid() & _slab(-1, SPLIT_Z)
    part -= Pos(0, 0, FLOOR_Z) * Cylinder(POCKET_R, SPLIT_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part += _tube(COLLAR_R - SLIDE_FIT, POCKET_R, SPLIT_Z, COLLAR_H - 0.5)
    if placed:
        return Pos(0, 0, FLAME_Z) * part
    # Upside down, sleeve on the bed: only a 1.6 mm ledge overhangs.
    return Pos(0, 0, COLLAR_H - 0.5) * Rot(180, 0, 0) * Pos(0, 0, -SPLIT_Z) * part


def tealight(placed=True) -> Part:
    """Stand-in for previews."""
    body = Cylinder(TEALIGHT_D / 2, TEALIGHT_BODY_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bulb = Pos(0, 0, TEALIGHT_BODY_H) * Cone(5, 1, TEALIGHT_H - TEALIGHT_BODY_H,
                                              align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, FLAME_Z + FLOOR_Z) * (body + bulb)


def base() -> Part:
    return SPIRAL.base()


def rotor() -> Part:
    return SPIRAL.rotor(Pos(0, 0, FLAME_Z) * _solid())


def ring() -> Part:
    return SPIRAL.ring()


def assembly() -> Compound:
    return SPIRAL.assembly(rotor(), shell(placed=True), cup(placed=True), tealight())
