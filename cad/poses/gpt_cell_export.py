"""Trace the bear + cloud of one plaque of the owner's GPT sheet (2x2 colourways, one-colour bear + cloud outline) into a clean
vector asset for the generator layout "gpt".
Usage: python cad/poses/gpt_cell_export.py <sheet.png> <cell: x0 y0 x1 y1 of the plate frame> <out.json>
Everything blue (bear body, cloud outline) is ONE colour in print, so only that connected blue shape is exported; the cream muzzle,
inner ears, eyes and the cloud inside are holes (the cream base shows through). Units = plaque design units (300 = plate width,
y up, origin = plate centre)."""
import json
import sys
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon
from shapely.ops import unary_union

sheet = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
x0, y0, x1, y1 = map(int, sys.argv[2:6])
out = Path(sys.argv[6])
cx, cy, u = (x0 + x1) / 2, (y0 + y1) / 2, 300.0 / (x1 - x0)
body_blue = np.array(sheet[130, 320])                       # sample of the bear body colour (first plaque)
dist = np.linalg.norm(sheet - body_blue, axis=2)
blue = dist < 115                                           # also catches the lighter, thinner cloud outline
region = np.zeros(blue.shape, bool)
region[y0 + 20:y0 + 290, x0 + 80:x1 - 80] = True           # bear + cloud, not the frame / name / boxes
m = blue & region
lab, n = ndi.label(m, structure=np.ones((3, 3)))
shape = np.zeros(m.shape, bool)
NAME = (x0 + 175, y0 + 175, x1 - 165, y0 + 262)            # the name text inside the cloud is added later with the real font: skip it
for i, sl in enumerate(ndi.find_objects(lab), 1):
    bx0, bx1, by0, by1 = sl[1].start, sl[1].stop, sl[0].start, sl[0].stop
    inside_name = bx0 >= NAME[0] and bx1 <= NAME[2] and by0 >= NAME[1] and by1 <= NAME[3]
    if not inside_name and (lab[sl] == i).sum() > 150:
        shape |= lab == i
# nose + mouth (dark navy in the picture) sit inside the cream muzzle: print them in the same colour as the bear
navy = np.linalg.norm(sheet - np.array([16.0, 22.0, 28.0]), axis=2) < 75
yy, xx = np.mgrid[0:navy.shape[0], 0:navy.shape[1]]
muzzle = ((xx - (x0 + 291)) ** 2 + (yy - (y0 + 134)) ** 2) < 32 ** 2
shape |= navy & muzzle
f = ndi.gaussian_filter(shape.astype(float), 0.8)
gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
pts, offs = gen.filled(0.5, 1.5)
polys = []
for p, o in zip(pts, offs):
    rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
    if len(rings[0]) < 4:
        continue
    pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
    if pg.area > 30:
        polys.append(pg.simplify(0.35))
g = unary_union(polys)
res = []
for p in (g.geoms if hasattr(g, "geoms") else [g]):
    rings = [list(p.exterior.coords)] + [list(r.coords) for r in p.interiors]
    res.append([[(round((x - cx) * u, 2), round((cy - y) * u, 2)) for x, y in r] for r in rings])
out.write_text(json.dumps({"main": res}))
b = g.bounds
print("polygons", len(res), "bbox px", [round(v) for v in b], "-> units x", round((b[0] - cx) * u, 1), round((b[2] - cx) * u, 1), "y", round((cy - b[3]) * u, 1), round((cy - b[1]) * u, 1))
