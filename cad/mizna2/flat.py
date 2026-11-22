"""Mizna v2 coaster (95 mm): clean parametric flat 2D layout from the owner's reference picture (picture not in git).
Coordinates are reference-picture pixels (circle centre 269,213, R 201 px = 47.5 mm) converted with one scale.
Usage: python cad/mizna2/flat.py [reference.png]  -> cad/out/mizna2/flat.png (+ overlay.png when a picture is given)"""
import math, sys
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import newborn_plaque as npq  # Font + Arabic shaping (harfbuzz)

CX, CY, RPX, R = 269.0, 213.0, 201.0, 47.5
K = R / RPX
FONTS = Path(__file__).resolve().parents[1] / "fonts"
COL = {"body": "#F4DCC8", "brown": "#5B3A22", "lilac": "#D2A9D6", "olive": "#A98C52"}


def mm(p):
    return ((p[0] - CX) * K, (CY - p[1]) * K)


def poly_px(pts):
    return Polygon([mm(p) for p in pts])


def leaf(base, tip, width, bulge=0.5):
    """pointed leaf (lens) between base and tip (px), width in px."""
    (bx, by), (tx, ty) = base, tip
    dx, dy = tx - bx, ty - by
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    pts = []
    for side in (1, -1):
        for i in range(0, 21):
            t = i / 20
            w = side * width / 2 * math.sin(math.pi * t) ** 0.8 * (1 + bulge * (0.5 - t) * 0.6)
            pts.append((bx + dx * t + nx * w, by + dy * t + ny * w))
        if side == 1:
            pts = pts[:]  # continue back along the other side
            pts_a = pts
            pts = []
    side1 = pts_a
    side2 = pts[::-1]
    return Polygon([mm(p) for p in side1 + side2]).buffer(0)


def stem(pts, w):
    return LineString([mm(p) for p in pts]).buffer(w * K / 2, cap_style=1, join_style=1)


def drop(cx, cy, h, w):
    """teardrop, tip up, centre (cx,cy) px."""
    pts = []
    for i in range(0, 41):
        a = math.pi * i / 40
        pts.append((cx + math.cos(a) * w / 2, cy + h * 0.18 + math.sin(a) * w / 2))
    pts = [(x, y) for x, y in pts]
    tip = (cx, cy - h * 0.5)
    poly = Polygon([mm(tip)] + [mm(p) for p in pts[::-1]]).convex_hull
    return poly.buffer(0)


