"""Dome of the Rock wall art (frame + building + olive branches), clean parametric redraw of the owner's reference picture.

All numbers are in the picture's own pixels (1086 x 1448, y down), measured on zoomed crops / mask profiles.
Black = one connected cut-out piece, cream = through holes, gold = plate under the dome grid.
The olive branches are drawn in quds_branches.py (clean leaves on measured spines).
"""
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

CX = 556.0                                   # building axis
FRAME_OUT = (103.0, 90.0, 976.0, 1355.5)     # outer frame
FRAME_IN = (149.0, 139.0, 930.0, 1310.0)     # inner opening
LINE = 5.4                                   # thinnest black line (1.2 mm at 290 mm height)


def mir(g, cx=CX):
    return affinity.scale(g, -1, 1, origin=(cx, 0))


def sym(g, cx=CX):
    return unary_union([g, mir(g, cx)])


def lame(cx, a, spring, apex, bottom, n=2.0, k=40):
    """Arch: straight sides from `bottom` up to `spring`, then a Lame curve (n=2 round, n<2 pointed) up to `apex`."""
    t = np.linspace(0, 1, k)
    hw = a * (1 - t ** n) ** (1 / n)
    y = spring - t * (spring - apex)
    left = list(zip(cx - hw, y)); right = list(zip(cx + hw, y))[::-1]
    return Polygon([(cx - a, bottom)] + left + right[1:] + [(cx + a, bottom)])


def below(line_y, x0, x1, ymax=2000.0):
    """Half plane under a sloped line y = line_y(x) between x0 and x1."""
    return Polygon([(x0, line_y(x0)), (x1, line_y(x1)), (x1, ymax), (x0, ymax)])


