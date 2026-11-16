"""Embroidery-style bookmark (navy + pink on white), clean parametric redraw of an owner's reference picture.

python cad/bookmarks/embroidery_navy_pink.py OUT_DIR REF_PNG     -> parts as WKT + flat preview with overlay
Layers: base (white, full outline minus the tassel hole, 1.2 mm), main (navy, 0.6 mm), accent (pink, 0.6 mm; cuts the navy).
Reference pixel box x 299..785, y 46..1398  ->  50 x 139 mm.  Everything raised sits on the solid base: no islands.
"""
import math
import sys
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

PX0, PX1, PY0, PY1 = 299, 785, 46, 1398
K = 50.0 / (PX1 - PX0)
W, H = 50.0, (PY1 - PY0) * K
CXP = (PX0 + PX1) / 2


def P(px, py):                       # picture pixel -> mm (y up)
    return ((px - PX0) * K, (PY1 - py) * K)


def line(pts, w):                    # pixel polyline -> thick line (mm)
    return LineString([P(*p) for p in pts]).buffer(w / 2, cap_style=1, join_style=1)


def mir(g):                          # mirror about the vertical centre line
    return affinity.scale(g, -1, 1, origin=(W / 2, 0))


def sym(g):
    return unary_union([g, mir(g)])


def kite(cx, cy, ang, length, width):
    a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
    m = 0.32 * length
    return Polygon([(cx, cy), (cx + ux * m + vx * width / 2, cy + uy * m + vy * width / 2), (cx + ux * length, cy + uy * length),
                    (cx + ux * m - vx * width / 2, cy + uy * m - vy * width / 2)])


def bud(cx, cy, ang, s=1.0):         # two small leaves spread +-35 deg from the axis angle (pink bud)
    out = []
    for d in (-32, 32):
        e = Point(0, 0).buffer(1, 24); e = affinity.scale(e, 1.55 * s, 0.82 * s)
        e = affinity.translate(e, 1.45 * s, 0); e = affinity.rotate(e, ang + d, origin=(0, 0))
        out.append(affinity.translate(e, cx, cy))
    return unary_union(out)


def ring(cx, cy, r0, r1):
    return Point(cx, cy).buffer(r1, 48).difference(Point(cx, cy).buffer(r0, 48))


