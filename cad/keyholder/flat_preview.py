"""Car-upholstery key holder: FLAT 2D drawing (step 1, no 3D yet).

Clean parametric shapes, measured on the 1536x1024 reference picture (picture px, y down).
Usage: python flat_preview.py <reference.png> <out_dir>
Writes flat.png (final colours), overlay.png (drawing 55 % over the reference).
"""
import sys, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely import affinity
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seat_wheel import seat_wheel, draw_seat_wheel

W_MM = 300.0
X0, X1 = 75.0, 1480.0           # plate left / right edge in the picture
MM_PX = W_MM / (X1 - X0)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "NotoSans-Bold.ttf")


def chaikin(pts, n=4):
    p = np.array(pts, float)
    for _ in range(n):
        q = np.empty((2 * len(p), 2))
        nxt = np.roll(p, -1, axis=0)
        q[0::2] = 0.75 * p + 0.25 * nxt
        q[1::2] = 0.25 * p + 0.75 * nxt
        p = q
    return Polygon(p).buffer(0)


def smooth_line(pts, n=4):
    p = np.array(pts, float)
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1])
        p = np.array(q)
    return LineString(p)


def ellipse(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, 64), rx, ry)
    e = affinity.rotate(e, rot, origin=(0, 0))
    return affinity.translate(e, cx, cy)


def text_poly(s, x, y_base, width, height_cap, italic=0.2):
    fp = FontProperties(fname=FONT)
    tp = TextPath((0, 0), s, size=100, prop=fp)
    polys = [Polygon(r).buffer(0) for r in tp.to_polygons() if len(r) > 2]
    polys.sort(key=lambda p: -p.area)
    res = None
    for p in polys:
        if res is None:
            res = p
        elif res.contains(p.representative_point()):
            res = res.difference(p)
        else:
            res = res.union(p)
    minx, miny, maxx, maxy = res.bounds
    cap = 72.9  # cap height of Noto Sans Bold at size 100
    res = affinity.scale(res, width / (maxx - minx), height_cap / cap, origin=(minx, 0))
    res = affinity.skew(res, xs=math.degrees(math.atan(italic)), origin=(minx, 0))
    res = affinity.scale(res, 1, -1, origin=(0, 0))      # picture y is down
    b = res.bounds
    return affinity.translate(res, x - b[0], y_base)     # y=0 (baseline) -> y_base


def smooth_poly(poly, step=2.0, sigma=5.0):
    """Resample the outline every `step` px and gaussian-smooth the coordinates (removes jagged/broken edges)."""
    from scipy.ndimage import gaussian_filter1d
    ring = poly.exterior
    n = max(int(ring.length / step), 16)
    pts = np.array([ring.interpolate(i * ring.length / n).coords[0] for i in range(n)])
    pts = np.stack([gaussian_filter1d(pts[:, k], sigma, mode="wrap") for k in (0, 1)], axis=1)
    return Polygon(pts).buffer(0)


def dashed(line, dash=13.0, gap=8.0, w=2.4):
    """Stitch dashes along a line (shapely LineString/LinearRing)."""
    from shapely.ops import substring
    out, d, n = [], 0.0, line.length
    while d < n:
        seg = substring(line, d, min(d + dash, n))
        if seg.length > 3:
            out.append(seg.buffer(w, cap_style=2))
        d += dash + gap
    return unary_union(out)


def strip_stitches(strip):
    """Cream dashed stitching like the picture: along the upper and lower edge (inset 12 px) + the fold line."""
    ring = strip.buffer(-12).exterior
    edge = ring.intersection(box(650, 440, 1405, 660))
    lines = list(edge.geoms) if hasattr(edge, "geoms") else [edge]
    fold = smooth_line([(1378, 482), (1335, 494), (1295, 534), (1262, 588), (1236, 618)])
    curl = smooth_line([(1300, 572), (1350, 580), (1400, 592)])
    parts = [dashed(l) for l in lines if l.length > 20] + [dashed(fold), dashed(curl, 11, 8, 2.0)]
    return unary_union(parts)


