"""Workshop key holder shaped like a combination wrench (reconstruction of the owner's reference picture).

Parametric build123d model.  Run:  python cad/wrench_keyholder.py [--out cad/wrench_keyholder/out]
Outputs (STEP + STL per printable component, full assemblies for both brake variants, validation report).

Coordinates: mm, X to the right, Y up (Y=0 is the top line of the connecting bar), Z out of the wall.
Z=0 is the back (wall side).  The reference picture is 2000 px wide; every picture point (px, py) is mapped with
    X = (px - 1000) * SCALE,  Y = (300 - py) * SCALE
so the picture proportions are kept exactly and the overall size is changed with one number (SCALE).
Uncertainty: the picture gives no dimensions.  SCALE=0.32 (about 610 mm long) is an assumption, not a measurement.
"""
import argparse
import math
import sys
from pathlib import Path

from build123d import (Box, Circle, Compound, Cylinder, Kind, Location, Plane, Polygon, Pos, Rectangle,
                       RectangleRounded, Rot, SlotOverall, Solid, Text, ThreePointArc, Line, BuildLine,
                       BuildSketch, Wire, Face, Sketch, export_step, export_stl, extrude, fillet, make_face,
                       offset, Align, Axis, Vector, Mode)

HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------------------------- parameters
PARAMS = dict(
    SCALE=0.32,            # mm per picture pixel  -> overall length 1905 px = 610 mm, height ~155 mm
    BASE_T=8.0,            # main body thickness (black plate), Z 0..BASE_T
    BAND_H=1.4,            # orange perimeter relief above the plate
    BAND_OFF=6.5,          # orange band: distance in from the outline (mm)
    BAND_W=4.2,            # orange band width (mm)
    PANEL_H=3.0,           # workshop wall panel relief
    DETAIL_H=2.2,          # workshop details relief above the panel
    JAW_SLOT_R=75,         # px: rounded end of the open jaw
    RING_OUT_R=195,        # px: ring head outer radius
    RING_HOLE_R=125,       # px: ring hole at the tooth tips' outer edge
    RING_TEETH=14,         # internal teeth of the ring head
    TOOTH_DEPTH=18,        # px
    HOOKS_PX=[600, 820, 1030, 1240, 1465],
    HOOK_W=22,             # px: hook band width (about 7 mm)
    HOOK_T=10.0,           # hook thickness (Z), stands on the plate front
    HOOK_SCREW_D=3.4,      # clearance hole for M3 screws from the back
    BRAKE_C=(1300, 262),   # px: brake centre
    BRAKE_R=82,            # px (the brake geometry is drawn at R=100 and scaled by BRAKE_R/100)
    CUTS_PX=[500, 925, 1530],   # split planes (printable parts: 4)
    CLEAR=0.25,            # mating clearance (mm)
    DOVE_ROOT=10.0, DOVE_TIP=16.0, DOVE_LEN=7.0,
    SPLICE_L=46.0, SPLICE_H=24.0, SPLICE_T=2.4,
    KEY_PX=[(418, 345), (1567, 345)],   # keyhole pockets behind the decorative screws
)
S = PARAMS["SCALE"]
T = PARAMS["BASE_T"]
FONT_BOLD = str(HERE / "fonts" / "NotoSans-Bold.ttf")


def P(x, y):
    return ((x - 1000) * S, (300 - y) * S)


def poly(pts):
    return Polygon(*[P(x, y) for x, y in pts], align=None)


def circ(cx, cy, r):
    return Pos(*P(cx, cy)) * Circle(r * S)


def rect(x0, y0, x1, y1):
    return Pos(*P((x0 + x1) / 2, (y0 + y1) / 2)) * Rectangle(abs(x1 - x0) * S, abs(y1 - y0) * S)


def rrect(x0, y0, x1, y1, r):
    return Pos(*P((x0 + x1) / 2, (y0 + y1) / 2)) * RectangleRounded(abs(x1 - x0) * S, abs(y1 - y0) * S, r * S)


