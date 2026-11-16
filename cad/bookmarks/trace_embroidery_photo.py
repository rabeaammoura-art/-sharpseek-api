import sys, numpy as np, contourpy
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon, MultiPolygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
O, S = sys.argv[1], sys.argv[2]
im = Image.open(f"{S}/emb/ref.png").convert("RGB"); a = np.asarray(im).astype(float)
X0, X1, Y0, Y1 = 299, 786, 46, 1399
sub = a[Y0:Y1, X0:X1]; R, G, B = sub[..., 0], sub[..., 1], sub[..., 2]
K = 50.0 / (X1 - X0); H = (Y1 - Y0) * K
navy = ((B - R) > 35) & ((R + G + B) < 400) & (R < 120)
pink = ((R - G) > 55) & (R > 170)
for n, m in (("navy", navy), ("pink", pink)): print(n, "pixels", int(m.sum()))
def polys(mask, sigma, minarea_px):
    f = ndi.gaussian_filter(np.pad(mask.astype(float), 6), sigma)
    pts_l, off_l = contourpy.contour_generator(z=f, fill_type="OuterOffset").filled(0.5, 9)
    out = []
    for pts, offs in zip(pts_l, off_l):
        rings = [(pts[offs[i]:offs[i + 1]] - 6 + 0.5) for i in range(len(offs) - 1)]
        p = Polygon(rings[0], rings[1:]).buffer(0)
        if p.area >= minarea_px: out.append(p)
    g = unary_union(out)
    return affinity.affine_transform(g, [K, 0, 0, -K, 0, H])        # mm, y up
def ex(x): return [p for p in (x.geoms if hasattr(x, "geoms") else [x]) if isinstance(p, Polygon) and p.area > 1e-4]
nv = polys(navy, 1.6, 12); pk = polys(pink, 1.6, 10)
outer = box(0, 0, 50, H).buffer(-3, join_style=1).buffer(3, join_style=1)
nv = nv.intersection(outer)
pk = pk.intersection(outer)
hole_c = None
fr = max(ex(nv), key=lambda p: p.area)
ring_c = [Polygon(i) for i in fr.interiors if abs(Polygon(i).centroid.x - 25) < 3 and Polygon(i).centroid.y > H - 12]
hole = ring_c[0] if ring_c else Point(25, H - 5.6).buffer(1.9)
print("hole found:", bool(ring_c), "area", round(hole.area, 1))
nv = nv.buffer(0.12, join_style=1)                                   # thread lines get a bit thicker (printable)
pk = pk.buffer(0.1, join_style=1)
nv = nv.difference(hole)
pk = pk.difference(hole).difference(nv.buffer(-0.5, join_style=1).difference(pk.buffer(0.3)).buffer(0))   # pink keeps its own area
main = nv.difference(pk).buffer(-0.05, join_style=1).buffer(0.05, join_style=1)
acc = pk.intersection(outer)
base = outer.difference(hole)
thin = main.difference(main.buffer(-0.35, join_style=1).buffer(0.37, join_style=1))
print("main pieces", len(ex(main)), "area", round(main.area), "| thin (<0.7 mm) area", round(thin.area, 1), "| accent pieces", len(ex(acc)), "area", round(acc.area))
for n, g in (("base", base), ("main", main), ("accent", acc)): open(f"{O}/photo_{n}.wkt", "w").write(g.wkt)
def patch(g, col, tf):
    v, c = [], []
    for p in ex(g):
        for r in [p.exterior] + list(p.interiors):
            xy = np.array([tf(x, y) for x, y in np.asarray(r.coords)]); v += xy.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(v, c), facecolor=col, edgecolor="none")
tf = lambda x, y: (x / K, (H - y) / K)
w, h = X1 - X0, Y1 - Y0
fig, axs = plt.subplots(1, 3, figsize=(13.2, 13.2 * h / w / 3 * 1.02), dpi=110)
axs[0].imshow(im.crop((X0, Y0, X1, Y1)))
axs[1].add_patch(patch(base, "#f4f4f2", tf)); axs[1].add_patch(patch(main, "#173d75", tf)); axs[1].add_patch(patch(acc, "#f08dbd", tf))
axs[2].imshow(im.crop((X0, Y0, X1, Y1))); axs[2].add_patch(patch(main, "#00ff66", tf)); axs[2].add_patch(patch(acc, "#ffee00", tf)); axs[2].collections
for ax, t in zip(axs, ("photo", "traced from the photo", "overlay (green = navy, yellow = pink)")):
    ax.set_xlim(0, w); ax.set_ylim(h, 0); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t, fontsize=10)
axs[1].set_facecolor("#cfd4d8")
fig.savefig(f"{O}/photo_trace_preview.png", bbox_inches="tight", facecolor="#cfd4d8")
