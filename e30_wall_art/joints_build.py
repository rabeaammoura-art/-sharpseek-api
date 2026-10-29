"""E30 wall art -> 6 printable tiles joined by bow-tie keys, with a verification report.
Input : out/rings.pkl (panel outline rings in mm, 900 mm wide, built by build.py + mesh.py)
Output: out/tiles/*.stl (print orientation: front face on the bed), out/e30_key.stl, out/assembled_preview.png, out/REPORT.md
"""
import pickle, json, itertools, numpy as np, trimesh
from shapely.geometry import Polygon, LineString, box, Point, MultiPolygon
from shapely import symmetric_difference_all, affinity
from shapely.ops import unary_union
from manifold3d import Manifold, CrossSection, FillRule
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

OUT = 'out'
T = 5.0                 # panel thickness
POCKET = 2.5            # pocket depth from the back (front skin stays 2.5 mm)
KEYT = 2.3              # key thickness (0.2 mm shorter than the pocket)
CLEAR = 0.2             # clearance key <-> pocket, all around
GAP = 0.1               # each tile face is pulled back this much at a seam (0.2 mm total joint gap)
MINW = 2.5              # minimum wall / line width
PAD_L, PAD_W, PAD_R = 22.0, 16.0, 3.0    # pad: across seam x along seam, corner radius
KEY = [(-7, -4), (-7, 4), (0, 2), (7, 4), (7, -4), (0, -2)]   # bow-tie key outline (mm)
MAXKEYS, MINGAP = 3, 60.0
FIXGAP = 14.0   # closest allowed spacing for connectivity keys
PLATE = (340.0, 310.0)  # usable H2D plate for a tile (350 x 320 minus margin)

rings = pickle.load(open(OUT + '/rings.pkl', 'rb'))
g = symmetric_difference_all(sorted([Polygon(r) for r in rings], key=lambda p: -p.area))
W = 900.0; H = max(r[:, 1].max() for r in rings)
XC, YC = [290.0, 610.0], 292.0
xs = [0, *XC, W]; ys = [0, YC, H]

# ---------- pads + keys -------------
def rot(p, a, c): return affinity.rotate(p, a, origin=c)
def pad_poly(c, ang):
    p = box(-PAD_L/2, -PAD_W/2, PAD_L/2, PAD_W/2).buffer(-PAD_R).buffer(PAD_R)
    return rot(affinity.translate(p, *c), ang, c)
def key_poly(c, ang, grow=0.0):
    k = affinity.translate(Polygon(KEY), *c); k = rot(k, ang, c)
    return k.buffer(grow, join_style=1, resolution=16) if grow else k

seams = []   # (orientation, coord, tile ids a,b, range)
for i, x in enumerate(XC):
    for j in range(2): seams.append(('v', x, (j, i), (j, i + 1), (ys[j], ys[j + 1])))
for i in range(3): seams.append(('h', YC, (0, i), (1, i), (xs[i], xs[i + 1])))

def seam_line(o, c, lo, hi): return LineString([(c, lo), (c, hi)]) if o == 'v' else LineString([(lo, c), (hi, c)])
def tile_rect(j, i): return box(xs[i], ys[j], xs[i + 1], ys[j + 1])

cands = []   # candidate key sites: crossings of the seam with the drawing
for o, c, a, b, (lo, hi) in seams:
    inter = g.intersection(seam_line(o, c, lo, hi)); segs = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
    for s in segs:
        if s.length <= 0: continue
        m = s.interpolate(0.5, normalized=True); p = (m.x, m.y)
        along = p[1] if o == 'v' else p[0]
        lim = (lo, hi)
        if along - lim[0] < 14 or lim[1] - along < 14: continue            # keep pads clear of panel edge / other seams
        if o == 'h' and min(abs(p[0] - x) for x in XC) < 14: continue
        if o == 'v' and abs(p[1] - YC) < 14: continue
        ang = 0 if o == 'v' else 90
        pad = pad_poly(p, ang)
        score = pad.difference(g).area           # new visible material added by the pad
        cands.append(dict(o=o, c=c, a=a, b=b, p=p, ang=ang, score=score))

