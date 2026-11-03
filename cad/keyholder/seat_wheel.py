"""Seat + steering wheel redrawn from a 1.5x crop of the reference (px = 80 + cx/1.5, 20 + cy/1.5).

Pieces are separate shapes (each will get its own relief height in 3D), stitching = dashed red lines like the picture.
"""
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, substring
from shapely import affinity


def C(pts):
    return [(80 + x / 1.5, 20 + y / 1.5) for x, y in pts]


def _smooth_closed(pts, n=3):
    p = np.array(pts, float)
    for _ in range(n):
        q = np.empty((2 * len(p), 2))
        nxt = np.roll(p, -1, axis=0)
        q[0::2] = 0.75 * p + 0.25 * nxt
        q[1::2] = 0.25 * p + 0.75 * nxt
        p = q
    return Polygon(p).buffer(0)


def _smooth_open(pts, n=3):
    p = np.array(pts, float)
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1])
        p = np.array(q)
    return LineString(p)


def _dash(line, dash=11.0, gap=7.0, w=1.9):
    out, d, n = [], 0.0, line.length
    while d < n:
        seg = substring(line, d, min(d + dash, n))
        if seg.length > 3:
            out.append(seg.buffer(w, cap_style=2))
        d += dash + gap
    return unary_union(out)


def _ell(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, 64), rx, ry)
    e = affinity.rotate(e, rot, origin=(0, 0))
    return affinity.translate(e, cx, cy)


