"""Trace the silver hub ring + spokes (with their holes: pad, buttons) from the reference. Local json output.
Usage: trace_wheel_inside.py ref.png out.json"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
from shapely.geometry import Polygon
from shapely.ops import unary_union

im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
mn, mxv = im.min(axis=2), im.max(axis=2)
H, W = mn.shape
yy, xx = np.mgrid[0:H, 0:W]
roi = (xx > 428) & (xx < 712) & (yy > 150) & (yy < 400)
m = (mn > 100) & ((mxv - mn) < 55) & roi
m = ndi.binary_opening(m, iterations=1)
m = ndi.binary_closing(m, iterations=2)
lab, n = ndi.label(m)
keep = np.zeros_like(m)
for i in range(1, n + 1):
    if (lab == i).sum() > 250:
        keep |= lab == i
sm = ndi.gaussian_filter(keep.astype(float), 1.3)
polys = []
for c in measure.find_contours(np.pad(sm, 1), 0.5):
    c = c - 1
    if len(c) > 12:
        polys.append(Polygon([(x, y) for y, x in c]).buffer(0))
# even-odd: sort by area, subtract contained rings
polys.sort(key=lambda p: -p.area)
res = None
for p in polys:
    if res is None: res = p
    elif res.contains(p.representative_point()): res = res.difference(p)
    else: res = res.union(p)
res = res.simplify(0.7)
print(res.geom_type, res.area, res.bounds)
geoms = list(res.geoms) if hasattr(res, "geoms") else [res]
json.dump([{"ext": [list(q) for q in g.exterior.coords], "holes": [[list(q) for q in h.coords] for h in g.interiors]} for g in geoms], open(sys.argv[2], "w"))