def comps(poly):
    return [q for q in (poly.geoms if hasattr(poly, 'geoms') else [poly]) if q.area > 0.5]

# material with pads is needed to know the islands per tile; choose keys greedily by score then fix connectivity
chosen = []
for o, c, a, b, rng in seams:
    pool = sorted([k for k in cands if k['o'] == o and k['c'] == c and k['a'] == a], key=lambda k: k['score'])
    mine = []
    for k in pool:
        if len(mine) >= MAXKEYS: break
        if all(np.hypot(k['p'][0] - m['p'][0], k['p'][1] - m['p'][1]) >= MINGAP for m in mine): mine.append(k)
    chosen += mine

def build(chosen):
    pads = unary_union([pad_poly(k['p'], k['ang']) for k in chosen]) if chosen else Polygon()
    return unary_union([g, pads])

def tiles_of(mat):
    tiles = {}
    for j in range(2):
        for i in range(3):
            r = tile_rect(j, i)
            sh = r.bounds
            x0 = sh[0] + (GAP/2 if i > 0 else 0); x1 = sh[2] - (GAP/2 if i < 2 else 0)
            y0 = sh[1] + (GAP/2 if j > 0 else 0); y1 = sh[3] - (GAP/2 if j < 1 else 0)
            tiles[(j, i)] = mat.intersection(box(x0, y0, x1, y1))
    return tiles

def island_graph(chosen):
    mat = build(chosen); tl = tiles_of(mat)
    isl = {}                               # (tile, idx) -> polygon
    for t, poly in tl.items():
        for n, q in enumerate(sorted(comps(poly), key=lambda q: -q.area)): isl[(t, n)] = q
    def which(t, pt):
        for (tt, n), q in isl.items():
            if tt == t and q.buffer(0.3).contains(Point(pt)): return (tt, n)
        return None
    edges = []
    for k in chosen:
        d = 4.0
        off = (d, 0) if k['o'] == 'v' else (0, d)
        pa = (k['p'][0] - off[0], k['p'][1] - off[1]); pb = (k['p'][0] + off[0], k['p'][1] + off[1])
        edges.append((which(k['a'], pa), which(k['b'], pb), k))
    return isl, edges

def components_after(chosen):
    isl, edges = island_graph(chosen)
    par = {n: n for n in isl}
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b, k in edges:
        if a is None or b is None: continue
        par[f(a)] = f(b)
    groups = {}
    for n in isl: groups.setdefault(f(n), []).append(n)
    return isl, list(groups.values()), f

# connectivity fix: add the cheapest candidate crossing that reduces the number of disconnected groups
for _ in range(60):
    isl, groups, f = components_after(chosen)
    if len(groups) == 1: break
    best = None
    for k in sorted(cands, key=lambda k: k['score']):
        if k in chosen: continue
        if any(np.hypot(k['p'][0] - m['p'][0], k['p'][1] - m['p'][1]) < FIXGAP for m in chosen): continue
        if len(components_after(chosen + [k])[1]) < len(groups): best = k; break
    if best is None: break
    chosen.append(best)
isl, groups, f = components_after(chosen)
print('keys', len(chosen), 'island groups after keys', len(groups), 'islands', len(isl))

mat = build(chosen); tl = tiles_of(mat)
# ---------- 3D ----------
def extrude(poly, z0, z1):
    rr = []
    for q in comps(poly):
        rr.append(np.array(q.exterior.coords)[:-1])
        for h in q.interiors: rr.append(np.array(h.coords)[:-1])
    return Manifold.extrude(CrossSection(rr, FillRule.EvenOdd), z1 - z0).translate([0, 0, z0])
