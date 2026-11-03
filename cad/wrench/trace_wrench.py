"""Trace the wrench silhouette (outer outline, ring hole with teeth, orange band) from the reference picture.
Usage: python cad/wrench/trace_wrench.py <reference.jpg> <out_dir>   -> wrench_trace.json (pixel coords) + overlay.png
The workshop and hooks are cut out of the mask (they are separate parts); the bar behind the workshop is filled."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from shapely.ops import unary_union
import contourpy

ref, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = Image.open(ref).convert("RGB"); W, H = im.size
a = np.asarray(im).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
K = W / 2000.0                                    # my measurements below are in a 2000 px wide view
def X(v): return int(v * K)
orange = (r > 190) & (g > 70) & (g < 200) & (b < 110) & (r - b > 110)
dark = (r + g + b) < 175
yy0, xx0 = np.mgrid[0:H, 0:W]
dark |= ((r + g + b) < 380) & (yy0 < int(300 * K))      # lighter grey outer border on the top side (no shadow there)
m = dark | orange
m = ndi.binary_closing(m, iterations=4)
yy, xx = np.mgrid[0:H, 0:W]
ZX0, ZX1 = X(512), X(1440)                         # bar zone (workshop sits here)
BT, BB = X(250), X(398)                            # bar top (hidden behind the workshop) / bar bottom
zone = (xx >= ZX0) & (xx < ZX1)
def edge(col, top=True):
    ys = np.where(m[:, col])[0]; ys = ys[(ys > X(150)) & (ys < X(480))]
    return ys.min() if top else ys.max()
tl, tr_ = X(239), X(252)                             # bar top line between the necks (hidden behind the workshop)
bl, br_ = BB, BB
m[zone] = False
for col in range(ZX0, ZX1):
    t = tl + (tr_ - tl) * (col - ZX0) / (ZX1 - ZX0)
    m[int(t):BB, col] = True
c2 = X(1535); e2 = edge(c2, top=False); print("e2", e2, "BB", BB, "tl", tl, "tr", tr_)                  # lower right neck: ease from the bar bottom to the ring edge (hook 5 is cut out)
for col in range(ZX1, c2):
    b = int(BB + (e2 - BB) * ((col - ZX1) / (c2 - ZX1)) ** 2)
    ys = np.where(m[:BB, col])[0]; ys = ys[ys > X(150)]
    m[BB:, col] = False; m[ys.min():b, col] = True      # solid from the neck top edge down (no slit at hook 5)
lab, n = ndi.label(m); sizes = ndi.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sizes)))
holes = ndi.binary_fill_holes(m) & ~m
hl, hn = ndi.label(holes)
for i in range(1, hn + 1):                         # keep only the big hole (ring); fill small texture holes
    if (hl == i).sum() < 20000: m[hl == i] = True
dy, dx = np.mgrid[-9:10, -9:10]; m = ndi.binary_opening(m, structure=(dx * dx + dy * dy) <= 81)   # removes thin workshop slivers
# contours
gen = contourpy.contour_generator(z=ndi.gaussian_filter(np.pad(m, 1).astype(float), 4.0))
lines = gen.lines(0.5)
polys = [Polygon([(x - 1, y - 1) for x, y in l]) for l in lines if len(l) > 20]
polys = [p.buffer(0).simplify(1.3) for p in polys if p.area > 500]
polys.sort(key=lambda p: -p.area)
outer = polys[0]; shape = Polygon(outer.exterior.coords)          # the toothed ring hole is parametric (RING below), not traced
# orange band: keep the band line, drop the workshop's orange (above the bar line in the zone)
om = orange.copy(); om[(xx >= X(545)) & (xx < ZX1) & (yy < X(292))] = False
rows = om[:, X(1222)].copy(); om[:, X(1222):ZX1 + X(6)] |= rows[:, None]       # band continues hidden under the brake disc
om = ndi.binary_closing(om, iterations=2); om = ndi.binary_opening(om, iterations=1)
ol, on_ = ndi.label(om); oranges = []
for i in range(1, on_ + 1):
    if (ol == i).sum() < 1500: continue
    gen = contourpy.contour_generator(z=ndi.gaussian_filter(np.pad(ol == i, 1).astype(float), 2.0))
    for l in gen.lines(0.5):
        p = Polygon([(x - 1, y - 1) for x, y in l]).buffer(0)
        if p.area > 800: oranges.append(p.simplify(1.0))
# the ring's orange band is a closed loop (has a hole): rebuild holes by difference of nested polygons
oranges.sort(key=lambda p: -p.area); bands = []
for p in oranges:
    for q in bands:
        if q.contains(p): bands[bands.index(q)] = q.difference(p); break
    else: bands.append(p)
def rings(poly):
    return {"outer": [list(map(float, c)) for c in poly.exterior.coords],
            "holes": [[list(map(float, c)) for c in i.coords] for i in poly.interiors]}
res = {"image_size": [W, H], "outline": rings(shape), "orange": [rings(p) for p in bands if p.area > 800],
       "screws_px": [[X(420), X(322)], [X(1567), X(328)]], "hooks_px_x": [X(600), X(820), X(1030), X(1240), X(1465)],
       "bar_top_px": BT, "bar_bottom_px": BB,
       # ring head measured on a 2x crop of the picture (2000 px-wide view units): centre, tooth tip/root radius, plate opening
       "ring": {"cx": X(1743.6), "cy": X(291), "r_tip": 108.6 * K, "r_root": 128 * K, "r_open": 145 * K, "teeth": 18}}
(out / "wrench_trace.json").write_text(json.dumps(res))
ov = im.copy(); d = ImageDraw.Draw(ov)
d.line(list(map(tuple, res["outline"]["outer"])), fill=(255, 0, 255), width=3)
for h in res["outline"]["holes"]: d.line(list(map(tuple, h)), fill=(0, 255, 255), width=3)
for o in res["orange"]:
    d.line(list(map(tuple, o["outer"])), fill=(0, 255, 0), width=2)
    for h in o["holes"]: d.line(list(map(tuple, h)), fill=(0, 255, 0), width=2)
ov.save(out / "overlay.png"); print("outer pts", len(res["outline"]["outer"]), "holes", len(res["outline"]["holes"]), "orange", len(res["orange"]))
