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
    tray_d: float = 264.0        # diameter of the frame flange (handle ring sits outside it)
    flange_w: float = 12.0       # flat rim between compartments and handle ring
    divider_half: float = 2.0    # half width of each Mercedes divider rib (rib = 4 mm)
    wall: float = 1.2            # ring wall: 3 lines of a 0.4 mm nozzle
    clear: float = 0.4           # print-in-place gap between neighbouring rings
    lip: float = 1.6             # stop-lip radial protrusion
    lip_flat: float = 0.6        # vertical land under/over each lip's 45° chamfer
    ring_h: float = 7.0          # height of every telescoping ring
    frame_h: float = 10.0        # height of flange, dividers and handle ring (collapsed height)
    floor_t: float = 1.2         # compartment floor thickness
    floor_inradius_min: float = 12.0  # smallest allowed floor (largest inscribed circle)
    # handle: outer ring, printed in place, hinged on the flange; its legs lift the frame
    handle_gap: float = 0.5      # print-in-place gap handle ring <-> flange
    handle_w: float = 10.0       # radial width of the handle ring
    leg_deg: float = 28.93       # leg length past the hinge: lift at the stop = n_rings * travel - 0.05
    leg_gap_deg: float = 1.5     # angular gap leg end <-> fixed outer ring segment
    pin_r: float = 2.0           # hinge pin (upper half round, lower half 45° V)
    pin_clear: float = 0.4       # radial clearance pin <-> hole
    pin_len: float = 5.0         # pin length into the flange
    stop_deg: float = 100.0      # handle angle at the base-pocket stop (over-centre lock)
    # base plate (separate print)
    base_d: float = 290.0
    base_t: float = 6.0
    pocket_d: float = 4.0        # depth of the two foot pockets
    pocket_x: tuple = (117.15, 127.18)  # pocket floor x range (+X side, mirrored) = solve_pocket()
    pocket_y: tuple = (-17.19, 17.19)   # pocket floor y range; y[1] is the vertical stop wall
    # twist lock: 3 mushroom posts on the base, keyhole slots in the 3 floors
    twist_lock: bool = True
    lock_deg: float = 7.0        # turn the tray this far (counter-clockwise seen from above) to unlock
    post_neck_r: float = 2.2
    post_head_r: float = 4.0
    post_head_t: float = 1.0     # cylindrical part of the head, above its 45° underside
    lock_clear: float = 0.4
    lock_play: float = 1.0       # head underside above the floor: absorbs the ~1 mm over-lift near 70°
    decor: bool = True           # engraved tomoe swirls, border lines, edge teeth (see _decor.py)
    compartment_angles: tuple = field(default=(30.0, 150.0, 270.0))
    with_handle: bool = True     # False for the small test coupon

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
    def r_flange(self):
        return self.tray_d / 2

    @property
    def handle_r0(self):
        return self.r_flange + self.handle_gap

    @property
    def handle_r1(self):
        return self.handle_r0 + self.handle_w

    @property
    def hinge_z(self):
        return self.frame_h / 2

    @property
    def hole_r(self):
        return self.pin_r + self.pin_clear

    @property
    def lock_c(self):
        """Distance of the posts from the centre: the floors' in-circle centres."""
        return self.sector_inradius / sin(radians(60))

    @property
    def lift(self):
        """Frame lift that extends every ring with the floors resting on the base."""
        return self.n_rings * self.travel


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
        if p.twist_lock:
            cavity = cavity + keyhole(p, th)
    body = envelope - cavity
    if p.decor:
        from _decor import rings_tool
        body = body - rings_tool(p)
    return body


def polar(r, a, z=0.0):
    return (r * cos(radians(a)), r * sin(radians(a)), z)


def keyhole(p: Params, th: float) -> Part:
    """Through-slot in the floor: round entry for the post head at th - lock_deg/2, then an arc
    slot (about the tray centre) for the neck up to th + lock_deg/2, where the post sits locked."""
    c, b, z0, hgt = p.lock_c, p.lock_deg / 2, -1.0, p.floor_t + 2.0
    w = p.post_neck_r + p.lock_clear
    tool = Pos(*polar(c, th - b, z0)) * Cylinder(p.post_head_r + p.lock_clear, hgt, align=None)
    tool = tool + annulus_sector(c - w, c + w, th - b, th + b, z0, hgt)
    for a in (th - b, th + b):
        tool = tool + Pos(*polar(c, a, z0)) * Cylinder(w, hgt, align=None)
    return tool


def lock_post(p: Params, th: float) -> Part:
    """Mushroom post on the base top (z = 0) at the locked position th + lock_deg/2."""
    x, y, _ = polar(p.lock_c, th + p.lock_deg / 2)
    z1 = p.floor_t + p.lock_play               # underside of the head above the floor
    z2 = z1 + (p.post_head_r - p.post_neck_r)  # 45° underside
    neck = Pos(x, y, -0.5) * Cylinder(p.post_neck_r, z1 + 0.5, align=None)
    cone = loft([Face(Wire.make_circle(p.post_neck_r).moved(Location((x, y, z1)))),
                 Face(Wire.make_circle(p.post_head_r).moved(Location((x, y, z2))))], ruled=True)
    head = Pos(x, y, z2) * Cylinder(p.post_head_r, p.post_head_t, align=None)
    return neck + cone + head