# ---------------------------------------------------------------- shapes
def build():
    L = {}
    bar = chaikin([(75, 600), (95, 555), (190, 548), (1380, 540), (1455, 548), (1480, 600),
                   (1478, 670), (1455, 705), (1380, 712), (800, 728), (200, 730), (110, 722), (80, 680)], 3)
    # arch outer edge + right block (measured on 3x crop), then down to the bar
    arch_pts = [(688, 118), (740, 88), (860, 71), (1000, 76), (1130, 115), (1230, 175), (1300, 240), (1335, 272)]
    outline = (arch_pts + [(1377, 295), (1400, 312), (1443, 350), (1447, 425), (1415, 445),
                           (1420, 470), (1470, 520), (1480, 600), (700, 600), (600, 560), (600, 200), (640, 150)])
    body = chaikin(outline, 2)                # smooth arch
    behind_wheel = ellipse(570, 245, 175, 197, -8).union(box(520, 200, 700, 600))
    base = unary_union([bar, body, behind_wheel])
    L["base"] = base

    # inner dark panel (behind lettering / machine)
    panel_pts = [(733, 195), (790, 166), (860, 150), (993, 149), (1127, 183), (1240, 243), (1300, 277),
                 (1330, 300), (1385, 332), (1425, 362), (1428, 440), (1300, 505), (700, 545), (640, 505), (640, 230)]
    panel = chaikin(panel_pts, 2)
    L["panel"] = panel.intersection(base)
    # recessed "wood" band between the outer arch ring and the panel
    ring_in = chaikin(arch_pts + [(1335, 272), (1300, 330), (700, 330), (688, 118)], 2).buffer(-24)
    L["band"] = ring_in.difference(panel).intersection(box(640, 60, 1340, 300))

    # steering wheel
    wheel_o = ellipse(570, 245, 168, 190, -8)
    wheel_i = ellipse(570, 245, 122, 144, -8)
    L["wheel_ring"] = wheel_o.difference(wheel_i)
    hub = Point(566, 222).buffer(56)
    spokes = [Polygon([(455, 195), (520, 200), (520, 245), (462, 240)]),
              Polygon([(612, 210), (690, 218), (692, 255), (612, 262)]),
              Polygon([(535, 270), (595, 270), (578, 380), (548, 382)])]
    L["wheel_hub"] = unary_union([hub] + spokes)
    L["wheel_btn"] = unary_union([Point(468, 218).buffer(7), Point(486, 220).buffer(7),
                                  Point(668, 235).buffer(7), Point(650, 233).buffer(7)])
    L["wheel_mark"] = wheel_o.difference(ellipse(570, 245, 150, 172, -8)).intersection(box(535, 40, 590, 110))

    # seat
    back = chaikin([(100, 420), (95, 300), (120, 210), (170, 160), (260, 150), (400, 175),
                    (450, 230), (500, 330), (545, 440), (575, 520), (570, 590), (480, 610),
                    (300, 610), (210, 600), (190, 560), (140, 540), (105, 480)], 4)
    head = chaikin([(205, 118), (215, 55), (260, 38), (370, 45), (402, 75), (404, 165), (300, 168), (212, 165)], 4)
    cush = chaikin([(205, 545), (232, 505), (330, 482), (470, 472), (560, 492), (580, 540),
                    (560, 592), (470, 612), (300, 617), (215, 597)], 4)
    L["seat_back"], L["seat_head"], L["seat_cush"] = back, head, cush
    L["seat_centre"] = chaikin([(255, 162), (415, 168), (432, 240), (440, 480), (300, 485), (262, 470), (252, 260)], 3)
    dia_area = box(272, 270, 438, 470)
    step, lines = 46, []
    for k in range(-12, 13):
        lines.append(LineString([(272 + k * step, 270), (272 + k * step + 200, 470)]))
        lines.append(LineString([(272 + k * step + 200, 270), (272 + k * step, 470)]))
    L["diamond_lines"] = unary_union(lines).intersection(dia_area)
    L["diamond_area"] = dia_area
    L["stitch"] = unary_union([back.buffer(-12).exterior, head.buffer(-10).exterior,
                               cush.buffer(-12).exterior, L["seat_centre"].buffer(-8).exterior])

    seat_wheel(L)      # measured redraw of seat + wheel (overrides the first sketch above)

    # lettering (real font)
    L["text"] = unary_union([text_poly("Car", 770, 366, 262, 80, 0.22),
                             text_poly("Upholstery", 683, 472, 472, 78, 0.22)])

    # car silhouette: two crescents (roof sweep + lower sweep) and a small arc
    def cres(top, bot):
        return Polygon(list(smooth_line(top).coords) + list(smooth_line(bot).coords)[::-1]).buffer(0)
    roof = cres([(770, 228), (880, 194), (975, 178), (1090, 183), (1180, 223), (1250, 252), (1303, 287)],
                [(1303, 287), (1240, 266), (1170, 240), (1100, 212), (1040, 208), (985, 218), (930, 236), (860, 232), (770, 228)])
    low = cres([(762, 282), (800, 256), (870, 238), (940, 232), (990, 236)],
               [(990, 236), (930, 262), (860, 275), (790, 280), (762, 282)])
    arc = cres([(1118, 296), (1150, 276), (1195, 270), (1230, 280)], [(1230, 280), (1190, 282), (1150, 292), (1118, 296)])
    L["swoosh"] = unary_union([roof, low, arc])

    # sewing machine (measured on a 3x crop: px = 1130 + cx/3, 250 + cy/3)
    def m(pts):
        return [(1130 + x / 3, 250 + y / 3) for x, y in pts]
    body_m = chaikin(m([(160, 160), (270, 160), (330, 235), (450, 232), (600, 215), (720, 215), (790, 240), (830, 300),
                        (835, 420), (830, 625), (610, 625), (640, 500), (600, 400), (480, 352), (350, 362),
                        (290, 410), (270, 470), (160, 490), (128, 480), (128, 170)]), 2)
    needle = box(*m([(165, 95)])[0], *m([(220, 160)])[0])
    foot_rod = box(*m([(170, 480)])[0], *m([(215, 600)])[0])
    foot = box(*m([(85, 645)])[0], *m([(310, 670)])[0])
    knob = unary_union([box(*m([(598, 100)])[0], *m([(715, 128)])[0]), box(*m([(620, 128)])[0], *m([(692, 205)])[0])])
    hand = chaikin(m([(830, 250), (870, 238), (910, 270), (915, 420), (880, 480), (840, 470), (826, 400)]), 2)
    slot = box(*m([(190, 180)])[0], *m([(225, 462)])[0]).buffer(-1)
    L["machine"] = unary_union([body_m, needle, foot_rod, foot, knob, hand]).difference(slot)

    # red leather strip
    strip = chaikin([(548, 602), (620, 572), (720, 537), (820, 512), (940, 492), (1060, 480),
                     (1180, 479), (1300, 480), (1390, 484), (1440, 505), (1458, 540),
                     (1448, 582), (1410, 607), (1345, 618), (1280, 626), (1180, 633),
                     (1060, 633), (940, 624), (800, 616), (660, 611)], 4)
    L["strip"] = strip
    L["strip_stitch"] = strip_stitches(strip)

    # hooks (front view) and screw holes
    hooks = [305, 565, 820, 1075, 1315]
    L["hooks_x"] = hooks
    L["hook_knob"] = unary_union([Point(x, 668).buffer(25) for x in hooks])
    L["hook_lug"] = unary_union([box(x - 17, 668, x + 17, 752) for x in hooks] +
                                [Point(x, 752).buffer(17) for x in hooks])
    L["screws"] = [(150, 668), (1425, 648)]
    return L


