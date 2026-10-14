"""Parametric new parts (build123d), modelled in the LEFT housing frame at their assembled position.

-Y = forward, +Z = up, +X = outboard. Right-hand parts = mirror in X + RH_SHIFT_X (see build_parts.py).
"""
import sys
from pathlib import Path
import math

from build123d import (Box, Cylinder, Sphere, Cone, Pos, Rot, Plane, BuildSketch, BuildPart, Circle,
                       Rectangle, SlotCenterToCenter, Locations, extrude, Mode, Part, Compound, import_step,
                       Polygon, Axis, fillet, Location)

sys.path.insert(0, str(Path(__file__).parent))
import params as P
import geom as G

INPUT = Path(__file__).parent / "input"


# ------------------------------------------------------------------ helpers
def cyl_y(r, y0, y1, x, z):
    """Cylinder along Y between y0 and y1 (any order) with axis through (x, z)."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, abs(y1 - y0))


def cyl_z(r, z0, z1, x, y):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, abs(z1 - z0))


def cyl_x(r, x0, x1, y, z):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, abs(x1 - x0))


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def plane_at_y(y):
    """Sketch plane: local (x, y) = global (X, Z); extrude(+t) grows toward -Y (forward)."""
    return Plane.XZ.offset(-y)


def slot(p0, p1, width):
    (x0, z0), (x1, z1) = p0, p1
    d = math.hypot(x1 - x0, z1 - z0)
    ang = math.degrees(math.atan2(z1 - z0, x1 - x0))
    return Pos((x0 + x1) / 2, (z0 + z1) / 2) * Rot(0, 0, ang) * SlotCenterToCenter(max(d, 0.01), width)


# ------------------------------------------------------------------ projector carrier (aiming frame)
def _follower_holder(q, ym):
    """45° holder that carries the Ø8 steel follower ball FOLLOWER_OFFSET behind the carrier.
    Its cut face is parallel to the wedge ramp, 3 mm off it, so the wedge can never touch the holder."""
    w = G.wedge_geom(); s = w["s"]; r = w["r"]
    bx, bz = q; by = w["ball_y"]
    n = (0.0, s, -s)                                           # contact normal, ball -> ramp
    blk = box(bx - 5.5, bx + 5.5, ym - 1.0, by + 6.0, bz - 6.0, bz + 7.0)
    c0 = (bx, by + n[1] * (r - 3.0), bz + n[2] * (r - 3.0))
    half = Pos(*c0) * Rot(-135, 0, 0) * Pos(0, 0, 50) * Box(100, 100, 100)
    blk = blk - half
    pocket = Pos(bx, by - n[1] * 0.5, bz - n[2] * 0.5) * Rot(-135, 0, 0) * Cylinder(P.FOLLOWER_BALL_D / 2 - 0.025, 7.0)
    return blk, pocket


def projector_carrier():
    cx, cz = P.PROJ_C
    f = G.projector_frame(); a = G.aim_points(); ym = f["y_mount"]; t = P.CARRIER_T
    Pp, Ap, Bp = [(a[k][0], a[k][2]) for k in "PAB"]
    sk = (Pos(cx, cz) * Circle(50.0) + slot(Pp, (Ap[0], Ap[1] + 3), 18.0) + slot((cx, cz), Pp, 18.0)
          + slot((cx, cz), Ap, 16.0) + slot((cx, cz), Bp, 18.0) + Pos(*Bp) * Circle(11.0))
    c = extrude(plane_at_y(ym) * sk, amount=t)
    # projector mounting: 3 x M5 heat-set inserts from the rear, front bosses for insert length
    for ang in P.PROJ_MOUNT_ANGLES:
        x = cx + P.PROJ_MOUNT_PCD / 2 * math.cos(math.radians(ang))
        z = cz + P.PROJ_MOUNT_PCD / 2 * math.sin(math.radians(ang))
        c = c + cyl_y(5.5, ym - t + 0.5, ym - t - 3.0, x, z)
        c = c - cyl_y(P.HSI["M5"] / 2, ym + 1, ym - P.HSI_DEPTH["M5"] - 0.5, x, z)
    # P: spherical socket, closed toward the front (preload bears on the monolithic cup)
    ycen = ym - t / 2
    c = c + cyl_y(12.0, ycen - 7.5, ycen + 5.5, Pp[0], Pp[1])
    c = c - (Pos(Pp[0], ycen, Pp[1]) * Sphere(P.PIVOT_BALL_D / 2 + 0.1))
    c = c - cyl_y(P.PIVOT_BALL_D / 2 + 0.1, ycen, ycen + 6, Pp[0], Pp[1])             # rear insertion
    for dz in (-8.5, 8.5):                                                            # cap screws M3
        c = c - cyl_y(P.HSI["M3"] / 2, ycen + 5.6, ycen + 5.5 - P.HSI_DEPTH["M3"], Pp[0], Pp[1] + dz)
    # A / B: follower-ball holders
    for q in (Ap, Bp):
        blk, pocket = _follower_holder(q, ym)
        c = c + blk - pocket
    # spring seats: Ø4 x 8 spigots on the FRONT face in line with A and B (compression springs to fascia)
    for q in (Ap, Bp):
        c = c + cyl_y(2.0, ym - t + 0.5, ym - t - 8.0, *q)
    c = c - cyl_y(P.PROJ_SHROUD_D / 2 + 0.5, ym + 1, ym - t - 5, cx, cz)            # shroud bore (last)
    return c


def pivot_cap():
    """Rear retainer that closes the P socket around the DIN 71803 ball stud neck."""
    a = G.aim_points(); ym = G.projector_frame()["y_mount"]; Pp = (a["P"][0], a["P"][2])
    ycen = ym - P.CARRIER_T / 2
    y0, y1 = ycen + 5.5, ycen + 8.5
    c = box(Pp[0] - 6.5, Pp[0] + 6.5, y0, y1, Pp[1] - 12, Pp[1] + 12)
    c = c - (Pos(Pp[0], ycen, Pp[1]) * Sphere(P.PIVOT_BALL_D / 2 + 0.1))
    c = c - cyl_y(3.9, y0 - 1, y1 + 1, *Pp)            # neck clearance: ±8° about the ball centre
    for dz in (-8.5, 8.5):
        c = c - cyl_y(P.CLEAR["M3"] / 2, y0 - 1, y1 + 1, Pp[0], Pp[1] + dz)
    return c


# ------------------------------------------------------------------ wedge (A and B)
def wedge(which):
    """45° wedge riding vertically on the adjuster screw; its front ramp pushes the follower ball.
    The ramp is thinner at the top: wedge RAISED (screw tightened) -> ball pushed forward; wedge lowered ->
    the preload springs push the carrier rearward. The ball load pushes the wedge rearward + DOWN, so the
    screw always hangs in tension from its head, which stays seated on the housing top plate."""
    from build123d import RegularPolygon
    a = G.aim_points(); w = G.wedge_geom()
    x = a[which][0]; cz = a[which][2] + w["dz"]; cy = w["cy"]; h = w["ramp_half"]
    yf, yb = w["y_front"], w["y_back"]
    z0, z1 = cz - w["below"], cz + w["above"]
    prof = [(yb, z0), (yb, z1), (cy + (z1 - cz), z1), (cy - h, cz - h), (cy - h, z0)]   # ramp runs out at the top
    wd = extrude(Plane.YZ.offset(x - P.WEDGE_W / 2) * Polygon(*prof, align=None), amount=P.WEDGE_W)
    wd = wd + box(x - 8.0, x + 8.0, cy + 9.5, yb, z0, z1)                        # T-block: guided part
    wd = wd - cyl_z(2.5, z0 - 1, z1 + 1, x, w["screw_y"])                         # Ø5.0 screw passage
    hexr = 8.0 / math.sqrt(3) + 0.15                                               # ISO 10511 M5, 8 AF x 5
    nut = extrude(Plane.XY.offset(z0 - 0.5) * (Pos(x, w["screw_y"]) * RegularPolygon(hexr, 6)), amount=6.0)
    return wd - nut


# ------------------------------------------------------------------ inboard bracket: pivot P + wedge A
WALL = 3.5      # channel side-wall thickness


def _channel(x, z0, z1):
    """Wedge guide: (walls, cavity). Front zone (cy+4.5..cy+9.5) is ±7.0 wide so the follower holder can
    enter it with its ±1.1 mm yaw swing; the rear zone guides the wedge's T-block at ±8.3."""
    w = G.wedge_geom(); cy = w["cy"]
    yw0, yt = cy + 4.5, cy + 9.5
    TW = 8.0
    walls = box(x - TW - 0.3 - WALL, x + TW + 0.3 + WALL, yw0, w["y_back"] + 5.0, z0, z1)
    cav = (box(x - 7.0, x + 7.0, yw0 - 40, yt + 0.01, z0 + 0.01, z1 + 1)
           + box(x - TW - 0.3, x + TW + 0.3, yt, w["y_back"] + 0.3, z0 + 0.01, z1 + 1))
    return walls, cav


