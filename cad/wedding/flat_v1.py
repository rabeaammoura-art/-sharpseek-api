"""Wedding heart plaque, flat 2D preview v1 (backlit idea, same as the newborn glow_cap plaque).

Usage:  python cad/wedding/flat_v1.py <reference.png> <out_dir> [--size 280]

The reference picture (owner's GPT image, 1254 x 1254) is third-party: it is only passed as an argument and nothing
traced from it is committed. Only the couple silhouette + veil are traced (big shapes); everything else is parametric
(heart, banner, hearts, rings, lines) and the text uses the real fonts of the generator.
Layers: gold (frame, hearts, lines, banner outline, rings), navy (couple, veil, names, date), cream (translucent
back-lit background, banner fill). Picture px -> mm with ONE scale factor.
"""
import argparse
import math
import sys
from pathlib import Path

import contourpy
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from PIL import Image
from scipy import ndimage as ndi
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import newborn_plaque as n  # noqa: E402

# ---- picture geometry (px), measured on the 1254 x 1254 reference -----------------------------------------------
AX = 625.0                      # symmetry axis of the heart
HX0, HX1, HY0, HY1 = 35.0, 1215.0, 25.0, 1215.0
FRAME_PX = 48.0


def px_to_mm_factory(size):
    s = size / (HX1 - HX0)
    cx, cy = AX, (HY0 + HY1) / 2

    def to_mm(g):
        return affinity.translate(affinity.scale(g, s, -s, origin=(0, 0)), -cx * s, cy * s)
    return s, to_mm


HEART_TAIL = [(1193, 520), (1170, 580), (1132, 640), (1094, 700), (1045, 760), (1000, 820), (950, 885), (895, 945), (835, 1005),
              (750, 1100), (625, 1215)]


def heart_px():
    """Outer heart: right lobe = ellipse arc (smooth, round top), lower side = points measured on the picture, mirrored."""
    from scipy.interpolate import splprep, splev
    cx, cy, rx, ry = 905.0, 380.0, 305.0, 350.0
    arc = []
    for t in np.linspace(math.radians(-134), math.radians(8), 40):      # from near the cleft over the top to the side
        arc.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    pts = np.array([(625, 212)] + arc + HEART_TAIL, float)
    tck, _ = splprep([pts[:, 0], pts[:, 1]], s=30.0, k=3)
    xs, ys = splev(np.linspace(0, 1, 500), tck)
    right = list(zip(xs, ys))
    left = [(2 * AX - x, y) for x, y in right[::-1]]
    return Polygon(right + left[1:]).buffer(0)


def parab_edge(x0, x1, y_mid, y_end, n_pts=40):
    xs = np.linspace(x0, x1, n_pts)
    k = (y_end - y_mid) / ((x0 - AX) ** 2)
    return [(x, y_mid + k * (x - AX) ** 2) for x in xs]


def banner_px():
    top = parab_edge(278, 972, 733, 808)
    bot = parab_edge(335, 915, 888, 938)
    band = Polygon(top + bot[::-1]).buffer(6, join_style=1).buffer(-6, join_style=1)
    tail_l = Polygon([(195, 885), (300, 845), (345, 945), (405, 968), (330, 1002), (215, 1032), (262, 950)])
    tail_r = affinity.scale(tail_l, -1, 1, origin=(AX, 0))
    return band, tail_l, tail_r


def trace_dark(ref, inside, sigma=1.6, min_area=30):
    """Dark navy mask of the couple + veil from the reference, as shapely polygons in px."""
    rgb = np.asarray(Image.open(ref).convert("RGB")).astype(int)
    H, W, _ = rgb.shape
    dark = (rgb[..., 0] < 85) & (rgb[..., 1] < 85) & (rgb[..., 2] < 110)
    zone = np.zeros((H, W), bool)
    zone[90:768, 150:705] = True            # couple
    zone[195:360, 470:1095] = True          # veil
    zone[285:445, 985:1022] = False         # alef of the name
    zone[360:450, 670:990] = False          # rest of the name
    zone[395:455, 540:650] = False          # small hearts shadows
    from PIL import ImageDraw
    msk = Image.new("L", (W, H), 0)
    ImageDraw.Draw(msk).polygon(list(inside.buffer(-4).exterior.coords), fill=255)
    m = dark & zone & (np.asarray(msk) > 0)
    lab, nl = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, nl + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= min_area])
    f = ndi.gaussian_filter(keep.astype(float), sigma)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if pg.area >= min_area:
            out.append(pg)
    return unary_union(out)