def to_trimesh(m):
    mm = m.to_mesh(); return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)

import os; os.makedirs(OUT + '/tiles', exist_ok=True)
pockets = unary_union([key_poly(k['p'], k['ang'], CLEAR) for k in chosen])
report = {}; tile_meshes = {}
for (j, i), poly in tl.items():
    pk = pockets.intersection(poly.buffer(1.0) if False else tile_rect(j, i).buffer(CLEAR))
    solid = extrude(poly, 0, T)
    # design coords: front face at z=T (viewer side), back at z=0; pocket cut from the back z in [0,POCKET]
    local = pockets.intersection(box(*poly.bounds).buffer(CLEAR + 1))
    if not local.is_empty: solid = solid - extrude(local, -1, POCKET)
    m = to_trimesh(solid)
    # print orientation: flip so the FRONT face lies on the bed (rotate 180 deg about x), then move to origin
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    m.apply_translation([-m.bounds[0][0], -m.bounds[0][1], -m.bounds[0][2]])
    name = f'e30_r{j}c{i}'
    m.export(f'{OUT}/tiles/{name}.stl'); tile_meshes[(j, i)] = (name, m)
keyman = extrude(Polygon(KEY), 0, KEYT); to_trimesh(keyman).export(OUT + '/e30_key.stl')
pickle.dump(dict(chosen=chosen, XC=XC, YC=YC), open(OUT + '/joints.pkl', 'wb'))

# ---------- verification ----------
checks = []
def chk(name, ok, detail=''): checks.append((name, bool(ok), detail)); print(('PASS' if ok else 'FAIL'), name, detail)
# 1. tiles reproduce the panel: pairwise disjoint, union + seam gap bands == material (with pads)
tiles2d = list(tl.values())
ov = sum(a.intersection(b).area for a, b in itertools.combinations(tiles2d, 2))
chk('tiles do not overlap each other', ov < 1e-6, f'overlap area {ov:.6f} mm2')
bands = unary_union([seam_line(o, c, lo, hi).buffer(GAP, cap_style=2) for o, c, a, b, (lo, hi) in seams])
rest = mat.difference(unary_union(tiles2d)).difference(bands.buffer(1e-6))
chk('tiles + 0.2 mm seam gaps reproduce the whole panel (no missing material)', rest.area < 1e-3, f'unexplained area {rest.area:.6f} mm2')
extra = unary_union(tiles2d).difference(mat.buffer(1e-6))
chk('tiles contain nothing outside the panel', extra.area < 1e-3, f'{extra.area:.6f} mm2')
chk('panel with pads still equals original drawing + pads only', g.difference(mat).area < 1e-6, f'missing original area {g.difference(mat).area:.6f}')
# 2. size
W_asm = mat.bounds[2] - mat.bounds[0]; H_asm = mat.bounds[3] - mat.bounds[1]
chk('assembled size 900 mm wide', abs(W_asm - 900) < 0.05, f'{W_asm:.2f} x {H_asm:.2f} mm')
for (j, i), (name, m) in tile_meshes.items():
    e = m.extents
    chk(f'{name}: fits plate {PLATE[0]:.0f}x{PLATE[1]:.0f}', e[0] <= PLATE[0] and e[1] <= PLATE[1], f'{e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f}')
    shells = m.split(only_watertight=False)
    chk(f'{name}: watertight, outward normals, no degenerate faces', m.is_watertight and m.is_winding_consistent and m.volume > 0 and (m.area_faces < 1e-9).sum() == 0, f'{len(shells)} shell(s), vol {m.volume/1000:.1f} cm3')
