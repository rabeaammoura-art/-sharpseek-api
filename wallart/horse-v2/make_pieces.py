"""Horse head 500 mm -> 4 printable pieces (head in one piece) with tongue-and-slot joints.
    python make_pieces.py horse_head_500mm.stl OUTDIR
Cuts: V at x=xc (full height), head/neck cut at y=yc (right of xc), mane cut at y=ys (left of xc);
positions are searched to cross as little stroke as possible."""
import sys, pathlib, itertools
import numpy as np, trimesh, manifold3d as m3
from manifold3d import CrossSection as CS, JoinType

T_LEN, T_ERODE, CLEAR, DEPTH_GAP = 7.0, 1.3, 0.15, 0.0
m = trimesh.load(sys.argv[1]); m.apply_translation(-m.bounds[0])
M = m3.Manifold(m3.Mesh(vert_properties=np.array(m.vertices, np.float32), tri_verts=np.array(m.faces, np.uint32)))
THK = float(m.extents[2]); W, H = float(m.extents[0]), float(m.extents[1])
G = M.slice(THK / 2)
rect = lambda x0, y0, x1, y1: CS.square([x1 - x0, y1 - y0]).translate([x0, y0])
area = lambda c: c.area()

def cost_line(x0, y0, x1, y1):
    return area(G ^ rect(min(x0, x1) - .5, min(y0, y1) - .5, max(x0, x1) + .5, max(y0, y1) + .5)) if True else 0
FIT = (316, 312)   # usable bed incl. 4 mm of tongue
def fits(r):
    c = G ^ rect(*r)
    if c.is_empty(): return True
    b = c.bounds(); w, h = b[2] - b[0], b[3] - b[1]
    return w <= FIT[0] and h <= FIT[1] and w > 80 and h > 80
best = None
for xc in range(240, 341, 5):
    if xc > FIT[0] or W - xc > FIT[0]: continue
    for yc in range(85, 101, 5):
        if not fits((xc, yc, W + 1, H + 1)) or not fits((xc, -1, W + 1, yc)): continue
        for ys in range(100, 270, 5):
            if not (fits((-1, ys, xc, H + 1)) and fits((-1, -1, xc, ys))): continue
            c = cost_line(xc, 0, xc, H) + cost_line(xc, yc, W, yc) + cost_line(0, ys, xc, ys)
            if best is None or c < best[0]:
                best = (c, xc, yc, ys)
_, xc, yc, ys = best
print("cuts: xc=%d yc=%d ys=%d (stroke area under cut lines %.0f mm2)" % (xc, yc, ys, best[0]))
R = {"head": (xc, yc, W + 1, H + 1), "neck": (xc, -1, W + 1, yc), "maneU": (-1, ys, xc, H + 1), "maneL": (-1, -1, xc, ys)}
# adjacent pairs: (from, to, edge rectangle band centre line, strip into 'to')
E = G.offset(-T_ERODE, JoinType.Round, 2, 16)
pairs = [("head", "neck", (xc, yc, W, yc)), ("head", "maneU", (xc, yc, xc, H)), ("neck", "maneL", (xc, 0, xc, yc)),
         ("maneU", "maneL", (0, ys, xc, ys)), ("head", "maneL", None)]
pieces = {k: G ^ rect(*v) for k, v in R.items()}
n_t = 0
for a, b, edge in pairs:
    if edge is None: continue
    x0, y0, x1, y1 = edge
    horiz = abs(y1 - y0) < 1e-6
    # strip on b's side, T_LEN deep
    sa = {"head": 1, "neck": -1, "maneU": 1, "maneL": -1}
    if horiz:
        d = -1 if b in ("neck", "maneL") else 1
        strip = rect(x0, y0 + (0 if d > 0 else -T_LEN), x1, y0 + (T_LEN if d > 0 else 0))
        touch = rect(x0, y0 - .4, x1, y0 + .4)
    else:
        d = -1 if b in ("maneU", "maneL", "neck") else 1
        strip = rect(x0 + (0 if d > 0 else -T_LEN), y0, x0 + (T_LEN if d > 0 else 0), y1)
        touch = rect(x0 - .4, y0, x0 + .4, y1)
    cand = (E ^ (strip + touch)).decompose()
    tongues = []
    for c in cand:
        if area(c ^ touch) < 1.0 or area(c) < 6: continue
        bb = c.bounds(); along = (bb[2] - bb[0]) if horiz else (bb[3] - bb[1])
        if along > 22: print("  skip long tangential run on", a, b, round(along)); continue
        tongues.append(c ^ strip)
    for t in tongues:
        t = t ^ rect(-1, -1, W + 1, H + 1)
        pieces[a] = pieces[a] + t
        pieces[b] = pieces[b] - t.offset(CLEAR, JoinType.Round, 2, 16)
        n_t += 1
    print(f"  {a}->{b}: {len(tongues)} tongues")
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
import json
meta = {}
for k, c in pieces.items():
    parts = c.decompose()
    bb = c.bounds(); sol = m3.Manifold.extrude(c, THK).translate([-bb[0], -bb[1], 0])
    ms = sol.to_mesh(); tm = trimesh.Trimesh(ms.vert_properties[:, :3], ms.tri_verts, process=True); tm.merge_vertices()
    print('   manifold status', sol.status(), 'faces', len(tm.faces), 'euler', tm.euler_number, 'broken', len(trimesh.repair.broken_faces(tm)))
    tm.export(out / f"horse_{k}.stl")
    meta[k] = dict(size=[round(bb[2] - bb[0], 1), round(bb[3] - bb[1], 1)], parts=len(parts), watertight=bool(tm.is_watertight), origin=[bb[0], bb[1]])
    print(k, meta[k])
json.dump(dict(xc=xc, yc=yc, ys=ys, pieces=meta), open(out / "layout.json", "w"))

# preview: pieces in colour (tongues/slots visible), cut lines dashed
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch; from matplotlib.path import Path
cols = {"head": "#c0392b", "neck": "#8e44ad", "maneU": "#1f77b4", "maneL": "#2a9d4b"}
fig, ax = plt.subplots(figsize=(10, 7.4), dpi=120)
for k, c in pieces.items():
    for poly in c.to_polygons():
        pts = np.vstack([poly, poly[:1]])
        ax.add_patch(PathPatch(Path(pts, [1] + [2] * (len(pts) - 2) + [79]), fc=cols[k], ec="none"))
for k, (x0, y0, x1, y1) in {"head": (xc, yc, W, H), "neck": (xc, 0, W, yc), "maneU": (0, ys, xc, H), "maneL": (0, 0, xc, ys)}.items():
    ax.text((x0 + x1) / 2, y1 - 14, k, ha="center", fontsize=12, fontweight="bold", color=cols[k], bbox=dict(fc="white", ec=cols[k], boxstyle="round"))
ax.axvline(xc, color="#444", ls="--", lw=.8); ax.axhline(yc, xmin=xc / W, color="#444", ls="--", lw=.8); ax.axhline(ys, xmax=xc / W, color="#444", ls="--", lw=.8)
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_aspect("equal"); ax.set_title(f"4 pieces; cuts x={xc}, y={yc} (right), y={ys} (left); tongue 7 mm + 0.15 mm clearance")
fig.savefig(out / "layout.png", bbox_inches="tight", facecolor="white")
