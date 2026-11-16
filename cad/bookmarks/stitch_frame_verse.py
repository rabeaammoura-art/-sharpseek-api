import sys, json, zipfile, os, numpy as np, trimesh
sys.path.insert(0, "/home/user/-sharpseek-api/cad")
import newborn_plaque as npq
from threemf import write_bambu_3mf, build_project_settings
from shapely import affinity
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
S, O = sys.argv[1], sys.argv[2]
G = np.load(f"{O}/stitch_grid_182_v4.npy"); H, NW = G.shape
G[15:158, 9:41] = 0                                                  # empty the inside (keep frame, zigzag, corners)
G[158:168, 13:37] = 0                                                # leftovers of the lower star
sub = G[15:168, 6:44]; sub[sub == 2] = 0                             # stray pink cells beside the frame
G[168:177, 19:32] = 0                                              # the small cross at the bottom (owner's mark)
font = npq.Font(sys.argv[4])
lines = ["ألا بذكر الله تطمئن القلوب"]
shapes = [npq.shape_run(font, t, 10.0, "rtl", "Arab")[0] for t in lines]
LEN, HGT, GAP = 124.0, 29.0, 0.0
k = min(min(LEN / (g.bounds[2] - g.bounds[0]), HGT / (g.bounds[3] - g.bounds[1])) for g in shapes)
print("scale", round(k, 2), [round((g.bounds[2] - g.bounds[0]) * k, 1) for g in shapes], [round((g.bounds[3] - g.bounds[1]) * k, 1) for g in shapes])
cx, cy = NW / 2, (H - 15 - 24 + 20) / 2 + 12                         # centre of the free area (mm, y up): rows 20..150
parts = []
xs = [cx]                    # line 1 on the left, line 2 on the right (reads top to bottom)
for g, x0 in zip(shapes, xs):
    g = affinity.scale(g, k, k, origin=(0, 0)).buffer(float(sys.argv[5]), join_style=1); b = g.bounds
    g = affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)
    g = affinity.rotate(g, 90, origin=(0, 0)); g = affinity.translate(g, x0, cy)
    parts.append(g)
text = unary_union(parts); print("text bounds", [round(v, 1) for v in text.bounds])
from shapely.prepared import prep
tp = prep(text); THR = float(sys.argv[3]); PIX = 0.5
sq = []
x0, y0, x1, y1 = text.bounds
for ix in range(int(x0 / PIX) - 1, int(x1 / PIX) + 2):
    for iy in range(int(y0 / PIX) - 1, int(y1 / PIX) + 2):
        c = box(ix * PIX, iy * PIX, (ix + 1) * PIX, (iy + 1) * PIX)
        if tp.intersects(c) and text.intersection(c).area > THR * PIX * PIX: sq.append(c.buffer(0.01, join_style=2))
text = unary_union(sq)
np.save(f"{O}/dhikr_grid.npy", G)
print("text squares:", len(sq))
def cells(v): return unary_union([box(i, H - 1 - j, i + 1, H - j) for j in range(H) for i in range(NW) if G[j, i] == v]).buffer(0.02, join_style=2)
hx, hy = 25.0, H - 5.0
hole = Point(hx, hy).buffer(2.2, 40); ring = Point(hx, hy).buffer(3.4, 40).difference(hole)
acc = cells(2).difference(Point(hx, hy).buffer(4.2, 40)).buffer(0)
main = unary_union([cells(1), ring]).difference(hole).difference(acc.buffer(0.03, join_style=2)).buffer(0)
fp = max(list(main.geoms), key=lambda p: p.area)
base = Polygon(fp.exterior).difference(hole)
main = unary_union([main, text.intersection(base.buffer(-1.5))]).buffer(0)
def ex(x): return [p for p in (x.geoms if hasattr(x, "geoms") else [x]) if isinstance(p, Polygon) and p.area > 1e-4]
meshes = {}
for n, g, h, z in (("base", base, 1.2, 0), ("main", main, 0.6, 1.2), ("accent", acc, 0.6, 1.2)):
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in ex(g)]); m.apply_translation([0, 0, z]); meshes[n] = m
    m.export(f"{O}/dhikrfn_{n}.stl"); print(n, "pieces", len(ex(g)), "watertight", all(b.is_watertight for b in m.split(only_watertight=False)), "size", m.extents.round(1).tolist())
cfg = json.loads(build_project_settings(open("/home/user/-sharpseek-api/cad/config/bambu_project_4fil_pla.config", "rb").read(), ["#F4F4F2", "#173D75", "#F08DBD", "#1B1B1B"], tower=(230, 100, 40)))
cfg["flush_multiplier"] = ["1", "1"]
tmp = f"{O}/_t.3mf"
write_bambu_3mf(tmp, [("Base_White", meshes["base"], 1), ("Main_Navy", meshes["main"], 2), ("Accent_Pink", meshes["accent"], 3)], (60, 70), "Bookmark_Dhikr_Fine_182", json.dumps(cfg, indent=4))
with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(f"{O}/Bookmark_Dhikr_Fine_182.3mf", "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        d = zi.read(it.filename)
        if it.filename == "Metadata/model_settings.config":
            t = d.decode(); assert 'value="1 1 1"' in t; d = t.replace('key="filament_maps" value="1 1 1"', 'key="filament_maps" value="1 1 1 2"').encode()
        if it.filename == "Metadata/project_settings.config":
            c = json.loads(d); c["filament_map"] = ["1", "1", "1", "2"]; d = json.dumps(c, indent=4).encode()
        zo.writestr(it, d)
os.remove(tmp)
def patch(g, col):
    v, c = [], []
    for p in ex(g):
        for r in [p.exterior] + list(p.interiors):
            xy = np.asarray(r.coords); v += xy.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(v, c), facecolor=col, edgecolor="none")
fig, ax = plt.subplots(figsize=(4.4, 13.5), dpi=110)
ax.add_patch(patch(base, "#f4f4f2")); ax.add_patch(patch(main, "#173d75")); ax.add_patch(patch(acc, "#f08dbd"))
ax.set_xlim(-2, 52); ax.set_ylim(-2, H + 2); ax.set_aspect("equal"); ax.axis("off"); ax.set_title("50 x 182 mm", fontsize=10)
fig.savefig(f"{O}/dhikr_fine_preview.png", bbox_inches="tight", facecolor="#cfd4d8")
