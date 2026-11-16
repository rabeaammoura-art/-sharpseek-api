import sys, json, zipfile, os, numpy as np, trimesh
sys.path.insert(0, "/home/user/-sharpseek-api/cad")
from threemf import write_bambu_3mf, build_project_settings
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
S, O, tag, name, cols, MODE = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(","), sys.argv[6]
P = 0.25; NX, NY = 200, 728
def mask(path, z, tol=0.02):
    m = trimesh.load(path); cz = m.triangles[:, :, 2].mean(1); sel = (np.abs(cz - z) < tol) & (np.abs(m.face_normals[:, 2]) > 0.5)
    cen = m.triangles[sel].mean(1)
    a = np.zeros((NY, NX), bool); a[np.clip((cen[:, 1] / P).astype(int), 0, NY - 1), np.clip((cen[:, 0] / P).astype(int), 0, NX - 1)] = True
    return a
M1, M2, M3 = (mask(f"{S}/{tag}_{i}.stl", 2.0) for i in (1, 2, 3)); SIL = mask(f"{S}/{tag}_1.stl", 0.0)
if os.environ.get("SMOOTH_SIL"):                                       # ragged outer edge: open + close the silhouette by about 1 mm
    r = int(float(os.environ["SMOOTH_SIL"]) / P); st = np.fromfunction(lambda i, j: (i - r) ** 2 + (j - r) ** 2 <= r * r, (2 * r + 1, 2 * r + 1))
    SIL = ndi.binary_closing(ndi.binary_opening(np.pad(SIL, r + 2), structure=st), structure=st)[r + 2:-(r + 2), r + 2:-(r + 2)]
L = np.zeros((NY, NX), int); L[SIL] = 1; L[M2] = 2; L[M3] = 3; L[M1] = 1; L[~SIL] = 0
if os.environ.get("BAND"):                                             # stray colour-3 outline lines along the edge
    dist = ndi.distance_transform_edt(np.pad(SIL, 1))[1:-1, 1:-1] * P
    cut = (L == 3) & (dist < float(os.environ["BAND"])); print("colour-3 px removed in the edge band:", int(cut.sum())); L[cut] = 1
for v in (2, 3):
    lab, n = ndi.label(L == v, structure=np.ones((3, 3))); sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    for k, sz in enumerate(sizes, 1):
        if sz < 13: L[lab == k] = 1
print("px per label", [int((L == v).sum()) for v in (1, 2, 3)])
def polys(m):
    boxes = []
    for j in range(NY):
        row = m[j]; d = np.diff(np.r_[0, row.astype(int), 0]); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
        for a, b in zip(st, en): boxes.append(box(a * P, j * P, b * P, (j + 1) * P))
    return unary_union(boxes).buffer(0)
def ex(x): return [p for p in (x.geoms if hasattr(x, "geoms") else [x]) if isinstance(p, Polygon) and p.area > 0.03]
p_sil = polys(L > 0); big = max(ex(p_sil), key=lambda p: p.area)
holes = [Polygon(i) for i in big.interiors if Polygon(i).area > 3.0]
slab = Polygon(big.exterior).difference(unary_union(holes) if holes else Polygon()).buffer(0)
print("slab pieces", len(ex(slab)), "holes kept", [round(h.area, 1) for h in holes])
pl = {v: polys(L == v).intersection(slab).buffer(0) for v in (1, 2, 3)}
for v in (1, 2, 3): print("label", v, "pieces", len(ex(pl[v])), "area", round(pl[v].area))
def extr(g, h, z0):
    g = g.buffer(0.004, join_style=2).buffer(0)
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in ex(g)]); m.apply_translation([0, 0, z0]); return m
parts = [("Slab", extr(slab, 1.2, 0), 1)]
if MODE == "inlay": parts.append(("Raised_Colour1", extr(pl[1], 0.6, 1.2), 1))
parts += [("Colour2", extr(pl[2], 0.6, 1.2), 2), ("Colour3", extr(pl[3], 0.6, 1.2), 3)]
for n, m, s in parts: print(n, "faces", len(m.faces), "watertight", all(b.is_watertight for b in m.split(only_watertight=False)))
cfg = json.loads(build_project_settings(open("/home/user/-sharpseek-api/cad/config/bambu_project_4fil_pla.config", "rb").read(), cols + ["#1B1B1B"], tower=(230, 100, 40)))
cfg["flush_multiplier"] = ["1", "1"]
tmp = f"{O}/_t.3mf"
write_bambu_3mf(tmp, parts, (60, 70), name, json.dumps(cfg, indent=4))
with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(f"{O}/{name}.3mf", "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        d = zi.read(it.filename)
        if it.filename == "Metadata/model_settings.config":
            t = d.decode(); d = t.replace('key="filament_maps" value="1 1 1 1"', 'key="filament_maps" value="1 1 1 2"').replace('key="filament_maps" value="1 1 1"', 'key="filament_maps" value="1 1 1 2"').encode()
        if it.filename == "Metadata/project_settings.config":
            c = json.loads(d); c["filament_map"] = ["1", "1", "1", "2"]; d = json.dumps(c, indent=4).encode()
        zo.writestr(it, d)
os.remove(tmp)
for n, m, s in parts: m.export(f"{O}/{name}_{n}.stl")
def patch(g, col):
    v, c = [], []
    for p in ex(g):
        for r in [p.exterior] + list(p.interiors):
            xy = np.asarray(r.coords); v += xy.tolist(); c += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(v, c), facecolor=col, edgecolor="none")
fig, ax = plt.subplots(figsize=(4.6, 13), dpi=100)
ax.add_patch(plt.Rectangle((-5, -5), 60, 195, facecolor="#cfd4d8"))
for g, c in ((slab, cols[0]), (pl[2], cols[1]), (pl[3], cols[2])): ax.add_patch(patch(g, c))
ax.set_xlim(-2, 52); ax.set_ylim(-2, 184); ax.set_aspect("equal"); ax.axis("off")
fig.savefig(f"{O}/{name}_preview.png", bbox_inches="tight", facecolor="#cfd4d8")
