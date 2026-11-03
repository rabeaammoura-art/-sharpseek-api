"""Trace the workshop (house, shelves, car, lifts, tools, lettering, brake disc) from the reference picture into 3 colour classes.
Usage: python cad/wrench/workshop/trace_workshop.py <reference.jpg> <out_dir>  -> workshop_trace.json (orig pixel coords) + overlays
Classes (owner decision): black = panel (house silhouette), white = everything light/grey, orange = orange AND red.
The house silhouette and the disc circle are drawn by hand (the picture's wall is the same grey as the roof border)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import contourpy

ref, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = Image.open(ref).convert("RGB"); W, H = im.size; K = W / 2000.0
a = np.asarray(im).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
def D(x, y): return (x * K, y * K)                       # 2000-view -> original px
HOUSE = [(590, 92), (1037, -14), (1474, 92), (1474, 128), (1432, 128), (1432, 296), (655, 296), (655, 128), (590, 128)]
SHELF = [(526, 122), (655, 122), (655, 268), (526, 268)]
DISC = ((1330, 268), 102)
house = unary_union([Polygon([D(*p) for p in HOUSE]), Polygon([D(*p) for p in SHELF])])
disc = Point(D(*DISC[0])).buffer(DISC[1] * K, 64)
def mask_of(poly):
    im_ = Image.new("L", (W, H), 0); ImageDraw.Draw(im_).polygon(list(poly.exterior.coords), fill=1); return np.asarray(im_).astype(bool)
mh, md = mask_of(house), mask_of(disc)
orange = (r > 150) & (r - b > 85) & (r > g + 45)
neutral = (np.max(a, axis=2) - np.min(a, axis=2)) < 45
white = ((r + g + b) > 400) & ~orange & neutral
def disk(n): y, x = np.mgrid[-n:n + 1, -n:n + 1]; return x * x + y * y <= n * n
def clean(m):
    m = ndi.binary_opening(m, structure=disk(2)); m = ndi.binary_closing(m, structure=disk(2))
    lab, n = ndi.label(m); sz = ndi.sum(m, lab, range(1, n + 1))
    for i, s_ in enumerate(sz, 1):
        if s_ < 60: m[lab == i] = False
    return m
def polys(m):
    gen = contourpy.contour_generator(z=ndi.gaussian_filter(np.pad(m, 1).astype(float), 1.3))
    P = [Polygon([(x - 1, y - 1) for x, y in l]).buffer(0) for l in gen.lines(0.5) if len(l) > 6]
    P = [p for p in P if p.area > 60]; P.sort(key=lambda p: -p.area)
    res = []                                           # outer shapes first; a contour inside an existing shape is a hole
    for p in P:
        for i, q in enumerate(res):
            if q.contains(p): res[i] = q.difference(p); break
        else: res.append(p)
    return unary_union(res).simplify(0.9)
def rings(g):
    gs = [g] if g.geom_type == "Polygon" else list(g.geoms)
    return [{"outer": [list(map(float, c)) for c in p.exterior.coords], "holes": [[list(map(float, c)) for c in i.coords] for i in p.interiors]} for p in gs if p.area > 20]
res = {"image_size": [W, H], "K": K, "house": rings(house), "disc": {"c": list(D(*DISC[0])), "r": DISC[1] * K}}
caliper = (r > 105) & (r > g * 1.7) & (r - b > 55)            # red caliper, darker reds included
res["house_white"] = rings(polys(clean(white & mh))); res["house_orange"] = rings(polys(clean(orange & mh)))
res["disc_orange"] = rings(polys(clean(caliper & md)))              # the rotor itself is drawn parametrically in workshop.py
(out / "workshop_trace.json").write_text(json.dumps(res))
ov = im.copy(); d = ImageDraw.Draw(ov)
for key, col in (("house_white", (0, 255, 255)), ("house_orange", (0, 255, 0)), ("disc_orange", (255, 255, 0))):
    for p in res[key]:
        d.line(list(map(tuple, p["outer"])), fill=col, width=2)
        for h in p["holes"]: d.line(list(map(tuple, h)), fill=col, width=1)
for g_ in (house, disc): d.line(list(g_.exterior.coords) if g_.geom_type == "Polygon" else [], fill=(255, 0, 0), width=1)
ov.crop((int(500 * K), 0, int(1500 * K), int(400 * K))).save(out / "overlay_workshop.png")
print({k: len(v) for k, v in res.items() if isinstance(v, list)})