def _insert_bosses(keys, z_face, up=True, d=12.0, h=11.0):
    """Bosses carrying M5 heat-set inserts on a bracket face that sits on a housing pad."""
    mt = G.mounts(); add = None; cut = None
    for k in keys:
        x, y, _ = mt[k]
        z0, z1 = (z_face, z_face + h) if up else (z_face - h, z_face)
        b = cyl_z(d / 2, z0, z1, x, y)
        hz = (z_face - 0.1, z_face + P.HSI_DEPTH["M5"] + 0.5) if up else (z_face - P.HSI_DEPTH["M5"] - 0.5, z_face + 0.1)
        hcut = cyl_z(P.HSI["M5"] / 2, *hz, x, y)
        add = b if add is None else add + b
        cut = hcut if cut is None else cut + hcut
    return add, cut


def inboard_bracket():
    a = G.aim_points(); adj = G.adjusters(); ym = G.projector_frame()["y_mount"]; w = G.wedge_geom()
    Pp = a["P"]; Ap = a["A"]; xa, ya = adj["A"]
    z_floor = G.BOSS_TOP_Z_BOTTOM; z_top = P.TOP_PLATE_UNDERSIDE_FRONT - 1.0
    x0, x1 = -163.0, Pp[0] + 12.0                  # x1 stays clear of the projector removal path
    ycen = ym - P.CARRIER_T / 2
    yw0 = ycen + P.STUD_SEAT_OFFSET; yw1 = yw0 + 8.0  # stud wall: front face = ball-stud seat
    base = box(x0, x1, yw0, ym + 37.0, z_floor, z_floor + 5.0)
    wall = box(x0, x1, yw0, yw1, z_floor, Pp[2] + 14.0)
    spine = box(x0, x0 + 7.0, yw0, ym + 37.0, z_floor, z_top)
    zc = Ap[2] + w["dz"]
    walls, cav = _channel(xa, zc - w["below"] - 7.0, z_top)
    arm = box(x0, xa, w["y_back"], w["y_back"] + 5.0, Pp[2] + 14.0, z_top)
    gusset = box(x0, x1, yw1, ym + 37.0, z_floor, z_floor + 18.0) - box(x0 + 7, x1 + 1, yw1 + 4, ym + 33.0, z_floor + 5, z_floor + 19)
    add, cut = _insert_bosses(("inb_bot_1", "inb_bot_2", "inb_bot_3"), z_floor)
    b = base + wall + spine + walls + arm + gusset + add
    b = b - cav - cut
    b = b - cyl_y(P.HSI["M6"] / 2, yw0 - 0.1, yw0 + P.HSI_DEPTH["M6"], Pp[0], Pp[2])    # ball stud M6 insert
    # adjuster-A head seat: the original top plate ends (diagonal rear edge, Y≈-51 at this X) just in
    # front of the screw, so the bracket carries the head on a tower flush with the housing top surface.
    z_seat = G.SEAT_Z
    tower = box(xa - 8.5, xa + 8.5, ya - 9.0, ya + 8.5, z_top - 6.0, z_seat)
    # front face kept 0.6 mm behind the plate's diagonal rear edge [CAD: Y = -50.75 + 0.5 (X + 154)]
    edge = Pos(xa, -50.75 + 0.5 * (xa + 154.0) + 0.6, 240.0) * Rot(0, 0, math.degrees(math.atan(0.5))) * Pos(0, -50, 0) * Box(200, 100, 100)
    tower = tower - edge
    tower = tower - cyl_z(P.CLEAR["M5"] / 2 + 0.25, z_top - 10, z_seat + 1, xa, ya)
    b = b + tower
    return b