def cloud(box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # bumps: (cx, cy, r) in fractions of the box
    bumps = [(0.17, 0.66, 0.20), (0.36, 0.42, 0.24), (0.58, 0.30, 0.30), (0.80, 0.52, 0.22), (0.86, 0.68, 0.18)]
    parts = [Point(mm((x0 + fx * w, y0 + fy * h))).buffer(fr * w * K, 48) for fx, fy, fr in bumps]
    body = unary_union(parts + [Polygon([mm((x0 + 0.17 * w, y0 + 0.66 * h)), mm((x0 + 0.86 * w, y0 + 0.68 * h)),
                                          mm((x0 + 0.86 * w, y1)), mm((x0 + 0.17 * w, y1))])])
    body = body.buffer(0)
    return body


def fit_text(text, font_key, bbox_px, scale_mode="width"):
    f = npq.Font(FONTS / font_key)
    g, adv = npq.shape_run(f, text, 100, 1 if False else "rtl", "Arab")
    x0, y0, x1, y1 = bbox_px
    gx0, gy0, gx1, gy1 = g.bounds
    tw, th = (x1 - x0) * K, (y1 - y0) * K
    s = min(tw / (gx1 - gx0), th / (gy1 - gy0)) if scale_mode == "fit" else tw / (gx1 - gx0)
    g = affinity.scale(g, s, s, origin=(0, 0))
    gx0, gy0, gx1, gy1 = g.bounds
    cxm, cym = mm(((x0 + x1) / 2, (y0 + y1) / 2))
    return affinity.translate(g, cxm - (gx0 + gx1) / 2, cym - (gy0 + gy1) / 2)


def flower(c, size, rot):
    """tulip-like bloom: 3 petals + calyx, c px centre of the bloom, rot degrees (0 = up)."""
    cx, cy = c
    petals = []
    for ang, sc in ((-40, 0.8), (-14, 1.0), (14, 1.0), (40, 0.8)):
        a = math.radians(ang + rot)
        ln, wd = size * 0.62 * sc, size * 0.30
        ctr = (cx + math.sin(a) * ln * 0.42, cy - math.cos(a) * ln * 0.42)
        petals.append(leaf((cx + math.sin(a) * 0 , cy - math.cos(a) * 0), (cx + math.sin(a) * ln, cy - math.cos(a) * ln), wd * 1.05, 0.2))
    bloom = unary_union(petals)
    a = math.radians(rot)
    cal = leaf((cx - math.sin(a) * size * 0.50, cy + math.cos(a) * size * 0.50), (cx + math.sin(a) * size * 0.02, cy - math.cos(a) * size * 0.05), size * 0.34, 0.0)
    return bloom, cal


def build():
    L = {k: [] for k in COL if k != "body"}
    # ---- text
    title = fit_text("مزنة", "NotoKufiArabic-Bold.ttf", (197, 117, 337, 204))
    sub = fit_text("رِقَّةً كالمطر", "NotoKufiArabic-Regular.ttf", (186, 212, 364, 272))
    L["brown"] += [title, sub]
    # ---- cloud: outline brown 0.8 mm, fill lilac, drops lilac
    cl = cloud((311, 61, 402, 108))
    ring = cl.difference(cl.buffer(-0.8))
    L["brown"].append(ring)
    L["lilac"].append(cl.buffer(-0.8))
    for (x, y) in [(336, 122), (370, 125), (384, 118), (354, 143), (391, 144), (372, 164)]:
        L["lilac"].append(drop(x, y, 17, 9))
    # ---- left sprig (olive leaves, brown stem)
    o = (110, 260)
    P = lambda cx, cy: (o[0] + cx / 5, o[1] + cy / 5)
    L["brown"].append(stem([P(495, 545), P(380, 460), P(280, 370), P(180, 240)], 2.6))
    for base, tip, w in [((185, 240), (85, 90), 78), ((268, 330), (235, 172), 62), ((265, 365), (105, 270), 66), ((375, 445), (345, 285), 62)]:
        L["olive"].append(leaf(P(*base), P(*tip), w / 5))
    # ---- right sprig (lilac blooms, olive leaves/calyx, brown stem)
    o = (300, 255)
    P = lambda cx, cy: (o[0] + cx / 5, o[1] + cy / 5)
    L["brown"].append(stem([P(45, 590), P(200, 480), P(320, 370), P(435, 235)], 2.4))
    L["brown"].append(stem([P(235, 395), P(225, 440), P(215, 475)], 2.2))
    L["brown"].append(stem([P(345, 275), P(335, 330), P(320, 370)], 2.2))
    for base, tip, w in [((375, 360), (480, 315), 85), ((258, 470), (385, 435), 80)]:
        L["olive"].append(leaf(P(*base), P(*tip), w / 5))
    for c, sz, rot in [((230, 305), 150, -5), ((350, 220), 130, 0), ((485, 160), 190, 20)]:
        b, cal = flower(P(*c), sz / 5, rot)
        L["lilac"].append(b)
        L["olive"].append(cal)
    return L


def render(L, path, S=12, overlay=None):
    from PIL import Image, ImageDraw
    N = int(2 * R * S) + 40
    im = Image.new("RGB", (N, N), "#ffffff")
    d = ImageDraw.Draw(im)
    c = N / 2
    d.ellipse([c - R * S, c - R * S, c + R * S, c + R * S], fill=COL["body"])

    for k in ("olive", "lilac", "brown"):
        m = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(m)
        for g in L[k]:
            for p in (g.geoms if hasattr(g, "geoms") else [g]):
                if p.is_empty or p.geom_type != "Polygon":
                    continue
                md.polygon([(c + x * S, c - y * S) for x, y in p.exterior.coords], fill=255)
                for h in p.interiors:
                    md.polygon([(c + x * S, c - y * S) for x, y in h.coords], fill=0)
        im.paste(COL[k], mask=m)
    im.save(path)
    if overlay:
        ref = Image.open(overlay).convert("RGB")
        s = RPX / 1.0
        box = (CX - RPX, CY - RPX, CX + RPX, CY + RPX)
        crop = ref.crop(tuple(int(v) for v in box)).resize((N - 40, N - 40))
        base = Image.new("RGB", (N, N), "#fff")
        base.paste(crop, (20, 20))
        ov = Image.blend(base, im, 0.5)
        ov.save(str(path).replace("flat", "overlay"))


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "out" / "mizna2"
    out.mkdir(parents=True, exist_ok=True)
    L = build()
    render(L, out / "flat.png", overlay=sys.argv[1] if len(sys.argv) > 1 else None)
    for k, v in L.items():
        print(k, [round(g.area, 1) for g in v])