def taper(p0, p1, w0, w1):
    """Straight line whose width goes from w0 to w1 (perspective paving joints)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0; n = np.array([-d[1], d[0]]) / np.hypot(*d)
    return Polygon([p0 + n * w0 / 2, p1 + n * w1 / 2, p1 - n * w1 / 2, p0 - n * w0 / 2])


def lattice(x0, x1, y0, y1, pitch, w, phase=0.0):
    """Cream cells of a diamond lattice band: diamonds on the centre line, half diamonds on both edges."""
    h = y1 - y0
    dist = pitch * h / np.hypot(pitch / 2, h)          # distance between parallel lattice lines
    f = 1 - w / dist
    cells = []
    i0 = int(np.floor((x0 - phase) / pitch)) - 1; i1 = int(np.ceil((x1 - phase) / pitch)) + 1
    for i in range(i0, i1 + 1):
        for cxx, cyy in ((phase + i * pitch, (y0 + y1) / 2), (phase + (i + .5) * pitch, y0), (phase + (i + .5) * pitch, y1)):
            cells.append(Polygon([(cxx - f * pitch / 2, cyy), (cxx, cyy - f * h / 2), (cxx + f * pitch / 2, cyy), (cxx, cyy + f * h / 2)]))
    return unary_union(cells).intersection(box(x0, y0, x1, y1))


# ---------------------------------------------------------------- dome
_PROF = np.array([(0, 451), (20, 452.5), (42, 458.5), (65.5, 468), (92.5, 480), (113, 492), (130.5, 504), (144.5, 516), (157, 528),
                  (168, 540), (178, 552), (186, 564), (193.5, 576), (200, 588), (205, 600), (210, 612), (213.5, 624),
                  (216.5, 636), (219.5, 648), (220.5, 660), (221, 672), (220.5, 684), (218, 698)])
TILT = 0.288                                  # the picture looks up at the dome: parallels are arcs


def dome_r(y):
    return np.interp(y, _PROF[:, 1], _PROF[:, 0])


def dome_silhouette():
    from scipy.interpolate import splev, splprep
    pts = np.vstack([np.c_[-_PROF[::-1, 0], _PROF[::-1, 1]], np.c_[_PROF[1:, 0], _PROF[1:, 1]]])
    tck, _ = splprep(pts.T, s=6.0)
    x, y = splev(np.linspace(0, 1, 400), tck)
    return Polygon(np.c_[x + CX, y])


def ring_top(X):
    return 643 + 63.6 * (1 - np.sqrt(np.clip(1 - (X / 221.0) ** 2, 0, 1)))


def ring_bot(X):
    return 665 + 70.0 * (1 - np.sqrt(np.clip(1 - (X / 236.0) ** 2, 0, 1)))


def _curve_poly(f_top, f_bot, x0, x1, k=160):
    X = np.linspace(x0, x1, k)
    return Polygon(list(zip(CX + X, f_top(X))) + list(zip(CX + X[::-1], f_bot(X[::-1]))))


def dome():
    """-> black (outline, grid, ring, finial), gold (visible cells), gold_plate (whole area under the grid)."""
    sil = dome_silhouette()
    above_ring = _curve_poly(lambda X: X * 0 + 400, ring_top, -235, 235)
    inner = sil.buffer(-9.0)
    yh = np.linspace(451, 708, 260); r = dome_r(yh)
    lines = []
    for i in range(5):                                           # meridians, 14 degrees apart
        phi = np.radians(7 + 14 * i)
        for s in (-1, 1):
            lines.append(LineString(np.c_[CX + s * r * np.sin(phi), yh - TILT * r * np.cos(phi)]).buffer(LINE / 2, cap_style=2))
    front = yh - TILT * r                                        # image height of each level on the centre line
    for yc in (484, 506, 535, 571, 614):                         # parallels (measured on the centre line)
        h = np.interp(yc, front, yh); rr = dome_r(h)
        phi = np.radians(np.linspace(-89, 89, 120))
        lines.append(LineString(np.c_[CX + rr * np.sin(phi), h - TILT * rr * np.cos(phi)]).buffer(LINE / 2))
    X = np.linspace(-130, 130, 80)
    cap = Polygon(list(zip(CX + X, 474 + 18 * (X / 100) ** 2)) + [(CX + 130, 440), (CX - 130, 440)])
    grid = unary_union(lines + [cap]).intersection(sil)
    ring = unary_union([_curve_poly(ring_top, ring_bot, -216, 216),
                        sym(affinity.scale(Point(CX - 221, 703).buffer(1.0, 32), 14.0, 21.0))])
    cres = Point(CX, 363).buffer(23, 48).difference(Point(CX, 356.5).buffer(17, 48))
    finial = unary_union([cres, box(CX - 5, 384, CX + 5, 446), Point(CX, 404).buffer(9.5), Point(CX, 422).buffer(13.5),
                          Polygon([(CX - 5, 438), (CX + 5, 438), (CX + 10, 448), (CX + 23, 461), (CX + 23, 466),
                                   (CX - 23, 466), (CX - 23, 461), (CX - 10, 448)])])
    outline = sil.difference(inner).intersection(above_ring.union(ring))
    black = unary_union([outline, grid.intersection(above_ring), ring, finial])
    plate = inner.intersection(above_ring)
    return black, plate.difference(black), plate


# ---------------------------------------------------------------- drum (under the dome)
def _panel(xc, hw, top, hw_out, bar=0.0, bot=748.0, tie=4.6):
    """Cream of one drum panel: rhombus ring (two chevrons, the black centre diamond hangs on a vertical tie),
    small corner triangles, and optional side bars."""
    ihw = hw - (bar + LINE if bar else 0)
    sq = box(xc - ihw, top, xc + ihw, bot)
    yc, hh = (top + bot) / 2, (bot - top) / 2
    rh = lambda a, b: Polygon([(xc - a, yc), (xc, yc - b), (xc + a, yc), (xc, yc + b)])
    outer, inn = rh(hw_out, hh), rh(hw_out * 0.45, hh * 0.5)
    cream = [outer.intersection(sq).difference(inn).difference(box(xc - tie / 2, top - 5, xc + tie / 2, bot + 5))]
    corners = sq.difference(rh(hw_out + LINE * np.hypot(hw_out, hh) / hh, hh + LINE * np.hypot(hw_out, hh) / hw_out))
    cream += [g for g in getattr(corners, "geoms", [corners]) if g.area > 40]
    if bar:
        cream += [box(xc - hw, top - 2, xc - hw + bar, 752), box(xc + hw - bar, top - 2, xc + hw, 752)]
    return unary_union(cream)


def drum():
    """-> body (black), holes (cream)."""
    X = np.linspace(-222, 222, 200)
    body = Polygon(list(zip(CX + X, ring_bot(X))) + [(CX + 222, 754), (CX - 222, 754)])
    strip = _curve_poly(ring_bot, lambda X: ring_bot(X) + 17, -211, 211).difference(sym(box(CX - 76, 600, CX - 37, 760)))
    pt = lambda Xc: float(ring_bot(np.array(Xc))) + 23
    holes = [strip,
             _panel(CX, 36, pt(0.0) + 1.5, 30, bar=8.0),
             sym(_panel(CX - 102, 26, pt(-102.0), 30)),
             sym(_panel(CX - 182.5, 16.5, pt(-182.5), 19))]
    return body, unary_union(holes)


# ---------------------------------------------------------------- front face + wings (left half, mirrored)
FX = 557.0 - CX      # the front face was measured around x = 557


def front():
    """-> body, holes of the octagon's front face (y 753..1086)."""
    body = box(322, 753, 2 * 557 - 322, 1089)
    H = [box(323, 766, 791, 775), box(323, 820, 791, 831), lattice(323, 791, 781, 811, 36.0, LINE, phase=557.0)]
    # arcade: two small arches + half of the big centre arch
    O1 = lame(376, 27, 885, 857, 1200, n=1.8); O2 = lame(449.5, 26.5, 885, 858, 1200, n=1.8)
    E = unary_union([lame(377, 46, 885, 849, 885), lame(449, 46, 885, 849, 885)])
    legs = unary_union([box(331, 884, 349, 947), box(403, 884, 423, 917), box(476, 884, 495, 917)])
    O0 = lame(557, 49, 928, 884, 1200, n=1.5)
    b_in, b_gap, b_out = O0.buffer(17, 32), O0.buffer(26, 32), O0.buffer(42, 32)
    top = box(300, 849, 814, 2000)
    molding = b_out.difference(b_gap).intersection(box(476, 849, 557, 917))
    m_band = unary_union([E, legs]).difference(unary_union([O1, O2])).difference(b_gap).intersection(top)
    half = [unary_union([m_band, molding]).intersection(box(331, 849, 557, 947))]
    # spandrels (small cream triangles above the arches)
    sp = box(331, 849, 557, 880).difference(unary_union([E, b_out]).buffer(LINE))
    half += [g for g in getattr(sp, "geoms", [sp]) if g.area > 45]
    # lintel + inner band of the big arch
    half.append(unary_union([box(389, 927, 510, 947), b_in.difference(O0)]).intersection(box(389, 849, 557, 947)).difference(O0))
    # columns (capital, shaft, base), panels, base block
    for c, w in ((414.5, 15.5), (493.5, 16.0)):
        half += [Polygon([(c - 12.5, 953.5), (c + 12.5, 953.5), (c + 9.5, 961.5), (c - 9.5, 961.5)]),
                 Polygon([(c - w / 2, 967), (c + w / 2, 967), (c + w / 2, 1058), (c + 14.5, 1066), (c + 14.5, 1081.5),
                          (c - 14.5, 1081.5), (c - 14.5, 1066), (c - w / 2, 1058)])]
    half += [box(328, 958.5, 351, 1050), box(360, 958.5, 397, 1050), box(441, 963, 470, 1070), box(328, 1057, 392, 1078)]
    H.append(sym(unary_union(half), 557.0))
    H.append(box(531, 964, 583, 1069))                          # door
    sh = lambda g: affinity.translate(g, -FX, 0)
    return sh(body), sh(unary_union(H))