# 3. joints
back_layer = {t: tl[t].difference(pockets) for t in tl}     # material present in the back layer (z < POCKET) after pockets
front_cover = unary_union(tiles2d).union(bands)
for n, k in enumerate(chosen):
    key = key_poly(k['p'], k['ang']); pk = key_poly(k['p'], k['ang'], CLEAR)
    coll = key.intersection(unary_union(list(back_layer.values()))).area
    dist = key.distance(unary_union(list(back_layer.values())))
    covered = pk.difference(front_cover).area
    ring = pk.buffer(MINW).difference(pk)
    wall_ok = ring.difference(mat.union(bands)).area
    chk(f'key {n+1} ({k["o"]} seam @ {k["p"][0]:.0f},{k["p"][1]:.0f}): key fits its pocket, clearance >= {CLEAR-0.01:.2f} mm', coll < 1e-9 and dist >= CLEAR - 0.01, f'collision {coll:.6f} mm2, min clearance {dist:.3f} mm')
    chk(f'key {n+1}: front skin closed behind pocket', covered < 1e-6, f'open area {covered:.6f}')
    chk(f'key {n+1}: walls around pocket >= {MINW} mm', wall_ok < 1e-6, f'thin area {wall_ok:.6f}')
    ta, tb = tl[k['a']], tl[k['b']]
    chk(f'key {n+1}: pocket spans both tiles', pk.intersection(ta).area > 20 and pk.intersection(tb).area > 20, f'{pk.intersection(ta).area:.0f} / {pk.intersection(tb).area:.0f} mm2')
# 4. min width (opening test) on each tile
r = MINW/2 - 0.05
lost = sum(p.difference(p.buffer(-r).buffer(r)).area for p in tiles2d)
big = 0
for p in tiles2d:
    d = p.difference(p.buffer(-r).buffer(r)); big += sum(1 for q in comps(d) if q.area > 2)
chk(f'every printed line >= {MINW} mm (opening test)', big == 0, f'{big} regions >2 mm2 fail; corner rounding area {lost:.0f} mm2')
unres = [k for a, b, k in island_graph(chosen)[1] if a is None or b is None]
chk('every key has material on both sides of its seam', not unres, f'{len(unres)} unresolved')
# 5. assembled connectivity via keys
chk('assembled panel is ONE connected body through the keyed joints', len(groups) == 1, f'{len(isl)} islands -> {len(groups)} group(s)')
small = [(k, q.area) for k, q in isl.items() if q.area < 100]
print('small islands (<100 mm2):', len(small), [(k, round(a, 1)) for k, a in small][:10])

# ---------- preview ----------
fig, ax = plt.subplots(figsize=(15, 9.6), dpi=130)
cols = ['#c0392b', '#e67e22', '#27ae60', '#2980b9', '#8e44ad', '#16a085']
for n, ((j, i), poly) in enumerate(tl.items()):
    for q in comps(poly):
        ax.fill(*q.exterior.xy, fc=cols[n % 6], ec='none')
        for h in q.interiors: ax.fill(*h.xy, fc='white', ec='none')
for pk in comps(pockets): ax.fill(*pk.exterior.xy, fc='white', ec='black', lw=0.6)
for o, c, a, b, (lo, hi) in seams:
    xx, yy = ([c, c], [lo, hi]) if o == 'v' else ([lo, hi], [c, c]); ax.plot(xx, yy, color='k', lw=0.5, ls='--', alpha=0.5)
ax.set_xlim(-5, 905); ax.set_ylim(-5, H + 5); ax.set_aspect('equal'); ax.axis('off')
ax.set_title(f'E30 wall art: 6 tiles + {len(chosen)} bow-tie keys (white = key pockets cut from the back)')
fig.savefig(OUT + '/assembled_preview.png', bbox_inches='tight')

allok = all(ok for _, ok, _ in checks)
json.dump(dict(checks=[(n, ok, d) for n, ok, d in checks], keys=[dict(o=k['o'], p=[round(k['p'][0], 1), round(k['p'][1], 1)]) for k in chosen], all_ok=allok), open(OUT + '/report.json', 'w'), indent=1)
print('ALL PASS' if allok else 'SOME CHECKS FAILED', len(checks), 'checks')