def ext(sk, z0, z1):
    return Pos(0, 0, z0) * extrude(sk, amount=z1 - z0)


def star_poly(cx, cy, r_out, r_in, n, rot=0.0, pts_per=2):
    """Tooth profile polygon (square-ish teeth)."""
    pts = []
    for i in range(n):
        a0 = rot + 2 * math.pi * i / n
        da = 2 * math.pi / n
        for f, r in ((0.0, r_out), (0.26, r_out), (0.30, r_in), (0.70, r_in), (0.74, r_out), (1.0, r_out)):
            if f == 1.0:
                continue
            a = a0 + f * da
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(pts)


# ----------------------------------------------------------------------------------------------- main body
def body_outline():
    """Wrench silhouette 2D (without holes)."""
    head_l = circ(260, 275, 205)
    bar = rect(380, 295, 1620, 405)
    ring = circ(1750, 290, PARAMS["RING_OUT_R"])
    # neck fills so the heads blend into the bar (concave corners are rounded below)
    neck_l = poly([(380, 240), (560, 295), (560, 405), (380, 405)])
    neck_r = poly([(1560, 295), (1700, 215), (1700, 405), (1560, 405)])
    sk = head_l + bar + ring + neck_l + neck_r
    # round the concave blends and the bar ends
    for v in list(sk.vertices()):
        try:
            cand = sk.vertices().filter_by(lambda q: abs(q.X - v.X) < 0.05 and abs(q.Y - v.Y) < 0.05)
            sk = fillet(cand, radius=12 * S)
        except Exception:
            pass
    slot = (poly([(10, 258), (235, 258), (235, 402), (10, 402)]) +
            circ(235, 330, PARAMS["JAW_SLOT_R"]))
    # open end slants like a real open-end wrench (15 degrees)
    slot = Pos(*P(235, 330)) * Rot(0, 0, -12) * Pos(*[-v for v in P(235, 330)]) * slot
    hole = star_poly(1750, 290, PARAMS["RING_HOLE_R"], PARAMS["RING_HOLE_R"] - PARAMS["TOOTH_DEPTH"],
                     PARAMS["RING_TEETH"])
    res = sk - slot - hole
    faces = sorted(res.faces(), key=lambda f: -f.area)
    return Sketch(children=[faces[0]])      # drop the sliver the slanted slot leaves behind


def make_body():
    out = body_outline()
    base = ext(out, 0, T)
    # perimeter band (orange): thin ring inside the outline, not along the bottom of the bar
    ow = out.faces()[0].outer_wire()        # outer boundary only (the ring teeth get no band)
    fa = make_face(ow.offset_2d(-PARAMS["BAND_OFF"]))
    fb = make_face(ow.offset_2d(-(PARAMS["BAND_OFF"] + PARAMS["BAND_W"])))
    band = Sketch(children=[fa]) - Sketch(children=[fb])
    cutter = rect(470, 352, 1570, 520)
    band = band - cutter
    orange = ext(band, T, T + PARAMS["BAND_H"])
    return base, orange, out