def wing():
    """-> body, holes of the left side face in perspective (mirrored for the right one)."""
    top = lambda x: 760 + 0.407 * (300 - x)
    bot = lambda x: 1091 + 0.079 * (300 - x)
    body = Polygon([(323, top(323)), (140, top(140)), (140, bot(140)), (323, bot(323))])
    X0, X1 = 150.0, 311.0
    b1 = lambda x: 778 + 0.393 * (300 - x); b2 = lambda x: 830.5 + 0.318 * (300 - x)
    t1 = lambda x: 4.0 - 0.005 * (300 - x); t2 = lambda x: 4.5 - 0.009 * (300 - x)
    quad = lambda fa, fb: Polygon([(X0, fa(X0)), (X1, fa(X1)), (X1, fb(X1)), (X0, fb(X0))])
    H = [quad(lambda x: b1(x) - t1(x), lambda x: b1(x) + t1(x)), quad(lambda x: b2(x) - t2(x), lambda x: b2(x) + t2(x))]
    la = lambda x: b1(x) + t1(x) + LINE; lb = lambda x: b2(x) - t2(x) - LINE
    cells = lattice(X0, X1, 0.0, 30.0, 23.0, LINE, phase=X1 - 11.5)      # flat band 30 px high, then sheared into place
    band = []
    for c in getattr(cells, "geoms", [cells]):
        pts = np.array(c.exterior.coords)
        y = la(pts[:, 0]) + pts[:, 1] / 30.0 * (lb(pts[:, 0]) - la(pts[:, 0]))
        q = Polygon(np.c_[pts[:, 0], y]).buffer(0)
        if q.area > 18: band.append(q)
    H.append(unary_union(band))
    # three arches (cream bands), leg bottoms on a sloped line
    legb = lambda x: 951 + 0.18 * (300 - x)
    for cx, a, ai, spring, apex, th in ((283.0, 26.0, 15.3, 892, 859, 11.5), (231.0, 15.0, 7.2, 897, 875, 8.5), (192.0, 13.0, 6.2, 905, 885.5, 8.0)):
        outer = lame(cx, a, spring, apex, 1000, n=1.7); inner = lame(cx, ai, spring, apex + th, 1000, n=1.7)
        H.append(outer.difference(inner).difference(below(legb, 140, 330)))
    # panels + base strip
    pt = lambda x: 961 + 0.172 * (300 - x); pb = lambda x: 1051 + 0.043 * (300 - x)
    for xa, xb in ((278, 311), (238, 268), (200, 228), (167, 191), (149, 157)):
        H.append(Polygon([(xa, pt(xa)), (xb, pt(xb)), (xb, pb(xb)), (xa, pb(xa))]))
    st = lambda x: 1058 + 0.05 * (300 - x); sb = lambda x: 1080 + 0.036 * (300 - x)
    H.append(Polygon([(149, st(149)), (X1, st(X1)), (X1, sb(X1)), (149, sb(149))]))
    return body, unary_union(H)


