"""Export the owner's flat nightcap-bear picture (two bears: with / without cloud; the lower one, WITHOUT cloud, is used) as the pose
"nightcap" of cad/poses/poses.json (same format as the other poses: px, y UP, origin = bottom centre of the bear).
Roles: body = light blue fill (body + cap), cream = white parts inside the bear (muzzle, cap band, pompom), navy = dark blue outline / eyes / nose,
yellow = none.   Usage: python cad/poses/nightcap_export.py <picture.png> [crop x0,y0,x1,y1]   (default crop = lower bear of the 1254 x 1254 picture)"""
import json, sys
from pathlib import Path
import contourpy
import matplotlib.colors as mc
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

src = sys.argv[1]
x0c, y0c, x1c, y1c = (int(v) for v in sys.argv[2].split(",")) if len(sys.argv) > 2 else (190, 640, 1010, 1240)
im = Image.open(src).convert("RGB").crop((x0c, y0c, x1c, y1c))
a = np.array(im).astype(float) / 255
H, S, V = (c for c in np.moveaxis(mc.rgb_to_hsv(a), -1, 0))
H = H * 360
white = (S < 0.14) & (V > 0.9)
dark = (S > 0.55) & (V < 0.6)
# background = white connected to the image border
border = np.zeros_like(white); border[0, :] = border[-1, :] = border[:, 0] = border[:, -1] = True
bg = ndi.binary_propagation(white & border, mask=white)
bear = ~bg
cream = bear & white
navy = dark
light = bear & ~white & ~dark
def polys(mask, sigma=1.3, min_area=12):
    m = ndi.gaussian_filter(mask.astype(float), sigma)
    gen = contourpy.contour_generator(z=m, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if pg.area >= min_area:
            out.append(pg)
    return unary_union(out) if out else Polygon()
body_g, cream_g, navy_g = polys(light | cream & False), polys(cream), polys(navy)
body_g = polys(bear & ~dark & ~cream | (bear & ndi.binary_dilation(dark, iterations=3) & ~cream))   # light blue incl. what is under the outline
ref = unary_union([body_g, navy_g, cream_g])
bx0, by0, bx1, by1 = ref.bounds
def norm(g):
    g = affinity.scale(g, 1, -1, origin=(0, 0))
    return affinity.translate(g, -(bx0 + bx1) / 2, by1)
roles = {}
for name, g in (("body", body_g), ("cream", cream_g), ("navy", navy_g), ("yellow", Polygon())):
    g = norm(g).simplify(0.6)
    polys_ = []
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        polys_.append([[(round(x, 1), round(y, 1)) for x, y in p.exterior.coords]] + [[(round(x, 1), round(y, 1)) for x, y in r.coords] for r in p.interiors])
    roles[name] = polys_
dst = Path(__file__).with_name("poses.json")
d = json.loads(dst.read_text())
d["nightcap"] = {"size": [bx1 - bx0, by1 - by0], "roles": roles}
dst.write_text(json.dumps(d))
print("nightcap pose:", round(bx1 - bx0), "x", round(by1 - by0), "px;", {k: len(v) for k, v in roles.items()})