def build():
    outer = box(0, 0, W, H).buffer(-3, join_style=1).buffer(3, join_style=1)
    hx, hy = W / 2, H - 5.6
    hole = Point(hx, hy).buffer(1.9, 40)
    inner = outer.buffer(-1.7, join_style=1)
    navy = [outer.difference(inner), ring(hx, hy, 1.9, 3.5)]
    pink = []
    # zig-zag borders left / right
    zz = []
    for i, py in enumerate(np.arange(262, 1236, 19.0)):
        zz.append((356 + (13 if i % 2 else -13), py))
    left = line(zz, 1.05); navy.append(sym(left))
    # corner diagonals (top + bottom): zigzag lines running toward the hole / the bottom centre
    def diag(p0, p1, n, amp):
        (x0, y0), (x1, y1) = p0, p1; L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L; vx, vy = -uy, ux
        pts = [(x0 + ux * L * t / n + vx * amp * (1 if t % 2 else -1), y0 + uy * L * t / n + vy * amp * (1 if t % 2 else -1)) for t in range(n + 1)]
        return line(pts, 1.05)
    navy.append(sym(diag((340, 222), (470, 98), 8, 9)))
    navy.append(sym(diag((372, 238), (458, 160), 5, 9)))
    navy.append(sym(diag((340, 1222), (524, 1368), 10, 9)))
    navy.append(sym(diag((372, 1206), (500, 1310), 7, 9)))
    # corner pinks
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        ox = 1.7 if sx > 0 else W - 1.7; oy = 1.7 if sy < 0 else H - 1.7
        tri = Polygon([(ox, oy), (ox + sx * 8.0, oy), (ox, oy - sy * 8.0)]).buffer(-1.3, join_style=1).buffer(1.8, join_style=1)
        pink.append(tri.intersection(inner))
    # small ornaments
    def plus(px, py, s=1.0, col=navy, long=2.9, short=1.5):
        cx, cy = P(px, py)
        for a in (0, 90):
            e = affinity.rotate(affinity.scale(Point(0, 0).buffer(1, 24), long * s, short * s), a, origin=(0, 0))
            col.append(sym(affinity.translate(e, cx, cy)) if abs(cx - W / 2) > 0.1 else affinity.translate(e, cx, cy))
    for off, py in ((115, 215), (127, 535)):
        plus(CXP - off, py)
    for off, py in ((135, 392), (135, 905)):
        plus(CXP - off, py, 0.95, pink)
    for off, py in ((72, 905),):
        cx, cy = P(CXP - off, py)
        navy.append(sym(unary_union([LineString([(cx - 1.1, cy - 1.1), (cx + 1.1, cy + 1.1)]).buffer(0.5), LineString([(cx - 1.1, cy + 1.1), (cx + 1.1, cy - 1.1)]).buffer(0.5)])))
    plus(CXP, 1300, 1.0)
    # tree
    cx, _ = P(CXP, 0)
    navy.append(line([(CXP, 248), (CXP, 560)], 1.05))
    for py, Lp in zip((290, 332, 374, 416, 458, 498), (22, 36, 52, 66, 80, 92)):
        navy.append(sym(line([(CXP, py), (CXP - Lp, py - Lp * 0.78)], 1.6)))
    navy.append(sym(line([(CXP, 548), (CXP - 92, 430)], 5.4)))
    for (dx, py, ang) in ((0, 232, 90), (47, 268, 118), (97, 318, 132), (110, 440, 150), (74, 372, 138)):
        for s in ((1, -1) if dx else (1,)):
            x, y = P(CXP + s * dx, py)
            pink.append(bud(x, y, ang if s > 0 else 180 - ang, 1.05))
    # snowflakes
    for cyp in (725, 1035):
        c0x, c0y = P(CXP, cyp)
        for a in (45, 135, 225, 315):
            navy.append(kite(c0x, c0y, a, 13.0, 8.8))
        for a in (0, 90, 180, 270):
            navy.append(kite(c0x, c0y, a, 11.2, 8.2))
            navy.append(LineString([(c0x, c0y), (c0x + 12.8 * math.cos(math.radians(a)), c0y + 12.8 * math.sin(math.radians(a)))]).buffer(0.55, cap_style=1))
            pink.append(bud(c0x + 12.4 * math.cos(math.radians(a)), c0y + 12.4 * math.sin(math.radians(a)), a, 1.05))
        for a in (45, 135, 225, 315):
            navy.append(LineString([(c0x, c0y), (c0x + 15.0 * math.cos(math.radians(a)), c0y + 15.0 * math.sin(math.radians(a)))]).buffer(0.55, cap_style=1))
            pink.append(bud(c0x + 14.4 * math.cos(math.radians(a)), c0y + 14.4 * math.sin(math.radians(a)), a, 1.05))
            for t in (4.0, 6.6, 9.2):
                pink.append(Point(c0x + t * math.cos(math.radians(a)), c0y + t * math.sin(math.radians(a))).buffer(0.95, 16))
        pink.append(box(c0x - 3.0, c0y - 3.0, c0x + 3.0, c0y + 3.0))
    pink = unary_union(pink).intersection(inner.union(outer.difference(inner).buffer(0)))
    main = unary_union(navy).difference(hole).difference(pink)
    base = outer.difference(hole)
    return base, main, pink


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    from PIL import Image
    out, ref = sys.argv[1], sys.argv[2]
    base, main, pink = build()
    for n, g in (("base", base), ("main", main), ("accent", pink)):
        open(f"{out}/emb_{n}.wkt", "w").write(g.wkt)
    def ex(x): return [p for p in (x.geoms if hasattr(x, "geoms") else [x]) if isinstance(p, Polygon) and p.area > 1e-4]
    def patch(g, col, alpha=1.0, tf=lambda x, y: (x, y)):
        v, c = [], []
        for p in ex(g):
            for r in [p.exterior] + list(p.interiors):
                xy = np.asarray(r.coords); xy = np.array([tf(a, b) for a, b in xy]); v += xy.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
        return PathPatch(MPath(v, c), facecolor=col, edgecolor="none", alpha=alpha)
    im = Image.open(ref).convert("RGB").crop((PX0 - 12, PY0 - 12, PX1 + 12, PY1 + 12)); w, h = im.size
    fig, axs = plt.subplots(1, 3, figsize=(3 * 4.4, 4.4 * h / w), dpi=110)
    axs[0].imshow(im)
    for ax, mode in ((axs[1], "mine"), (axs[2], "overlay")):
        if mode == "overlay": ax.imshow(im)
        tf = (lambda x, y: (x / K + 12, (H - y) / K + 12)) if mode == "overlay" else (lambda x, y: (x / K + 12, (H - y) / K + 12))
        if mode == "mine": ax.add_patch(patch(base, "#f4f4f2", tf=tf))
        ax.add_patch(patch(main, "#173d75", 0.55 if mode == "overlay" else 1, tf)); ax.add_patch(patch(pink, "#f08dbd", 0.6 if mode == "overlay" else 1, tf))
    for ax, t in zip(axs, ("reference", "my redraw (50 x %.0f mm)" % H, "overlay")):
        ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t, fontsize=11)
        ax.set_facecolor("#cfd4d8")
    fig.savefig(f"{out}/emb_preview.png", bbox_inches="tight", facecolor="#cfd4d8")
    print("size 50 x %.1f mm; areas base %.0f main %.0f pink %.0f" % (H, base.area, main.area, pink.area))
