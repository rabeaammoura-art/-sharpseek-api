"""E30 line art (transparent PNG) -> pieces with in-plane butterfly (bow-tie) keys, STL + keys + preview.
    python make_e30.py lineart.png OUTDIR
Sizes: small 500 mm (2x1), medium 700 mm (3x2), large 940 mm (4x2) - the bed (325 x 320) decides the piece count.  Thickness 4 mm.
At each cut crossing a rounded pad (full thickness) joins both pieces; a bow-tie pocket is cut from the BACK
(2 mm deep, front stays closed) and a printed bow-tie key (1.8 mm) locks the two pads together."""
import sys, pathlib, json, itertools
import cv2, numpy as np, trimesh, manifold3d as m3
from PIL import Image
from shapely import affinity
from shapely.geometry import LineString
from shapely.ops import nearest_points, unary_union
from manifold3d import CrossSection as CS, JoinType, FillRule
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "student_pack"))
from trace import mask_to_geom

T, POCKET, KEYT, CLEAR = 4.0, 2.0, 1.8, 0.2
PAD_L, PAD_W = 18.0, 12.0                    # pad along the seam normal / along the seam
KEY = [(-7, -4), (-7, 4), (0, 2), (7, 4), (7, -4), (0, -2)]   # bow-tie key (mm)
FIT = (316, 312)
SIZES = {"small": (500, 2, 1), "medium": (700, 3, 2), "large": (940, 4, 2)}
MAXKEYS, MINGAP = 4, 45.0

a = np.array(Image.open(sys.argv[1]).convert("RGBA"))[..., 3] > 128
ys, xs = np.where(a); a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
m = cv2.resize(a.astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) > 0.5).astype(np.uint8)
g = mask_to_geom(m.astype(bool), 1.0, m.shape[0])
parts = sorted(g.geoms if hasattr(g, "geoms") else [g], key=lambda p: -p.area); main = parts[0]
for p in parts[1:]:
    if p.area < 150: continue
    pa, pb = nearest_points(main, p); main = unary_union([main, p, LineString([pa, pb]).buffer(4)])
g0 = affinity.translate(main, -main.bounds[0], -main.bounds[1])

def to_cs(geom):
    out = None
    for p in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        c = CS([list(map(tuple, p.exterior.coords))] + [list(map(tuple, r.coords)) for r in p.interiors], FillRule.EvenOdd)
        out = c if out is None else out + c
    return out
rect = lambda x0, y0, x1, y1: CS.square([x1 - x0, y1 - y0]).translate([x0, y0])
def rot(c, ang, cx, cy): return c.translate([-cx, -cy]).rotate(ang).translate([cx, cy])
def pad_at(cx, cy, ang): return rot(CS.square([PAD_L, PAD_W], center=True).offset(0, JoinType.Round).translate([cx, cy]), ang, cx, cy).offset(0, JoinType.Round)
def key2d(cx, cy, ang, grow=0.0):
    c = CS([KEY], FillRule.EvenOdd).translate([cx, cy]); c = rot(c, ang, cx, cy)
    return c.offset(grow, JoinType.Round, 2, 24) if grow else c

