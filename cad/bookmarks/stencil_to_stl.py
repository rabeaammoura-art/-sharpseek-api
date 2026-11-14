"""Black/white stencil picture (e.g. from GPT with cad/bookmarks/gpt_prompt) -> cut-out bookmark STL.

    python cad/bookmarks/stencil_to_stl.py picture.png OUT_DIR --name rose [--width 45] [--thick 1.0] [--grow 0.0]

Black = printed, white = cut through. The outline is traced on a smoothed copy (no pixel steps), scaled so the black
bounding box is --width mm wide, loose islands are tied in with small bridges (red circles in the preview), --grow thickens every black shape (mm per side).
Writes NAME.stl and NAME_preview.png and prints the checks (pieces, thin necks, narrow gaps, size).
"""
import argparse
import numpy as np
import contourpy
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

ap = argparse.ArgumentParser()
ap.add_argument("picture"); ap.add_argument("out")
ap.add_argument("--name", default="bookmark"); ap.add_argument("--width", type=float, default=45.0)
ap.add_argument("--thick", type=float, default=1.0); ap.add_argument("--grow", type=float, default=0.0)
ap.add_argument("--colour", default="#e6b3ad")
a = ap.parse_args()

im = Image.open(a.picture).convert("L")
im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
dark = ndi.gaussian_filter(1.0 - np.asarray(im, float) / 255.0, 1.3)
dark = np.pad(dark, 4)                                                # so shapes touching the border close
polys = []
gen = contourpy.contour_generator(z=dark, fill_type="OuterOffset")
pts_list, off_list = gen.filled(0.5, 5.0)
for pts, offs in zip(pts_list, off_list):
    rings = [pts[offs[i]:offs[i + 1]] for i in range(len(offs) - 1)]
    p = Polygon(rings[0], rings[1:]).buffer(0)
    if not p.is_empty:
        polys.append(p)
g = unary_union(polys)
x0, y0, x1, y1 = g.bounds
k = a.width / (x1 - x0)
from shapely import affinity
g = affinity.affine_transform(g, [k, 0, 0, -k, -x0 * k, y1 * k])      # mm, y up, origin at the lower-left corner
g = g.simplify(0.03)
if a.grow:
    g = g.buffer(a.grow, join_style=1)
# widen white cut lines that are too narrow to print open (under 0.5 mm) by 0.1 mm per side
narrow = g.buffer(0.25, join_style=1).buffer(-0.25, join_style=1).difference(g)
g = g.difference(narrow.buffer(0.1, join_style=1)).buffer(0)
parts = sorted(g.geoms if isinstance(g, MultiPolygon) else [g], key=lambda p: -p.area)
main, loose = parts[0], [p for p in parts[1:] if p.area >= 2.0]
# islands (e.g. petals drawn with a white line all around) are tied to the body with two small bridges each
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
bridges = []
todo = list(loose)
while todo:
    todo.sort(key=lambda p: p.distance(main))
    isl = todo.pop(0)
    p1, p2 = nearest_points(isl, main)
    made = [LineString([p1, p2])]
    ring = isl.exterior
    cand = [ring.interpolate(s) for s in np.linspace(0, ring.length, 200, endpoint=False)]
    cand = [q for q in cand if q.distance(main) < 1.6 and q.distance(p1) > 0.3 * ring.length / 3.14]
    if cand:
        q = max(cand, key=lambda q: q.distance(p1))
        made.append(LineString(nearest_points(q, main)))
    for ln in made:
        ext = affinity.scale(ln, 1 + 1.2 / max(ln.length, 0.05), 1 + 1.2 / max(ln.length, 0.05))
        bridges.append(ext.buffer(0.55, cap_style=2))
    main = unary_union([main, isl] + bridges[-len(made):]).buffer(0)
    if isinstance(main, MultiPolygon):
        main = max(main.geoms, key=lambda p: p.area)
print(f"islands tied in with bridges: {len(loose)} (bridges {len(bridges)})")
print(f"size {main.bounds[2] - main.bounds[0]:.1f} x {main.bounds[3] - main.bounds[1]:.1f} mm, thickness {a.thick} mm, windows {len(main.interiors)}")
for lim in (0.6, 0.8, 1.0):
    thin = main.difference(main.buffer(-lim / 2, join_style=1).buffer(lim / 2 + 0.02, join_style=1))
    spots = [p for p in (thin.geoms if hasattr(thin, "geoms") else [thin]) if p.area > 0.05]
    print(f"black thinner than {lim} mm: {sum(p.area for p in spots):.1f} mm2 in {len(spots)} spots")
closed = main.buffer(0.25, join_style=1).buffer(-0.25, join_style=1).difference(main)
print(f"white gaps narrower than 0.5 mm: {closed.area:.1f} mm2")
# is it still one piece if every neck under 0.8 mm breaks?
core = main.buffer(-0.4, join_style=1)
print("pieces if necks under 0.8 mm break:", len(core.geoms) if isinstance(core, MultiPolygon) else 1)

import trimesh
m = trimesh.creation.extrude_polygon(main, a.thick)
m.export(f"{a.out}/{a.name}.stl")
print(f"watertight {m.is_watertight}, volume {m.volume / 1000:.2f} cm3")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
v, c = [], []
for ring in [main.exterior] + list(main.interiors):
    xy = np.asarray(ring.coords); v += xy.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
fig, ax = plt.subplots(figsize=(4.4, 13), dpi=140)
ax.add_patch(PathPatch(MPath(v, c), facecolor=a.colour, edgecolor="#00000040", linewidth=0.4))
for b_ in bridges:
    ax.plot(*b_.centroid.xy, "o", ms=9, mfc="none", mec="#d00000", mew=1.2)
ax.set_xlim(-3, main.bounds[2] + 3); ax.set_ylim(-3, main.bounds[3] + 3); ax.set_aspect("equal"); ax.axis("off")
fig.savefig(f"{a.out}/{a.name}_preview.png", bbox_inches="tight", facecolor="#f7f5f0")