def outboard_pillar():
    a = G.aim_points(); adj = G.adjusters(); ym = G.projector_frame()["y_mount"]; w = G.wedge_geom()
    Bp = a["B"]; xb, yb = adj["B"]
    z_floor = G.BOSS_TOP_Z_BOTTOM; z_top = G.BOSS_BOT_Z_TOP
    zc = Bp[2] + w["dz"]
    xi, xo = xb - 8.3 - WALL, xb + 20.0
    base = box(xi, xo, ym + 6.0, ym + 48.0, z_floor, z_floor + 5.0)
    walls, cav = _channel(xb, z_floor, z_top)                          # full-height U column
    top = box(xi, xo, w["cy"] + 4.5, w["y_back"] + 5.0, z_top - 5.0, z_top)
    rib = box(xb + 8.3, xo, w["y_back"], w["y_back"] + 5.0, z_floor, z_top)
    add1, cut1 = _insert_bosses(("out_bot_1", "out_bot_2"), z_floor)
    add2, cut2 = _insert_bosses(("out_top_1",), z_top, up=False)
    b = base + walls + top + rib + add1 + add2
    b = b - cav - cut1 - cut2
    b = b - cyl_z(P.CLEAR["M5"] / 2 + 0.25, zc, z_top + 1, xb, yb)    # long adjuster screw guide
    return b