def keyholes(base):
    """Keyhole pockets in the back (T-slot): head chamber inside, narrow slot at the back (for an M4 wall screw)."""
    for (px, py) in PARAMS["KEY_PX"]:
        x, y = P(px, py)
        pocket = Pos(x, y, 0) * Cylinder(4.9, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamber = Pos(x, y + 4.5, 2.2) * extrude(SlotOverall(8 + 9.8, 9.8, rotation=90), amount=3.8)
        slot = Pos(x, y + 4.5, 0) * extrude(SlotOverall(8 + 4.6, 4.6, rotation=90), amount=2.3)
        base = base - pocket - chamber - slot
    return base


def screw_heads():
    """Decorative cross screws (black, raised)."""
    out = []
    for px, py in ((418, 322), (1567, 328)):
        x, y = P(px, py)
        head = Pos(x, y, T) * Cylinder(6.2, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        slot1 = Pos(x, y, T + 1.0) * Box(8.2, 1.4, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        slot2 = Pos(x, y, T + 1.0) * Box(1.4, 8.2, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        out.append(head - slot1 - slot2)
    return out


# ----------------------------------------------------------------------------------------------- workshop
def workshop():
    """Returns dict colour -> list of solids."""
    ph, dh = PARAMS["PANEL_H"], PARAMS["DETAIL_H"]
    zp = T                    # panel starts on the plate
    zd = T + ph               # details start on the panel
    c = {"black": [], "white": [], "orange": [], "red": []}

    # wall panel and roof ---------------------------------------------------------------------
    panel = poly([(655, 100), (1030, 8), (1425, 100), (1425, 295), (655, 295)])
    c["black"].append(ext(panel, zp, zd))
    roof_dark = poly([(588, 112), (1030, -14), (1472, 112), (1472, 72), (1030, -50), (588, 72)])  # unused guard
    # roof: grey/white layered border (two slanted bars), a dark eave under it
    roof_out = poly([(595, 104), (1030, -4), (1468, 104), (1468, 132), (1030, 28), (595, 132)])
    c["black"].append(ext(poly([(590, 125), (1030, -12), (1472, 125), (1472, 98), (1030, -34), (590, 98)]) -
                          poly([(590, 125), (1030, -12), (1472, 125), (1472, 98), (1030, -34), (590, 98)]) +
                          poly([(600, 98), (1030, -8), (1462, 98), (1462, 128), (1030, 42), (600, 128)]), zp, zd))
    c["white"].append(ext(roof_out, zd, zd + dh))
    # side pillars
    for x0, x1 in ((655, 676), (1404, 1425)):
        c["white"].append(ext(rect(x0, 100, x1, 290), zd, zd + dh * 0.8))
    # gear emblem + WORKSHOP lettering
    gear = star_poly(1037, 48, 40, 31, 8, rot=0.2) + circ(1037, 48, 31)
    gear = gear - circ(1037, 48, 13)
    c["white"].append(ext(gear, zd, zd + dh))
    tx, ty = P(1037, 104)
    with BuildSketch() as txt:
        Text("WORKSHOP", 15.5, font_path=FONT_BOLD, align=(Align.CENTER, Align.CENTER))
    t_sk = Pos(tx, ty) * txt.sketch
    c["white"].append(ext(t_sk, zd, zd + dh))
    # orange speed stripes beside the lettering
    for i, yy in enumerate((84, 99, 114)):
        dx = i * 12
        c["orange"].append(ext(poly([(765 + dx, yy), (872, yy), (872, yy + 9), (765 + dx + 8, yy + 9)]), zd, zd + dh * 0.7))
        c["orange"].append(ext(poly([(1202, yy), (1308 - dx, yy), (1308 - dx - 8, yy + 9), (1202, yy + 9)]), zd, zd + dh * 0.7))

    # left tool board: 6 hanging spanners ---------------------------------------------------------
    c["black"].append(ext(rect(685, 130, 830, 212), zd, zd + 0.8))
    for i in range(6):
        x = 702 + i * 24
        stem = rect(x - 3.5, 150, x + 3.5, 205)
        head = circ(x, 143, 8) - circ(x, 140, 3.6)
        sp = stem + head
        if i % 2:
            sp = sp + circ(x, 208, 6.5) - circ(x, 208, 2.5)
        c["white"].append(ext(sp, zd + 0.8, zd + 0.8 + dh * 0.8))

    # red tool cabinet ----------------------------------------------------------------------------------
    cab = rect(697, 226, 823, 290)
    grooves = (rect(697, 247, 823, 249.5) + rect(759, 249.5, 761.5, 290) + rect(697, 268, 823, 270.5))
    c["red"].append(ext(cab - grooves, zd, zd + dh * 1.4))
    for x in (722, 735, 785, 798):
        c["white"].append(ext(rect(x - 5, 257, x + 5, 259), zd + dh * 1.4, zd + dh * 1.4 + 0.6))
    c["white"].append(ext(rect(693, 222, 827, 228), zd, zd + dh * 1.5))   # worktop

    # left oil shelf: two shelves with 4 containers -----------------------------------------------
    c["black"].append(ext(rect(525, 120, 655, 268), zp, zd + 0.5))
    for y in (178, 262):
        c["white"].append(ext(rect(545, y, 652, y + 6), zd + 0.5, zd + dh))
    for i, (x0, col) in enumerate(((556, "red"), (601, "red"))):
        c[col].append(ext(can(x0, 128, x0 + 38, 176), zd + 0.5, zd + 0.5 + dh * 1.3))
    for x0 in (556, 601):
        c["orange"].append(ext(can(x0, 208, x0 + 38, 260), zd + 0.5, zd + 0.5 + dh * 1.3))

    # central bay: lift columns, car --------------------------------------------------------------------------
    for x0 in (862, 1170):
        c["orange"].append(ext(rect(x0 + 6, 150, x0 + 30, 282), zd, zd + dh * 1.4))
        c["orange"].append(ext(rect(x0 - 10, 276, x0 + 46, 292), zd, zd + dh * 1.4))
        c["white"].append(ext(rect(x0 + 14, 138, x0 + 22, 160), zd, zd + dh * 1.4))   # piston
    for (a, b) in ((896, 928), (1146, 1176)):
        c["orange"].append(ext(rect(a, 238, b, 250), zd, zd + dh * 1.4))
    car = (rrect(925, 207, 1147, 268, 16) + poly([(952, 207), (975, 160), (1100, 160), (1122, 207)]))
    c["white"].append(ext(car, zd + 0.5, zd + 0.5 + dh * 1.6))
    wind = poly([(962, 204), (980, 168), (1096, 168), (1114, 204)])
    c["black"].append(ext(wind, zd + 0.5 + dh * 1.6, zd + 0.5 + dh * 1.6 + 0.6))
    for hx in (950, 1122):
        c["black"].append(ext(rrect(hx - 14, 213, hx + 14, 227, 4), zd + 0.5 + dh * 1.6, zd + 0.5 + dh * 1.6 + 0.6))
    c["black"].append(ext(rrect(985, 228, 1088, 250, 6), zd + 0.5 + dh * 1.6, zd + 0.5 + dh * 1.6 + 0.6))
    # ceiling light over the bay
    c["white"].append(ext(poly([(1010, 132), (1050, 132), (1062, 146), (998, 146)]) + rect(1028, 120, 1032, 132),
                          zd, zd + dh))
    c["orange"].append(ext(circ(1030, 150, 5), zd, zd + dh))

    # right shelf: frame with small oil filters / bottles -------------------------------------------
    frame = rect(1245, 135, 1385, 182) - rect(1250, 140, 1380, 177)
    c["white"].append(ext(frame, zd, zd + dh))
    c["white"].append(ext(rect(1245, 177, 1385, 183), zd, zd + dh * 1.3))
    for x0, h in ((1256, 26), (1282, 32), (1308, 24), (1335, 30), (1360, 22)):
        c["white"].append(ext(rrect(x0, 177 - h, x0 + 18, 177, 3), zd, zd + dh * 1.1))
    return c


def can(x0, y0, x1, y1):
    body = rrect(x0, y0 + 8, x1, y1, 5)
    spout = rect(x0 + 5, y0, x0 + 15, y0 + 10)
    handle = rect(x0 + 18, y0 + 12, x1 - 5, y0 + 20)
    return body + spout - handle


# ----------------------------------------------------------------------------------------------- hooks
def make_hook(hx):
    """J hook (profile in the wall plane, stem lying on the plate front, J hangs 8 mm off the wall)."""
    w = PARAMS["HOOK_W"]
    with BuildLine() as ln:
        Line(P(hx, 346), P(hx, 440))
        ThreePointArc(P(hx, 440), P(hx + 26, 466), P(hx + 52, 440))
        Line(P(hx + 52, 440), P(hx + 52, 416))
    wire = ln.wire()
    outline = wire.offset_2d(w * S / 2, kind=Kind.ARC)
    face = make_face(outline)
    tip = Pos(*P(hx + 52, 410)) * Circle(w * S * 0.85)
    sk = Sketch(children=[face]) + tip
    solid = ext(sk, T, T + PARAMS["HOOK_T"])
    # two pilot holes for M3 self-tapping screws from the back
    for py in (362, 394):
        x, y = P(hx, py)
        solid = solid - Pos(x, y, T) * Cylinder(1.25, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return solid


def hook_holes(base):
    d = PARAMS["HOOK_SCREW_D"]
    for hx in PARAMS["HOOKS_PX"]:
        for py in (362, 394):
            x, y = P(hx, py)
            base = base - Pos(x, y, 0) * Cylinder(d / 2, T + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
            cs = Solid.make_cone(d / 2 + 1.4, d / 2, 1.5)  # countersink at the back
            cs = Pos(x, y, 0) * cs
            base = base - cs
    return base


# ----------------------------------------------------------------------------------------------- brakes
PEG_R, PEG_DEPTH = 3.0, 5.0          # brake locating peg: dia 6, goes 5 mm into the plate (socket opens at the front)


def brake_peg():
    x, y = P(*PARAMS["BRAKE_C"])
    zd = T + PARAMS["PANEL_H"]
    return Pos(x, y, T - PEG_DEPTH) * Cylinder(PEG_R, zd - (T - PEG_DEPTH) + 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cut_brake_socket(solid):
    x, y = P(*PARAMS["BRAKE_C"])
    return solid - Pos(x, y, T - PEG_DEPTH - 0.5) * Cylinder(PEG_R + PARAMS["CLEAR"], PEG_DEPTH + 0.5 + PARAMS["PANEL_H"] + 1,
                                                          align=(Align.CENTER, Align.CENTER, Align.MIN))


def fit_brake(cols):
    """Scale a brake drawn at R=100 px to BRAKE_R and sit it on top of the wall panel."""
    k = PARAMS["BRAKE_R"] / 100.0
    cx, cy = P(*PARAMS["BRAKE_C"])
    zd = T + PARAMS["PANEL_H"]
    res = {}
    for col, ss in cols.items():
        res[col] = [Pos(cx * (1 - k), cy * (1 - k), zd - k * T) * s.scale(k) for s in ss]
    res.setdefault("black", []).append(brake_peg())
    return res


def brake_disc():
    cx, cy = PARAMS["BRAKE_C"]
    R = PARAMS["BRAKE_R"]
    z0 = T                      # sits on the plate (a round pocket is not needed)
    out = {"white": [], "black": [], "red": []}
    rotor = circ(cx, cy, R) - circ(cx, cy, 36)
    for i in range(18):
        a = 2 * math.pi * i / 18
        rotor = rotor - circ(cx + 80 * math.cos(a), cy + 80 * math.sin(a), 5.5)
        if i % 2 == 0:
            rotor = rotor - circ(cx + 62 * math.cos(a + 0.17), cy + 62 * math.sin(a + 0.17), 4.2)
    out["white"].append(ext(rotor, z0, z0 + 3.0))
    hub = circ(cx, cy, 40) - circ(cx, cy, 12)
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        hub = hub - circ(cx + 26 * math.cos(a), cy + 26 * math.sin(a), 4.2)
    out["black"].append(ext(hub, z0, z0 + 6.0))
    # caliper: arc over the rotor edge (right side) + piston body + bleed nipple
    cal = circ(cx, cy, 116) - circ(cx, cy, 64)
    cut = poly([(cx - 200, cy - 200), (cx + 12, cy - 200), (cx + 12, cy + 200), (cx - 200, cy + 200)])
    keep = Pos(*P(cx, cy)) * Rot(0, 0, 0) * Pos(*[-v for v in P(cx, cy)]) * (
        poly([(cx + 12, cy - 90), (cx + 130, cy - 90), (cx + 130, cy + 70), (cx + 12, cy + 70)]))
    cal = cal & keep
    out["red"].append(ext(cal, z0 + 1.0, z0 + 7.0))
    out["black"].append(ext(rect(cx + 100, cy - 70, cx + 112, cy - 56), z0 + 7.0, z0 + 8.0))  # bleed nipple
    out["red"].append(ext(rect(cx + 60, cy - 18, cx + 80, cy + 18), z0 + 7.0, z0 + 8.2))     # caliper ribs
    return out


def brake_drum():
    cx, cy = PARAMS["BRAKE_C"]
    R = PARAMS["BRAKE_R"]
    z0 = T
    out = {"white": [], "black": [], "red": [], "orange": []}
    plate = circ(cx, cy, R)
    out["black"].append(ext(plate, z0, z0 + 2.0))
    rim = circ(cx, cy, R) - circ(cx, cy, R - 7)
    out["black"].append(ext(rim, z0 + 2.0, z0 + 5.0))
    hub = circ(cx, cy, 30) - circ(cx, cy, 11)
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        hub = hub - circ(cx + 20 * math.cos(a), cy + 20 * math.sin(a), 3.4)
    out["black"].append(ext(hub, z0 + 2.0, z0 + 6.5))
    # two brake shoes (C shaped arcs, left and right)
    ring = circ(cx, cy, 78) - circ(cx, cy, 62)
    for sgn in (1, -1):
        half = poly([(cx + sgn * 6, cy - 90), (cx + sgn * 100, cy - 90), (cx + sgn * 100, cy + 90),
                     (cx + sgn * 6, cy + 90)])
        out["white"].append(ext(ring & half, z0 + 2.0, z0 + 6.0))
        # shoe web (inner rib) from the arc toward the hub
        web = (circ(cx, cy, 64) - circ(cx, cy, 55)) & half
        out["white"].append(ext(web, z0 + 2.0, z0 + 4.5))
    # wheel cylinder (top) and adjuster star wheel (bottom)
    out["red"].append(ext(rrect(cx - 22, cy - 76, cx + 22, cy - 56, 4), z0 + 2.0, z0 + 6.0))
    star = star_poly(cx, cy + 66, 13, 9, 8) - circ(cx, cy + 66, 3.5)
    out["orange"].append(ext(star, z0 + 2.0, z0 + 6.0))
    out["black"].append(ext(rect(cx - 26, cy + 62, cx - 13, cy + 70) + rect(cx + 13, cy + 62, cx + 26, cy + 70),
                            z0 + 2.0, z0 + 5.0))
    # return springs: two zig-zag wires near the top and bottom of the shoes
    for yy, sg in ((cy - 44, 1), (cy + 44, -1)):
        pts = []
        n = 7
        for k in range(n + 1):
            pts.append((cx - 38 + k * 76 / n, yy + (4 if k % 2 else -4)))
        wire = []
        for k in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            wire.append(poly([(x0, y0 - 1.6), (x1, y1 - 1.6), (x1, y1 + 1.6), (x0, y0 + 1.6)]))
        sp = wire[0]
        for w in wire[1:]:
            sp = sp + w
        out["white"].append(ext(sp, z0 + 4.0, z0 + 6.0))
    return out


# ----------------------------------------------------------------------------------------------- assembly / split
def dovetail(xc, y_mid, grow=0.0):
    """Tongue pointing +X from the cut plane at xc (2D sketch, mm)."""
    r, t, l = PARAMS["DOVE_ROOT"], PARAMS["DOVE_TIP"], PARAMS["DOVE_LEN"]
    g = grow
    return Polygon((xc - 1.0, y_mid - r / 2 - g), (xc, y_mid - r / 2 - g), (xc + l + g, y_mid - t / 2 - g),
                   (xc + l + g, y_mid + t / 2 + g), (xc, y_mid + r / 2 + g), (xc - 1.0, y_mid + r / 2 + g), align=None)


def split_parts(black_body, groups, cuts_mm, xmin, xmax):
    """Cut every coloured group at the split planes; returns {part_name: {colour: Compound}}."""
    bounds = [xmin - 1] + cuts_mm + [xmax + 1]
    names = ["A_left_jaw", "B_bar_left", "C_bar_right", "D_ring_head"]
    parts = {}
    for i, name in enumerate(names):
        x0, x1 = bounds[i], bounds[i + 1]
        win = Pos((x0 + x1) / 2, 0, 50) * Box(x1 - x0, 400, 200)
        d = {}
        for col, solids in groups.items():
            ss = []
            for s in solids:
                try:
                    r = s & win
                except Exception:
                    continue
                ss.extend(r.solids())
            if ss:
                d[col] = ss
        parts[name] = d
    return parts


def build():
    base, orange_band, outline = make_body()
    ymid = P(0, 350)[1]
    cuts_mm = [P(c, 0)[0] for c in PARAMS["CUTS_PX"]]
    base = keyholes(base)
    base = hook_holes(base)
    base = cut_brake_socket(base)
    shop = workshop()
    shop["black"][0] = cut_brake_socket(shop["black"][0])
    groups = {"black": [base] + screw_heads() + shop["black"], "orange": [orange_band] + shop["orange"],
              "white": shop["white"], "red": shop["red"]}
    bb = base.bounding_box()
    xmin, xmax = bb.min.X, bb.max.X
    parts = split_parts(base, {"black": [base] + screw_heads() + shop["black"], "orange": groups["orange"],
                               "white": groups["white"], "red": groups["red"]}, cuts_mm, xmin, xmax)
    # dovetails: tongue on the left part, groove in the right part (black base only)
    for i, xc in enumerate(cuts_mm):
        left, right = list(parts.values())[i], list(parts.values())[i + 1]
        tongue = ext(dovetail(xc, ymid), 0, T - 1.5)
        groove = ext(dovetail(xc, ymid, grow=PARAMS["CLEAR"]), -0.1, T - 1.2)   # blind groove, front face stays closed
        left["black"][0] = left["black"][0] + tongue
        right["black"][0] = right["black"][0] - groove
        # splice plate recess + pilot holes on the back
        L, H, TT = PARAMS["SPLICE_L"], PARAMS["SPLICE_H"], PARAMS["SPLICE_T"]
        rec = Pos(xc, ymid, 0) * Box(L, H, TT + 0.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        left["black"][0] = left["black"][0] - rec
        right["black"][0] = right["black"][0] - rec
        for sx in (-17, -9, 9, 17):
            for sy in (-7, 7):
                hole = Pos(xc + sx, ymid + sy, TT) * Cylinder(1.3, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
                tgt = left if sx < 0 else right
                tgt["black"][0] = tgt["black"][0] - hole
    # separate loose parts
    hooks = {f"hook_{i+1}": {"black": [make_hook(h)]} for i, h in enumerate(PARAMS["HOOKS_PX"])}
    splices = {}
    L, H, TT = PARAMS["SPLICE_L"] - 2 * PARAMS["CLEAR"], PARAMS["SPLICE_H"] - 2 * PARAMS["CLEAR"], PARAMS["SPLICE_T"] - 0.1
    for i, xc in enumerate(cuts_mm):
        plate = Pos(xc, ymid, 0) * Box(L, H, TT, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for sx in (-17, -9, 9, 17):
            for sy in (-7, 7):
                plate = plate - Pos(xc + sx, ymid + sy, 0) * Cylinder(1.7, TT + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
                cs = Pos(xc + sx, ymid + sy, 0) * Solid.make_cone(1.7, 3.0, 0.0001 + 1.3, Plane.XY.offset(TT - 1.3).location) \
                    if False else None
        splices[f"splice_{i+1}"] = {"black": [plate]}
    return parts, hooks, splices


def brake_variants():
    return {"disc": fit_brake(brake_disc()), "drum": fit_brake(brake_drum())}


COLOURS = {"black": "#1b1b1d", "orange": "#ff7a00", "white": "#e8e8ea", "red": "#d01818"}


def export_all(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    parts, hooks, splices = build()
    brakes = brake_variants()
    everything = {}
    for group in (parts, hooks, splices):
        everything.update(group)
    for name, cols in brakes.items():
        everything[f"brake_{name}"] = cols
    report = []
    asm = {"disc": [], "drum": []}
    for pname, cols in everything.items():
        for col, solids in cols.items():
            solids = solids if isinstance(solids, list) else [solids]
            if len(solids) > 1:                       # merge touching/overlapping solids of one colour
                try:
                    solids = list(solids[0].fuse(*solids[1:]).clean().solids())
                except Exception as e:  # noqa
                    print("fuse failed", pname, col, e)
            cols[col] = solids
            comp = Compound(children=solids)
            comp.label = f"{pname}_{col}"
            base = f"{pname}__{col}"
            (out / "step").mkdir(exist_ok=True)
            (out / "stl").mkdir(exist_ok=True)
            export_step(comp, str(out / "step" / f"{base}.step"))
            export_stl(comp, str(out / "stl" / f"{base}.stl"), tolerance=0.02, angular_tolerance=0.1)
            valid = all(s.is_valid for s in comp.solids())
            vol = sum(s.volume for s in comp.solids())
            bb = comp.bounding_box()
            report.append((pname, col, len(comp.solids()), valid, vol, (bb.size.X, bb.size.Y, bb.size.Z)))
            if pname.startswith("brake_"):
                asm[pname.split("_")[1]].append(comp)
            else:
                for k in asm:
                    asm[k].append(comp)
    # exact interference check (OCC booleans): every pair of different components, per brake variant
    print("interference check (volume > 1 mm3 is reported):")
    items = [(n, c, Compound(children=s if isinstance(s, list) else [s])) for n, cols in everything.items()
             for c, s in cols.items()]
    nclash = 0
    for variant in ("disc", "drum"):
        use = [(n, c, comp) for n, c, comp in items if not n.startswith("brake_") or n == f"brake_{variant}"]
        for i in range(len(use)):
            for j in range(i + 1, len(use)):
                (na, ca, A), (nb, cb, B) = use[i], use[j]
                if na == nb:
                    continue
                ba, bb = A.bounding_box(), B.bounding_box()
                if ba.min.X > bb.max.X or bb.min.X > ba.max.X or ba.min.Y > bb.max.Y or bb.min.Y > ba.max.Y \
                        or ba.min.Z > bb.max.Z or bb.min.Z > ba.max.Z:
                    continue
                try:
                    v = (A & B).volume
                except Exception as e:  # noqa
                    v = -1
                if v > 1.0 or v < 0:
                    nclash += 1
                    print(f"  [{variant}] {na}/{ca} x {nb}/{cb}: {v:.1f} mm3")
    print("  clashes:", nclash)
    for k, comps in asm.items():
        a = Compound(children=comps)
        a.label = f"wrench_keyholder_{k}_brake"
        export_step(a, str(out / f"assembly_{k}_brake.step"))
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "wrench_keyholder" / "out"))
    a = ap.parse_args()
    rep = export_all(Path(a.out))
    for r in rep:
        print("%-12s %-7s solids=%d valid=%s vol=%.0f mm3 bbox=%.1fx%.1fx%.1f" % (r[0], r[1], r[2], r[3], r[4], *r[5]))