def fit_text(segments, lang, rtl, cx, cy, width):
    g, w = n.text_line(segments, lang, rtl)
    s = width / w
    g = affinity.scale(g, s, s, origin=(0, 0))
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def small_heart(cx, cy, w):
    h = n.heart(0, 0, w)
    x0, y0, x1, y1 = h.bounds
    return affinity.translate(h, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def line_px(x0, x1, y, t):
    return LineString([(x0 + t / 2, y), (x1 - t / 2, y)]).buffer(t / 2, 8)


def build(ref, size):
    s, to_mm = px_to_mm_factory(size)
    # ---- everything below is built in PIXEL space with y DOWN, then converted -------------------------------------
    outer = heart_px()
    # frame is thick (48 px) on the sides and thinner (34 px) on the lower diagonals, like the picture
    bands = []
    for y0 in range(0, 1260, 30):
        d = float(np.interp(y0 + 15, [520, 800], [FRAME_PX, 34.0]))
        bands.append(outer.buffer(-d, join_style=2, mitre_limit=6).intersection(box(0, y0, 1254, y0 + 30)))
    inner = unary_union(bands).buffer(2, join_style=1).buffer(-2, join_style=1)
    band, tail_l, tail_r = banner_px()
    ban_fill = unary_union([band, tail_l, tail_r])
    line_w = 3.0 / s                                   # banner outline 3 mm
    ban_out = unary_union([p.buffer(line_w / 2, join_style=1).difference(p.buffer(-line_w / 2, join_style=1))
                           for p in (tail_l, tail_r)]).difference(band)
    ban_out = unary_union([ban_out, band.buffer(line_w / 2, join_style=1).difference(band.buffer(-line_w / 2, join_style=1))])

    # ---- small gold things (picture px; y down -> flip sign for the heart helper) -----------------------------------
    def ph(cx, cy, w):                                  # heart in px space, point DOWN
        h = affinity.scale(n.heart(0, 0, w), 1, -1, origin=(0, 0))
        x0, y0, x1, y1 = h.bounds
        return affinity.translate(h, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)
    deco_hearts = unary_union([ph(890, 150, 68), ph(810, 198, 58), ph(728, 232, 50), ph(573, 392, 52), ph(622, 445, 44)])
    mid_heart = ph(847, 497, 118)
    ra = Point(587, 1052).buffer(46, 48).difference(Point(587, 1052).buffer(34, 48))
    rb = Point(663, 1052).buffer(46, 48).difference(Point(663, 1052).buffer(34, 48))
    gap = 4.0                                             # ~0.9 mm: shows which ring is over / under
    top, bot = Point(625, 1052 - 12.5).buffer(17), Point(625, 1052 + 12.5).buffer(17)
    rings = unary_union([ra.difference(rb.buffer(gap).intersection(top)), rb.difference(ra.buffer(gap).intersection(bot))])
    # bottom lines: only as long as the heart allows between the frame and the rings
    y_l = 1004
    row = inner.intersection(LineString([(0, y_l), (1254, y_l)]))
    xl, xr = row.bounds[0], row.bounds[2]
    lines_b = [line_px(a_, b_, y_l, 8) for a_, b_ in [(xl + 16, 541 - 10), (709 + 10, xr - 16)] if b_ - a_ >= 24]
    lines = unary_union([line_px(630, 775, 497, 9), line_px(918, 1055, 497, 9)] + lines_b)

    # ---- text: font geometry is y UP, so build it in mm space afterwards -------------------------------------------
    navy_trace = trace_dark(ref, inner.buffer(-5))

    gold_px = unary_union([outer.difference(inner), deco_hearts, mid_heart, lines, rings])
    gold_px = unary_union([gold_px.difference(ban_fill), ban_out])
    navy_px = navy_trace.difference(ban_fill)

    gold = to_mm(gold_px)
    navy = to_mm(navy_px)
    cream_px = unary_union([inner, ban_fill])
    cream = to_mm(cream_px)

    # text in mm (y up): centres measured in px
    def tmm(px, py):
        return to_mm(Point(px, py)).coords[0]
    texts = []
    for segs, kind, lang, (cx, cy), wpx in [
        ([("أحمد", 40, "name")], "name", "ar", (845, 365), 330),
        ([("سارة", 40, "name")], "name", "ar", (852, 610), 335),
        ([("يوم الزواج", 40, "name")], "name", "ar", (622, 830), 485),
        ([("15/06/2026", 40, "num")], "num", "en", (622, 960), 335),
    ]:
        x, y = tmm(cx, cy)
        texts.append(fit_text(segs, lang, lang == "ar", x, y, wpx * s))
    amp = fit_text([("&", 40, "num")], "en", False, *tmm(847, 500), 13.0)
    navy = unary_union([navy] + texts)
    cream_marks = amp                                    # cream "&" on the gold heart
    gold = gold.difference(cream_marks).difference(navy)
    navy = navy.difference(to_mm(deco_hearts.buffer(3)))
    navy = unary_union([q for q in (navy.geoms if hasattr(navy, 'geoms') else [navy]) if q.area >= 12.0])
    return dict(gold=gold, navy=navy, cream=cream, amp=cream_marks, outer=to_mm(outer), inner=to_mm(inner), s=s)


def patch(g, **kw):
    out = []
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)
            verts += c
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
        out.append(PathPatch(MPath(verts, codes), **kw))
    return out


def render(L, path, ref=None):
    fig, ax = plt.subplots(figsize=(9, 9), dpi=140)
    ax.set_facecolor("#3b3330")
    if ref is not None:
        s = L["s"]
        im = np.asarray(Image.open(ref).convert("RGB"))
        ex = [-AX * s, (im.shape[1] - AX) * s, -(im.shape[0] - (HY0 + HY1) / 2) * s, (HY0 + HY1) / 2 * s]
        ax.imshow(im, extent=ex, zorder=0)
        a = 0.55
    else:
        a = 1.0
    for g, col, z in [(L["cream"], "#fff1c9", 1), (L["gold"], "#d9a21b", 2), (L["navy"], "#161d3c", 3), (L["amp"], "#fff1c9", 4)]:
        for p in patch(g, fc=col, ec="none", alpha=a, zorder=z):
            ax.add_patch(p)
    x0, y0, x1, y1 = L["outer"].bounds
    ax.set_xlim(x0 - 6, x1 + 6)
    ax.set_ylim(y0 - 6, y1 + 6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="#3b3330")
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("out")
    ap.add_argument("--size", type=float, default=280)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    L = build(a.ref, a.size)
    render(L, out / "flat_v1.png")
    render(L, out / "flat_v1_overlay.png", ref=a.ref)
    x0, y0, x1, y1 = L["outer"].bounds
    print(f"heart {x1 - x0:.1f} x {y1 - y0:.1f} mm")