# ------------------------------------------------------------------ Devil Eye adapter (from the ORIGINAL ring)
def devil_adapter():
    """Original 'hållare ljus 90' ring, moved onto its bosses, re-bored for the Devil Eye module and
    thickened rearward so the lens obeys the same 'just recessed' rule as the projector."""
    d = G.devil_frame(); cx, cz = P.DEVIL_C
    orig = import_step(str(INPUT / "lightring90_L_orig.step"))
    sx, sy, sz = P.LIGHTRING_SHIFT
    ring = Pos(sx, sy, sz) * orig
    ring = Part(ring.wrapped) if not isinstance(ring, Part) else ring
    yf, yr = d["ring_front"], d["ring_rear"]
    ring = ring + cyl_y(105.5 / 2, P.LIGHTRING_Y[0], P.LIGHTRING_Y[1], cx, cz)      # fill old 90 mm bore
    if yr > P.LIGHTRING_Y[1]:
        ext = cyl_y(52.0, P.LIGHTRING_Y[1] - 0.5, yr, cx, cz)
        ring = ring + ext
    ring = ring - cyl_y(P.DEVIL_LENS_D / 2 + 0.5, yf - 1, yr + 1, cx, cz)
    ring = ring - cyl_y(P.DEVIL_FLANGE_D / 2 + 0.3, d["y_flange"], yr + 1, cx, cz)
    for (hx, hz) in P.LIGHTRING_HOLES:                                              # keep original Ø7 holes
        ring = ring - cyl_y(3.5, yf - 1, yr + 1, hx, hz)
    for ang in (30.0, 150.0, 270.0):                                                # clamp ring inserts M4
        x = cx + (P.DEVIL_FLANGE_D / 2 + 6.0) * math.cos(math.radians(ang))
        z = cz + (P.DEVIL_FLANGE_D / 2 + 6.0) * math.sin(math.radians(ang))
        ring = ring - cyl_y(P.HSI["M4"] / 2, yr + 0.1, yr - P.HSI_DEPTH["M4"] - 0.5, x, z)
    return ring


def devil_clamp():
    d = G.devil_frame(); cx, cz = P.DEVIL_C; yr = d["ring_rear"]
    c = cyl_y(P.DEVIL_FLANGE_D / 2 + 11.0, yr, yr + 3.0, cx, cz) - cyl_y(P.DEVIL_BODY_D / 2 + 1.0, yr - 1, yr + 4, cx, cz)
    for ang in (30.0, 150.0, 270.0):
        x = cx + (P.DEVIL_FLANGE_D / 2 + 6.0) * math.cos(math.radians(ang))
        z = cz + (P.DEVIL_FLANGE_D / 2 + 6.0) * math.sin(math.radians(ang))
        c = c - cyl_y(P.CLEAR["M4"] / 2, yr - 1, yr + 4, x, z)
    return c


# ------------------------------------------------------------------ placeholder module envelopes (ASSUMED)
def slot_solid(cx, cz, x, z, ym):
    return extrude(plane_at_y(ym + 4) * slot((cx, cz), (x, z), 14.0), amount=-4)

