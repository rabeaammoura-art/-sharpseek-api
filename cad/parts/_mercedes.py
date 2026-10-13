"""Collapsible 3-compartment "Mercedes" serving tray — shared geometry.

All plan shapes are exact inward offsets S(d) of a 120° sector of radius R_SECTOR:
    S(d) = {P : P·n1 >= d, P·n2 >= d, |P| <= R_SECTOR - d}
so every wall in the tray is a constant-thickness parallel offset and every
clearance is exact. Every solid is built from three primitives on S(d):
prism, ruled loft (45° chamfer), and boolean union/difference. The Fusion 360
script (fusion/MercedesTray/MercedesTray.py) uses the same formulas.

Coordinates: mm, Z up, tray printed collapsed with its bottom on z = 0.
"""
from dataclasses import dataclass, field
from math import cos, floor, radians, sin, sqrt

from build123d import (Axis, Box, Compound, Cylinder, Edge, Face, Location, Part, Pos, Solid,
                       Wire, extrude, loft)


@dataclass(frozen=True)
class Params:
    tray_d: float = 280.0        # outer diameter of the flange
    flange_w: float = 20.0       # flat outer rim width (handle hinges live here)
    divider_half: float = 2.0    # half width of each Mercedes divider rib (rib = 4 mm)
    wall: float = 1.2            # ring wall: 3 lines of a 0.4 mm nozzle
    clear: float = 0.4           # print-in-place gap between neighbouring rings
    lip: float = 1.6             # stop-lip radial protrusion
    lip_flat: float = 0.6        # vertical land under/over each lip's 45° chamfer
    ring_h: float = 7.0          # height of every telescoping ring
    frame_h: float = 9.0         # height of flange + dividers
    floor_t: float = 1.2         # compartment floor thickness
    floor_inradius_min: float = 12.0  # smallest allowed floor (largest inscribed circle)
    # handle (separate part, see README)
    handle_r: float = 134.0      # centreline radius of the arc handle
    handle_w: float = 10.0       # radial width of the handle band
    handle_t: float = 6.0        # band thickness (= pin diameter)
    pin_len: float = 5.5
    pin_clear: float = 0.3       # radial clearance pin <-> hinge hole
    hinge_gap: float = 0.8       # gap handle end <-> post, and handle <-> flange
    post_t: float = 6.0          # post thickness along hinge axis
    post_w: float = 12.0
    compartment_angles: tuple = field(default=(30.0, 150.0, 270.0))
    hinge_posts: bool = True     # False for the small test coupon

    # ---- derived -------------------------------------------------------
    @property
    def r_sector(self):
        return self.tray_d / 2 - self.flange_w

    @property
    def pitch(self):
        """Plan distance between consecutive rings' outer surfaces."""
        return self.wall + self.lip + self.clear

    @property
    def sector_inradius(self):
        s = sin(radians(60))
        return self.r_sector * s / (1 + s)

    @property
    def n_rings(self):
        room = self.sector_inradius - self.floor_inradius_min - (self.divider_half + self.lip + self.clear + self.wall)
        return floor(room / self.pitch) + 1

    def ring_inset(self, k):
        """Outer-surface inset of ring k (1 = outermost moving ring, n_rings = floor)."""
        return self.divider_half + self.lip + self.clear + (k - 1) * self.pitch

    @property
    def travel(self):
        """Vertical extension per step: lip chamfers meet face-to-face."""
        return self.ring_h - 2 * self.lip_flat - self.lip + self.clear

    @property
    def floor_inradius(self):
        return self.sector_inradius - self.ring_inset(self.n_rings) - self.wall

    @property
    def hinge_z(self):
        return self.frame_h + self.hinge_gap + self.handle_t / 2

    @property
    def pin_r(self):
        return self.handle_t / 2

    @property
    def hole_r(self):
        return self.pin_r + self.pin_clear

    @property
    def post_x(self):
        """(inner x, outer x) of the hinge post on the +X side."""
        outer = self.handle_r - self.handle_w / 2 - self.hinge_gap
        return outer - self.post_t, outer

    @property
    def post_top(self):
        return self.hinge_z + self.hole_r * sqrt(2) + 1.5


P = Params()


# ---------------------------------------------------------------- plan shapes
def sector_points(p: Params, d: float, theta_c: float):
    """Apex, arc start, arc mid, arc end of S(d) for the compartment centred at theta_c (deg)."""
    R = p.r_sector
    u = lambda a: (cos(radians(a)), sin(radians(a)))
    apex_r = d / cos(radians(30))
    s = sqrt((R - d) ** 2 - d ** 2)
    e1, n1 = u(theta_c - 60), u(theta_c + 30)
    e2, n2 = u(theta_c + 60), u(theta_c - 30)
    apex = (apex_r * u(theta_c)[0], apex_r * u(theta_c)[1])
    a1 = (s * e1[0] + d * n1[0], s * e1[1] + d * n1[1])
    a2 = (s * e2[0] + d * n2[0], s * e2[1] + d * n2[1])
    mid = ((R - d) * u(theta_c)[0], (R - d) * u(theta_c)[1])
    return apex, a1, mid, a2