def annulus_sector(r0, r1, a0, a1, z0, h) -> Part:
    """Flat ring segment r0..r1 between polar angles a0..a1 (deg, counter-clockwise), z0..z0+h."""
    pol = lambda r, a: (r * cos(radians(a)), r * sin(radians(a)), z0)
    am = (a0 + a1) / 2
    face = Face(Wire([Edge.make_three_point_arc(pol(r1, a0), pol(r1, am), pol(r1, a1)),
                      Edge.make_line(pol(r1, a1), pol(r0, a1)),
                      Edge.make_three_point_arc(pol(r0, a1), pol(r0, am), pol(r0, a0)),
                      Edge.make_line(pol(r0, a0), pol(r1, a0))]))
    return extrude(face, h)


def yz_prism(p, profile, x0, x1) -> Part:
    """Prism along X from x0 to x1 of a closed (y, z) profile: list of ('line', a, b) / ('arc', a, m, b)."""
    edges = []
    for seg in profile:
        pts = [(x0, y, z) for y, z in seg[1:]]
        edges.append(Edge.make_line(*pts) if seg[0] == "line" else Edge.make_three_point_arc(*pts))
    return extrude(Face(Wire(edges)), x1 - x0, dir=(1, 0, 0))


def pin_profile(p):
    """Upper half round, lower half a 45° V (prints without support, turns freely in a round hole)."""
    r, z = p.pin_r, p.hinge_z
    return [("arc", (r, z), (0, z + r), (-r, z)), ("line", (-r, z), (0, z - r)), ("line", (0, z - r), (r, z))]


def hole_profile(p):
    """Round hole with a 45° teardrop roof."""
    r, z = p.hole_r, p.hinge_z
    q = r / sqrt(2)
    return [("arc", (q, z + q), (0, z - r), (-q, z + q)), ("line", (-q, z + q), (0, z + r * sqrt(2))),
            ("line", (0, z + r * sqrt(2)), (q, z + q))]


def frame(p: Params) -> Part:
    body = Cylinder(p.r_flange, p.frame_h, align=None)  # base on z = 0
    if p.with_handle:
        g = p.leg_deg + p.leg_gap_deg  # fixed outer-ring segment between the two leg ends
        body = body + annulus_sector(p.r_flange - 1.0, p.handle_r1, 180 + g, 360 - g, 0, p.frame_h)
    for th in p.compartment_angles:
        body = body - lipped_cavity(p, p.divider_half, th, p.frame_h)
    if p.with_handle:
        for side in (1, -1):
            x0, x1 = sorted((side * (p.r_flange - p.pin_len - 1.0), side * (p.r_flange + 0.1)))
            body = body - yz_prism(p, hole_profile(p), x0, x1)
    if p.decor:
        from _decor import frame_tool
        body = body - frame_tool(p)
    return body


def handle(p: Params, angle: float = 0.0) -> Part:
    """Handle ring + legs + hinge pins in frame coordinates. angle 0 = flat in the flange plane
    (print state); 90 = upright; p.stop_deg = open and locked over centre."""
    body = annulus_sector(p.handle_r0, p.handle_r1, -p.leg_deg, 180 + p.leg_deg, 0, p.frame_h)
    for side in (1, -1):
        x0, x1 = sorted((side * (p.r_flange - p.pin_len), side * (p.handle_r0 + 0.5)))
        body = body + yz_prism(p, pin_profile(p), x0, x1)
    if p.decor:
        from _decor import handle_tool
        body = body - handle_tool(p)
    if angle:
        body = body.rotate(Axis((0, 0, p.hinge_z), (1, 0, 0)), angle)
    return body


# ---------------------------------------------------------------- kinematics
def leg_points(p: Params, step: float = 0.1):
    """Dense samples of the +X leg's end region (all its faces), collapsed pose, frame coords."""
    import numpy as np
    r0, r1, h, phi = p.handle_r0, p.handle_r1, p.frame_h, p.leg_deg
    rs, zs = np.arange(r0, r1 + 1e-9, step), np.arange(0, h + 1e-9, step)
    ths = np.radians(-phi + np.arange(0, 4.0, step / r1 * 57.3))
    pts = []
    R, Z = np.meshgrid(rs, zs)                       # end face
    pts.append(np.c_[R.ravel() * cos(radians(-phi)), R.ravel() * sin(radians(-phi)), Z.ravel()])
    for r in (r0, r1):                               # inner / outer cylinder
        T, Z = np.meshgrid(ths, zs)
        pts.append(np.c_[r * np.cos(T.ravel()), r * np.sin(T.ravel()), Z.ravel()])
    for z in (0.0, h):                               # bottom / top face
        R, T = np.meshgrid(rs, ths)
        pts.append(np.c_[R.ravel() * np.cos(T.ravel()), R.ravel() * np.sin(T.ravel()), np.full(R.size, z)])
    return np.vstack(pts)


