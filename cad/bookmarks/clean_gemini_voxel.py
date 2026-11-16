import sys, json, zipfile, os, numpy as np, trimesh, contourpy
sys.path.insert(0, "/home/user/-sharpseek-api/cad")
from threemf import write_bambu_3mf, build_project_settings
from scipy import ndimage as ndi
from shapely.geometry import Polygon, MultiPolygon, box
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
S, O, tag, name, cols = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5].split(",")
P = 0.25; NX, NY = 200, 728
def mask(path, z, tol=0.02):
    m = trimesh.load(path); cz = m.triangles[:, :, 2].mean(1); sel = (np.abs(cz - z) < tol) & (np.abs(m.face_normals[:, 2]) > 0.5)
    cen = m.triangles[sel].mean(1)
    a = np.zeros((NY, NX), bool); a[np.clip((cen[:, 1] / P).astype(int), 0, NY - 1), np.clip((cen[:, 0] / P).astype(int), 0, NX - 1)] = True
    return a
M1 = mask(f"{S}/{tag}_1.stl", 2.0); M2 = mask(f"{S}/{tag}_2.stl", 2.0); M3 = mask(f"{S}/{tag}_3.stl", 2.0); SIL = mask(f"{S}/{tag}_1.stl", 0.0)
top = M1 | M2 | M3
print("silhouette px", int(SIL.sum()), "| top px", int(top.sum()), "| M1/M2/M3", int(M1.sum()), int(M2.sum()), int(M3.sum()), "| overlap", int((M1 & M2).sum() + (M1 & M3).sum() + (M2 & M3).sum()), "| top outside silhouette", int((top & ~SIL).sum()), "| silhouette not covered by top", int((SIL & ~top).sum()))
# one label per pixel of the silhouette: 1,2,3 (uncovered -> background colour 1)
L = np.zeros((NY, NX), int); L[SIL] = 1; L[M2] = 2; L[M3] = 3; L[M1] = 1
L[~SIL] = 0
# remove specks: colour 2 / 3 components under 0.8 mm2 go back to colour 1
for v in (2, 3):
    lab, n = ndi.label(L == v, structure=np.ones((3, 3)))
    for k in range(1, n + 1):
        sz = (lab == k).sum()
        if sz < 13: L[lab == k] = 1
if os.environ.get("OPEN3"):                                            # hairline strokes of colour 3 (thinner than 0.75 mm) go back to colour 1
    op = ndi.binary_opening(L == 3, structure=np.ones((3, 3)))
    print("hairline px removed from colour 3:", int(((L == 3) & ~op).sum())); L[(L == 3) & ~op] = 1
UP = 4
def smooth_polys(Lm, sig):
    fl = np.stack([ndi.gaussian_filter(np.pad(np.kron((Lm == v).astype(float), np.ones((UP, UP))), 8), sig) for v in (0, 1, 2, 3)])
    arg = fl.argmax(0); out = {}
    for v in (0, 1, 2, 3):
        pts_l, off_l = contourpy.contour_generator(z=(arg == v).astype(float), fill_type="OuterOffset").filled(0.5, 9)
        polys = []
        for pts, offs in zip(pts_l, off_l):
            rings = [(pts[offs[i]:offs[i + 1]] - 8 + 0.5) * (P / UP) for i in range(len(offs) - 1)]
            p = Polygon(rings[0], rings[1:]).buffer(0)
            if not p.is_empty: polys.append(p)
        out[v] = unary_union(polys).simplify(0.02)
    return out
Lm = L.copy()                                              # label 0 = outside the silhouette
poly = smooth_polys(Lm, 3.0)
sil = unary_union([poly[1], poly[2], poly[3]]).buffer(0)
def ex(x): return [p for p in (x.geoms if hasattr(x, "geoms") else [x]) if isinstance(p, Polygon) and p.area > 0.05]
for v in (1, 2, 3): print("label", v, "pieces", len(ex(poly[v])), "area mm2", round(poly[v].area))
big = max(ex(sil), key=lambda p: p.area)
holes = [Polygon(i) for i in big.interiors if Polygon(i).area > 3.0]
print("silhouette: pieces", len(ex(sil)), "holes kept", [round(h.area, 1) for h in holes], "all holes", len(list(big.interiors)))
slab = Polygon(big.exterior).difference(unary_union(holes) if holes else Polygon()).buffer(0)
# any label area inside the filled-in tiny holes: give it to colour 1 (already inside the slab, nothing to do)
def extr(g, h, z0):
    g = g.buffer(0.004, join_style=2).buffer(0)
    m = trimesh.util.concatenate([trimesh.creation.extrude_polygon(p, h) for p in ex(g)]); m.apply_translation([0, 0, z0]); return m
MODE = sys.argv[6] if len(sys.argv) > 6 else "inlay"
for v in (1, 2, 3): poly[v] = poly[v].intersection(slab).buffer(0)
parts = [("Slab", extr(slab, 1.2, 0), 1)]
if MODE == "inlay": parts.append(("Raised_Colour1", extr(poly[1], 0.6, 1.2), 1))
parts += [("Colour2", extr(poly[2], 0.6, 1.2), 2), ("Colour3", extr(poly[3], 0.6, 1.2), 3)]
for n, m, s in parts: print(n, "faces", len(m.faces), "watertight", all(b.is_watertight for b in m.split(only_watertight=False)))
cfg = json.loads(build_project_settings(open("/home/user/-sharpseek-api/cad/config/bambu_project_4fil_pla.config", "rb").read(), cols + ["#1B1B1B"], tower=(230, 100, 40)))
cfg["flush_multiplier"] = ["1", "1"]
tmp = f"{O}/_t.3mf"
write_bambu_3mf(tmp, [(n, m, s) for n, m, s in parts], (60, 70), name, json.dumps(cfg, indent=4))
with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(f"{O}/{name}.3mf", "w", zipfile.ZIP_DEFLATED) as zo:
    for it in zi.infolist():
        d = zi.read(it.filename)
        if it.filename == "Metadata/model_settings.config":
            t = d.decode(); assert 'value="1 1 1 1"' in t or 'value="1 1 1"' in t
            d = t.replace('key="filament_maps" value="1 1 1 1"', 'key="filament_maps" value="1 1 1 2"').replace('key="filament_maps" value="1 1 1"', 'key="filament_maps" value="1 1 1 2"').encode()
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
for g, c in ((slab, cols[0]), (poly[2], cols[1]), (poly[3], cols[2])): ax.add_patch(patch(g, c))
ax.set_xlim(-2, 52); ax.set_ylim(-2, 184); ax.set_aspect("equal"); ax.axis("off")
fig.savefig(f"{O}/{name}_preview.png", bbox_inches="tight", facecolor="#cfd4d8")