def sector_face(p: Params, d: float, theta_c: float, z: float) -> Face:
    apex, a1, mid, a2 = [(x, y, z) for x, y in sector_points(p, d, theta_c)]
    return Face(Wire([Edge.make_line(apex, a1), Edge.make_three_point_arc(a1, mid, a2),
                      Edge.make_line(a2, apex)]))


def prism(p, d, th, z0, z1):
    return extrude(sector_face(p, d, th, z0), z1 - z0)


def frustum(p, d0, z0, d1, z1, th):
    """Ruled loft S(d0)@z0 -> S(d1)@z1: 45° faces when |d1-d0| == z1-z0."""
    return loft([sector_face(p, d0, th, z0), sector_face(p, d1, th, z1)], ruled=True)


# ---------------------------------------------------------------- solids
def lipped_cavity(p, d_open, th, height):
    """Opening S(d_open) through `height`, with a 45°-chamfered stop lip of width p.lip at the bottom."""
    lo = p.lip_flat
    return (prism(p, d_open + p.lip, th, 0, height)
            + frustum(p, d_open + p.lip, lo, d_open, lo + p.lip, th)
            + prism(p, d_open, th, lo + p.lip, height))


def ring(p: Params, k: int, th: float) -> Part:
    a, h, lo = p.ring_inset(k), p.ring_h, p.lip_flat
    envelope = (prism(p, a, th, 0, h)
                + frustum(p, a, h - lo - p.lip, a - p.lip, h - lo, th)
                + prism(p, a - p.lip, th, h - lo, h))
    if k < p.n_rings:
        cavity = lipped_cavity(p, a + p.wall, th, h)
    else:  # floor
        cavity = prism(p, a + p.wall, th, p.floor_t, h)
    return envelope - cavity


def teardrop_x(p, x0, x1):
    """Hinge hole along X, teardrop (45° roof) so it prints without support."""
    r, z = p.hole_r, p.hinge_z
    cyl = Pos((x0 + x1) / 2, 0, z) * Cylinder(r, x1 - x0, rotation=(0, 90, 0))
    q = r / sqrt(2)
    tri = Face(Wire.make_polygon([(x0, -q, z + q), (x0, q, z + q), (x0, 0, z + r * sqrt(2))]))
    return cyl + extrude(tri, x1 - x0, dir=(1, 0, 0))


def frame(p: Params) -> Part:
    body = Cylinder(p.tray_d / 2, p.frame_h, align=None)  # base on z = 0
    if not p.hinge_posts:
        for th in p.compartment_angles:
            body = body - lipped_cavity(p, p.divider_half, th, p.frame_h)
        return body
    xi, xo = p.post_x
    for side in (1, -1):
        post = Pos(side * (xi + xo) / 2, 0, (p.frame_h + p.post_top) / 2) * Box(
            p.post_t, p.post_w, p.post_top - p.frame_h)
        body = body + post
    for th in p.compartment_angles:
        body = body - lipped_cavity(p, p.divider_half, th, p.frame_h)
    for side in (1, -1):
        x0, x1 = sorted((side * (xi - 1), side * (xo + 1)))
        body = body - teardrop_x(p, x0, x1)
    return body


def handle(p: Params, angle: float = 0.0) -> Part:
    """Handle in assembled position. angle 0 = folded down over +Y half; 90 = upright."""
    r0, r1, z, t = p.handle_r - p.handle_w / 2, p.handle_r + p.handle_w / 2, p.hinge_z, p.handle_t
    band = (Cylinder(r1, t) - Cylinder(r0, t)) - Pos(0, -r1, 0) * Box(2 * r1 + 2, 2 * r1, t + 2)
    band = Pos(0, 0, z) * band
    xi, _ = p.post_x
    pin_x0 = xi + 1.0  # pin tip stays 1 mm inside the post's inner face
    for side in (1, -1):
        cap = Pos(side * p.handle_r, 0, z) * Cylinder(t / 2, p.handle_w, rotation=(0, 90, 0))
        lo, hi = sorted((side * pin_x0, side * r0))
        pin = Pos((lo + hi) / 2, 0, z) * Cylinder(p.pin_r, hi - lo, rotation=(0, 90, 0))
        band = band + cap + pin
    if angle:
        band = band.rotate(Axis((0, 0, z), (1, 0, 0)), angle)
    return band


def tray_bodies(p: Params = P, extension: float = 0.0):
    """Frame + all rings. extension in [0, 1]: 0 = collapsed (print state), 1 = fully extended
    with the floors on the table (z = 0) and the frame lifted by n_rings * travel."""
    n, dz = p.n_rings, p.travel * extension
    bodies = {"frame": frame(p).moved(Location((0, 0, n * dz)))}
    for th in p.compartment_angles:
        for k in range(1, n + 1):
            bodies[f"c{int(th)}_r{k:02d}"] = ring(p, k, th).moved(Location((0, 0, (n - k) * dz)))
    return bodies