def rotate_x(pts, angle, zp):
    import numpy as np
    a = radians(angle)
    y, z = pts[:, 1], pts[:, 2] - zp
    return np.c_[pts[:, 0], y * np.cos(a) - z * np.sin(a), y * np.sin(a) + z * np.cos(a) + zp]


def base_height(p: Params, x, y):
    """Base top surface height (0 = flat top) under points x, y: pockets with 45° side and
    entry ramps, vertical stop wall at pocket_y[1]."""
    import numpy as np
    ax = np.abs(x)
    (x0, x1), (y0, y1), d = p.pocket_x, p.pocket_y, p.pocket_d
    depth_x = np.clip(np.minimum(ax - (x0 - d), (x1 + d) - ax), 0, d)
    depth_y = np.clip(y - (y0 - d), 0, d)
    depth = np.minimum(depth_x, depth_y)
    depth[y > y1] = 0.0
    return -depth


_LEG = {}


def frame_lift(p: Params, angle: float, on_base: bool = True) -> float:
    """Frame lift above the base top for a handle angle: the legs rest on the base surface."""
    if p not in _LEG:
        _LEG[p] = leg_points(p)
    pts = rotate_x(_LEG[p], angle, p.hinge_z)
    ground = base_height(p, pts[:, 0], pts[:, 1]) if on_base else 0.0 * pts[:, 0]
    return max(0.0, float((ground - pts[:, 2]).max()))


def solve_pocket(p: Params, clearance: float = 0.3):
    """Pocket that holds the foot from where it starts to drop in up to the stop angle."""
    import numpy as np
    pts = leg_points(p)
    feet = []
    for a in np.arange(80.0, p.stop_deg + 1e-9, 0.5):
        q = rotate_x(pts, a, p.hinge_z)
        low = q[q[:, 2] <= q[:, 2].min() + p.pocket_d]
        feet.append(low)
    f = np.vstack(feet)
    stop = feet[-1]
    r = lambda v: round(float(v), 2)  # noqa: E731
    return ((r(f[:, 0].min() - clearance), r(f[:, 0].max() + clearance)),
            (r(f[:, 1].min() - clearance), r(stop[:, 1].max() + clearance)))


def base(p: Params) -> Part:
    """Base plate, top face at z = 0. Two pockets catch the handle's feet; each pocket's +Y wall
    is vertical and is the over-centre stop at p.stop_deg. Other pocket walls are 45° ramps."""
    body = Cylinder(p.base_d / 2, p.base_t, align=None).moved(Location((0, 0, -p.base_t)))
    (x0, x1), (y0, y1), d = p.pocket_x, p.pocket_y, p.pocket_d
    for side in (1, -1):
        top = Face(Wire.make_polygon([(side * (x0 - d), y0 - d, 0), (side * (x1 + d), y0 - d, 0),
                                      (side * (x1 + d), y1, 0), (side * (x0 - d), y1, 0)], close=True))
        bot = Face(Wire.make_polygon([(side * x0, y0, -d), (side * x1, y0, -d),
                                      (side * x1, y1, -d), (side * x0, y1, -d)], close=True))
        body = body - loft([bot, top], ruled=True)
    if p.twist_lock:
        for th in p.compartment_angles:
            body = body + lock_post(p, th)
    if p.decor:
        from _decor import base_tool
        body = body - base_tool(p)
    return body


def tray_bodies(p: Params = P, extension: float = 0.0):
    """Frame + all rings. extension in [0, 1]: 0 = collapsed (print state), 1 = fully extended
    with the floors on the table (z = 0) and the frame lifted by n_rings * travel."""
    n, dz = p.n_rings, p.travel * extension
    bodies = {"frame": frame(p).moved(Location((0, 0, n * dz)))}
    for th in p.compartment_angles:
        for k in range(1, n + 1):
            bodies[f"c{int(th)}_r{k:02d}"] = ring(p, k, th).moved(Location((0, 0, (n - k) * dz)))
    return bodies


def assembly(p: Params = P, angle: float = 0.0, with_base: bool = True):
    """Every body placed for a handle angle, physically: the legs push the frame up by
    frame_lift(angle); ring k leaves the base once the frame has risen k * travel."""
    lift = frame_lift(p, angle) if p.with_handle else 0.0
    bodies = {"frame": frame(p).moved(Location((0, 0, lift)))}
    for th in p.compartment_angles:
        for k in range(1, p.n_rings + 1):
            bodies[f"c{int(th)}_r{k:02d}"] = ring(p, k, th).moved(Location((0, 0, max(0.0, lift - k * p.travel))))
    if p.with_handle:
        bodies["handle"] = handle(p, angle).moved(Location((0, 0, lift)))
    if with_base:
        bodies["base"] = base(p)
    return bodies
