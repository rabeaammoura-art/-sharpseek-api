"""Trace the car from the owner's second workshop picture (white pixels; dark windscreen/grille/lights become holes).
Usage: python cad/wrench/workshop/trace_car.py <picture.png> <out.json>   (the json is NOT committed: the picture's origin is unknown)"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from shapely.ops import unary_union
import contourpy

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB"); k = im.size[0] / 924.0
c = im.crop((int(400 * k), int(925 * k), int(650 * k), int(1095 * k))); c = c.resize((c.size[0] * 4, c.size[1] * 4), Image.LANCZOS)
a = np.asarray(c).astype(int); mn = a.min(axis=2); mx = a.max(axis=2)
m = (mn > 170) & (mx - mn < 40)
m[:240, :] = False                                           # the floating lamp bar above the car is not part of it
m = ndi.binary_opening(m, iterations=2); m = ndi.binary_closing(m, iterations=2)
lab, n = ndi.label(m); sz = ndi.sum(m, lab, range(1, n + 1))
for i, s in enumerate(sz, 1):
    if s < 1500: m[lab == i] = False
gen = contourpy.contour_generator(z=ndi.gaussian_filter(np.pad(m, 1).astype(float), 3.0))
P = [Polygon([(x - 1, y - 1) for x, y in l]).buffer(0) for l in gen.lines(0.5) if len(l) > 8]
P = [p for p in P if p.area > 1500]; P.sort(key=lambda p: -p.area)
res = []
for p in P:
    for i, q in enumerate(res):
        if q.contains(p): res[i] = q.difference(p); break
    else: res.append(p)
g = unary_union(res).simplify(1.2)
gs = [g] if g.geom_type == "Polygon" else list(g.geoms)
json.dump({"bounds": list(g.bounds), "polys": [{"outer": [list(map(float, c_)) for c_ in p.exterior.coords], "holes": [[list(map(float, c_)) for c_ in i.coords] for i in p.interiors]} for p in gs]}, open(out, "w"))
print("parts", len(gs), "bounds", [round(b) for b in g.bounds], "holes", sum(len(p.interiors) for p in gs))