def build(name, wmm, nx, ny, out):
    s = wmm / g0.bounds[2]; gg = affinity.scale(g0, s, s, origin=(0, 0)); W, H = gg.bounds[2], gg.bounds[3]
    G = to_cs(gg)
    area = lambda c: c.area()
    # cut positions: vertical cuts near uniform, horizontal cut per column; minimise stroke area under the cut line
    xcuts = [0.0]
    for i in range(1, nx):
        best = min(((area(G ^ rect(x - .5, 0, x + .5, H)), x) for x in np.arange(i * W / nx * 0.93, i * W / nx * 1.07, 3)))
        xcuts.append(best[1])
    xcuts.append(W)
    ycuts = {}
    for i in range(nx):
        yy = [0.0]
        for j in range(1, ny):
            best = min(((area(G ^ rect(xcuts[i], y - .5, xcuts[i + 1], y + .5)), y) for y in np.arange(j * H / ny * 0.9, j * H / ny * 1.1, 3)))
            yy.append(best[1])
        yy.append(H); ycuts[i] = yy
    rects = {(i, j): (xcuts[i], ycuts[i][j], xcuts[i + 1], ycuts[i][j + 1]) for i in range(nx) for j in range(ny)}
    # seams: (piece a, piece b, orientation, line coords)
    seams = []
    for i in range(nx):
        for j in range(ny - 1):
            seams.append(((i, j), (i, j + 1), "h", (xcuts[i], ycuts[i][j + 1], xcuts[i + 1], ycuts[i][j + 1])))
    for i in range(nx - 1):
        seams.append(((i, 0), (i + 1, 0), "v", (xcuts[i + 1], 0, xcuts[i + 1], H)))  # whole height; pieces in a column share x-cut
    pieces = {k: G ^ rect(*r) for k, r in rects.items()}
    pads = {k: None for k in rects}; pockets = {k: None for k in rects}
    nkeys = 0; keylog = []
    for a_, b_, o, (x0, y0, x1, y1) in seams:
        band = rect(x0 - .6, y0 - .6, x1 + .6, y1 + .6) if o == "h" else rect(x0 - .6, y0, x0 + .6, y1)
        cr = [c for c in (G ^ band).decompose() if area(c) > 3]
        cr.sort(key=lambda c: -area(c))
        chosen = []
        for c in cr:
            bb = c.bounds(); cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
            if o == "v" and not (rects[a_][1] - 1 <= cy <= rects[a_][3] + 1): pass
            if all(np.hypot(cx - px_, cy - py_) >= MINGAP for px_, py_ in chosen) and len(chosen) < MAXKEYS and 18 < (bb[2] - bb[0] if o == "h" else bb[3] - bb[1]) + 100:
                chosen.append((cx, cy))
        for cx, cy in chosen:
            ang = 90 if o == "h" else 0          # key long axis across the seam
            pad = pad_at(cx, cy, ang); pk = key2d(cx, cy, ang, CLEAR)
            for k in rects:
                r = rect(*rects[k])
                pp = pad ^ r
                if not pp.is_empty(): pieces[k] = pieces[k] + pp
                kk = pk ^ r
                if not kk.is_empty(): pockets[k] = kk if pockets[k] is None else pockets[k] + kk
            nkeys += 1; keylog.append((o, round(cx), round(cy)))
    out.mkdir(parents=True, exist_ok=True); meta = {}
    for k, c in pieces.items():
        bb = c.bounds(); w, h = bb[2] - bb[0], bb[3] - bb[1]
        solid = m3.Manifold.extrude(c, T)
        if pockets[k] is not None:
            solid = solid - m3.Manifold.extrude(pockets[k], POCKET).translate([0, 0, T - POCKET])
        solid = solid.translate([-bb[0], -bb[1], 0]); ms = solid.to_mesh()
        tm = trimesh.Trimesh(ms.vert_properties[:, :3], ms.tri_verts); tm.merge_vertices()
        fn = f"e30_{name}_{k[0] + 1}x{k[1] + 1}.stl"; tm.export(out / fn)
        meta[fn] = dict(size=[round(w, 1), round(h, 1)], fits=bool(w <= 325 and h <= 320), watertight=bool(tm.is_watertight))
    key = m3.Manifold.extrude(CS([KEY], FillRule.EvenOdd), KEYT); ms = key.to_mesh()
    trimesh.Trimesh(ms.vert_properties[:, :3], ms.tri_verts).export(out / "e30_key.stl")
    print(name, f"{W:.0f}x{H:.0f} mm", f"{nx}x{ny}", "keys", nkeys, json.dumps(meta))
    json.dump(dict(keys=nkeys, keylog=keylog, pieces=meta), open(out / f"layout_{name}.json", "w"))
    # preview
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch; from matplotlib.path import Path
    def compound(c):
        v, cd = [], []
        for poly in c.to_polygons():
            pts = np.vstack([poly, poly[:1]]); v.extend(pts); cd.extend([1] + [2] * (len(pts) - 2) + [79])
        return Path(v, cd)
    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=120); cols = ["#c0392b", "#1f77b4", "#2a9d4b", "#8e44ad", "#e67e22", "#16a085"]
    for n_, (k, c) in enumerate(pieces.items()):
        ax.add_patch(PathPatch(compound(c), fc=cols[n_ % 6], ec="none"))
    for k, c in pockets.items():
        if c is not None:
            ax.add_patch(PathPatch(compound(c), fc="white", ec="black", lw=.5))
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.set_title(f"E30 {name}: {W/10:.0f} x {H/10:.0f} cm, {nx*ny} pieces, {nkeys} butterfly keys (white = key pockets)")
    fig.savefig(out / f"layout_{name}.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

out = pathlib.Path(sys.argv[2])
for name, (w, nx, ny) in SIZES.items():
    build(name, w, nx, ny, out)