def floor():
    """Paving joints (black lines) in front of the building."""
    l1 = [(140, 1131), (300, 1114.5), (375, 1110), (455, 1108.5), (557, 1107.5)]
    L = [LineString(l1 + [(650, 1108), (700, 1118), (760, 1127.5), (800, 1129.5)]).buffer(3.4, cap_style=2),   # runs under the leaves
         LineString([(140, 1182), (255, 1140), (362, 1141)]).buffer(4.0, join_style=2),
         taper((364, 1139), (170, 1313), 6.5, 15.0),          # far left joint
         taper((477, 1106), (371, 1313), 5.6, 16.0),          # left of centre
         taper((559.5, 1106), (614, 1220), 5.6, 10.0),        # right of centre (ends under the leaf)
         box(322, 1168, 449, 1175), box(252, 1227, 420, 1237),
         box(452, 1152, 584, 1158), box(421, 1212, 545, 1221), box(575, 1136, 700, 1142)]
    return unary_union(L)


def frame():
    return box(*FRAME_OUT).difference(box(*FRAME_IN))


def build():
    """-> dict(black, gold, plate, veins) in picture pixels."""
    from quds_branches import branches
    d_black, gold, plate = dome()
    parts = [frame(), d_black, floor()]
    for body, holes in (drum(), front()):
        parts.append(body.difference(holes))
    wb, wh = wing()
    parts += [wb.difference(wh), mir(wb.difference(wh), 557.0 - FX)]
    leaves, veins = branches()
    inside = box(*FRAME_OUT)
    black = unary_union(parts + [leaves]).intersection(inside).buffer(0)
    return {"black": black, "gold": gold.difference(black), "plate": plate, "veins": veins.intersection(box(*FRAME_IN))}