def ph_projector():
    cx, cz = P.PROJ_C; f = G.projector_frame(); y0, ym = f["y_front"], f["y_mount"]
    shroud = cyl_y(P.PROJ_SHROUD_D / 2, y0, ym, cx, cz)
    flange = cyl_y(P.PROJ_SHROUD_D / 2 + 3, ym, ym + 4, cx, cz)
    for ang in P.PROJ_MOUNT_ANGLES:
        x = cx + P.PROJ_MOUNT_PCD / 2 * math.cos(math.radians(ang)); z = cz + P.PROJ_MOUNT_PCD / 2 * math.sin(math.radians(ang))
        flange = flange + cyl_y(7.0, ym, ym + 4, x, z) + slot_solid(cx, cz, x, z, ym)
    body = box(cx - P.PROJ_BODY_W / 2, cx + P.PROJ_BODY_W / 2, ym + 4, ym + P.PROJ_BODY_L,
               cz - P.PROJ_BODY_H / 2, cz + P.PROJ_BODY_H / 2)
    y1 = ym + P.PROJ_BODY_L
    sink = box(cx - P.PROJ_SINK_W / 2, cx + P.PROJ_SINK_W / 2, y1, y1 + P.PROJ_SINK_L,
               cz - P.PROJ_SINK_H / 2, cz + P.PROJ_SINK_H / 2)
    return shroud + flange + body + sink


def ph_projector_lens():
    cx, cz = P.PROJ_C; y0 = G.projector_frame()["y_front"]
    return cyl_y(P.PROJ_SHROUD_D / 2 - 6, y0 - 0.5, y0 + 6, cx, cz)


def ph_devil():
    cx, cz = P.DEVIL_C; d = G.devil_frame()
    lens = cyl_y(P.DEVIL_LENS_D / 2, d["y_front"], d["y_flange"], cx, cz)
    flange = cyl_y(P.DEVIL_FLANGE_D / 2, d["y_flange"], d["y_flange"] + P.DEVIL_FLANGE_T, cx, cz)
    body = cyl_y(P.DEVIL_BODY_D / 2, d["y_flange"] + P.DEVIL_FLANGE_T, d["y_flange"] + P.DEVIL_FLANGE_T + P.DEVIL_BODY_L, cx, cz)
    return lens + flange + body


# ------------------------------------------------------------------ purchased hardware (visual + interference only)
def hardware():
    a = G.aim_points(); adj = G.adjusters(); w = G.wedge_geom(); ym = G.projector_frame()["y_mount"]
    hw = {}
    for k, L in (("A", 50.0), ("B", 100.0)):                         # ISO 4762 M5 x L, A2
        x, y = adj[k]
        hw[f"HW_screw_M5x{int(L)}_{k}"] = (cyl_z(4.25, G.SEAT_Z + 1.0, G.SEAT_Z + 6.0, x, y)
                                          + cyl_z(5.0, G.SEAT_Z, G.SEAT_Z + 1.0, x, y)       # washer
                                          + cyl_z(2.5, G.SEAT_Z - L + 1.0, G.SEAT_Z + 1.0, x, y))
        bx, bz = a[k][0], a[k][2]
        hw[f"HW_ball_8_{k}"] = Pos(bx, w["ball_y"], bz) * Sphere(P.FOLLOWER_BALL_D / 2)
        sp = P.PRELOAD_SPRING; y1 = ym - P.CARRIER_T; y0 = y1 - sp["l_installed"]
        hw[f"HW_spring_{k}"] = cyl_y(sp["od"] / 2, y0, y1, bx, bz) - cyl_y(sp["od"] / 2 - 0.8, y0 - 1, y1 + 1, bx, bz)
    Pp = a["P"]; ycen = ym - P.CARRIER_T / 2
    hw["HW_ballstud_DIN71803_10"] = (Pos(Pp[0], ycen, Pp[2]) * Sphere(P.PIVOT_BALL_D / 2)
                                     + cyl_y(3.5, ycen, ycen + P.STUD_SEAT_OFFSET, Pp[0], Pp[2])
                                     + cyl_y(3.0, ycen + P.STUD_SEAT_OFFSET, ycen + P.STUD_SEAT_OFFSET + 10, Pp[0], Pp[2]))
    return hw