# ---------------------------------------------------------------- drawing
def paint(ax, g, **kw):
    if g.is_empty:
        return
    if hasattr(g, "geoms"):
        for p in g.geoms:
            paint(ax, p, **kw)
    elif g.geom_type == "Polygon":
        verts, codes = [], []
        for ring in [g.exterior] + list(g.interiors):
            c = np.array(ring.coords)
            verts += list(c)
            codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def draw(L, path, ref=None, alpha=1.0):
    fig = plt.figure(figsize=(15.36, 10.24), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1536); ax.set_ylim(1024, 0); ax.axis("off")
    if ref is not None:
        ax.imshow(Image.open(ref).convert("RGB"), extent=(0, 1536, 1024, 0))
        a = alpha
    else:
        ax.add_patch(plt.Rectangle((0, 0), 1536, 1024, fc="#d9d4cc"))
        a = 1.0
    BLK, BLK2, BLK3 = "#15151a", "#26262e", "#3a3a45"
    RED, SIL = "#c4161c", "#d8d8dc"
    kw = lambda c: dict(fc=c, ec="none", lw=0, alpha=a)
    paint(ax, L["base"], **kw(BLK))
    paint(ax, L["panel"], **kw(BLK2))
    paint(ax, L["band"], **kw(BLK3))
    draw_seat_wheel(ax, L, paint, kw, (BLK, BLK2, BLK3, RED, SIL))
    paint(ax, L["text"], **kw(SIL))
    paint(ax, L["swoosh"], **kw(SIL))
    paint(ax, L["machine"], **kw(SIL))
    paint(ax, L["strip"], **kw(RED))
    paint(ax, L["strip_stitch"], **kw("#f0e6d0"))
    paint(ax, L["hook_lug"], **kw(BLK2))
    paint(ax, L["hook_knob"], **kw(BLK3))
    for x in L["hooks_x"]:
        paint(ax, Point(x, 668).buffer(9), **kw(BLK))
    for (x, y) in L["screws"]:
        paint(ax, Point(x, y).buffer(11), **kw("#0a0a0a"))
    fig.savefig(path, dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    ref, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    L = build()
    if len(sys.argv) > 3:        # traced big shapes (local json from trace_keyholder.py)
        import json
        T = json.load(open(sys.argv[3]))
        L["strip"] = smooth_poly(Polygon(T["strip"]).buffer(0).buffer(-4).buffer(4), 2.0, 4.0)
        L["strip_stitch"] = strip_stitches(L["strip"])
        sw = Polygon(T["swoosh"]).buffer(0)
        L["swoosh"] = sw
        if "sil" in T:
            L["base"] = Polygon(T["sil"]).buffer(0).buffer(-5).buffer(5).buffer(14).buffer(-14)
            L["base"] = smooth_poly(L["base"], 2.0, 6.0)
            L["panel"] = L["panel"].intersection(L["base"])
    b = unary_union([L["base"], L["wheel_ring"], L["seat_left"], L["seat_head"], L["hook_lug"]]).bounds
    print("bbox px", [round(v) for v in b], "-> mm", round((b[2]-b[0])*MM_PX, 1), "x", round((b[3]-b[1])*MM_PX, 1))
    draw(L, f"{out}/flat.png")
    draw(L, f"{out}/overlay.png", ref=ref, alpha=0.55)