def seat_wheel(L):
    # ---------------- steering wheel (behind the seat) -------------------
    wo = _ell(570, 232, 168, 201)
    wi = _ell(570, 229, 130, 152)
    L["wheel_ring"] = wo.difference(wi)
    L["wheel_mark"] = L["wheel_ring"].intersection(box(547, 20, 582, 100))
    hub_c = (557, 237)
    ring = Point(*hub_c).buffer(70).difference(Point(*hub_c).buffer(61))
    spokes = unary_union([
        Polygon(C([(530, 240), (640, 236), (650, 330), (535, 300)])),                       # left
        Polygon(C([(800, 262), (935, 325), (938, 352), (815, 378), (800, 330)])),            # right
        Polygon(C([(655, 425), (700, 440), (775, 428), (748, 548), (716, 562), (693, 546)])),  # bottom
    ])
    slot = Polygon(C([(702, 462), (742, 458), (730, 522), (714, 522)]))
    L["wheel_hub"] = unary_union([ring, spokes]).difference(slot)
    L["wheel_pad"] = Point(*hub_c).buffer(61)           # dark airbag cover (slightly raised)
    L["wheel_logo"] = Point(*hub_c).buffer(26)
    L["wheel_btn"] = unary_union([
        box(*C([(548, 258)])[0], *C([(580, 285)])[0]), box(*C([(582, 258)])[0], *C([(612, 283)])[0]),
        box(*C([(548, 290)])[0], *C([(580, 312)])[0]), box(*C([(582, 288)])[0], *C([(612, 308)])[0]),
        box(*C([(830, 285)])[0], *C([(868, 312)])[0]), box(*C([(872, 292)])[0], *C([(912, 320)])[0]),
        box(*C([(830, 318)])[0], *C([(868, 340)])[0]), box(*C([(872, 325)])[0], *C([(910, 345)])[0]),
    ]).buffer(2).buffer(-2)
    L["wheel_stitch"] = _dash(wi.buffer(9).exterior, 12, 8, 1.8)

    # ---------------- seat pieces ----------------------------------------
    head = _smooth_closed(C([(215, 110), (232, 45), (290, 15), (420, 22), (470, 60), (497, 140),
                             (490, 205), (380, 225), (250, 208), (215, 165)]), 3)
    left_b = _smooth_closed(C([(72, 300), (112, 232), (200, 205), (255, 208), (290, 300), (305, 500),
                               (310, 690), (245, 775), (190, 830), (130, 770), (75, 570)]), 3)
    centre_up = Polygon(C([(262, 222), (500, 225), (515, 365), (285, 368)])).buffer(-5).buffer(5)
    diamond = Polygon(C([(290, 368), (515, 368), (555, 665), (318, 668)])).buffer(-5).buffer(5)
    right_b = _smooth_closed(C([(520, 285), (585, 325), (650, 420), (692, 540), (688, 620),
                                (670, 720), (560, 760), (520, 366)]), 3).difference(diamond.buffer(2)).difference(centre_up.buffer(1))
    cush = _smooth_closed(C([(300, 700), (450, 676), (600, 676), (700, 722), (742, 790), (722, 852),
                             (600, 882), (430, 882), (300, 872), (190, 852), (184, 792), (232, 745)]), 4)
    L["seat_head"], L["seat_left"], L["seat_centre"] = head, left_b.difference(centre_up.buffer(1)), centre_up
    L["seat_diamond"], L["seat_right"], L["seat_cush"] = diamond, right_b, cush

    # filler under the seat pieces: no empty gaps between them (closing of the union)
    parts = unary_union([head, L["seat_left"], centre_up, diamond, right_b, cush])
    L["seat_fill"] = parts.buffer(22).buffer(-22).intersection(L["base"].buffer(-3) if "base" in L else parts.buffer(22))

    # diamond lattice (clean, parametric): pitch 52 px wide, 70 px tall
    x0, y0, x1, y1 = diamond.bounds
    lines = []
    for k in range(-14, 16):
        xs = 273 + k * 52
        lines.append(LineString([(xs, y0 - 10), (xs + 26 * 14, y0 - 10 + 35 * 14)]))
        lines.append(LineString([(xs + 26 * 14, y0 - 10), (xs, y0 - 10 + 35 * 14)]))
    lat = unary_union(lines).intersection(diamond.buffer(-6))
    L["seat_lattice"] = unary_union([_dash(g, 12, 6, 1.6) for g in (lat.geoms if hasattr(lat, "geoms") else [lat])])

    st = [
        C([(268, 35), (262, 110), (272, 190)]), C([(298, 30), (292, 110), (302, 195)]),   # headrest left
        C([(440, 45), (468, 110), (480, 195)]),                                           # headrest right
        C([(212, 222), (180, 300), (178, 520), (190, 820)]), C([(138, 240), (128, 400), (140, 600), (172, 800)]),  # left bolster
        C([(268, 232), (300, 400), (312, 690)]),                                          # left bolster inner
        C([(530, 295), (610, 360), (670, 470), (682, 590)]),                              # right bolster edge
        C([(300, 692), (450, 676), (600, 678), (695, 720), (735, 785)]),                  # cushion top
        C([(205, 752), (350, 740), (450, 760), (495, 820), (500, 870)]),                  # cushion front
        C([(200, 777), (330, 757), (440, 787), (480, 842)]),
    ]
    L["seat_stitch"] = unary_union([_dash(_smooth_open(s, 3), 11, 7, 1.9) for s in st])
    L["seat_piping"] = _smooth_open(C([(490, 232), (520, 360), (540, 500), (556, 665)]), 2).buffer(3.2)
    return L


def draw_seat_wheel(ax, L, paint, kw, cols):
    BLK, BLK2, BLK3, RED, SIL = cols
    paint(ax, L["wheel_ring"].buffer(1.5), **kw(BLK))
    paint(ax, L["wheel_ring"], **kw(BLK3))
    paint(ax, L["wheel_stitch"], **kw(RED))
    paint(ax, L["wheel_mark"], **kw(RED))
    paint(ax, L["wheel_hub"], **kw(SIL))
    paint(ax, L["wheel_pad"], **kw(BLK))
    paint(ax, L["wheel_logo"], **kw(BLK2))
    paint(ax, L["wheel_btn"], **kw(BLK))
    paint(ax, L["seat_fill"], **kw(BLK2))
    for k in ("seat_left", "seat_right", "seat_cush", "seat_head"):
        paint(ax, L[k].buffer(1.5), **kw(BLK))
        paint(ax, L[k], **kw(BLK3))
    paint(ax, L["seat_centre"], **kw(BLK2))
    paint(ax, L["seat_diamond"], **kw(BLK3))
    paint(ax, L["seat_lattice"], **kw(RED))
    paint(ax, L["seat_piping"], **kw(RED))
    paint(ax, L["seat_stitch"], **kw(RED))
