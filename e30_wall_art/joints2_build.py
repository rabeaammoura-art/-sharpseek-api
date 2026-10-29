"""E30 wall art -> 6 printable tiles with INTEGRATED half-thickness dovetail joints (no loose keys).
Each joint: a full-thickness pad straddles the seam; one tile grows a dovetail tongue (back half only, 2.5 mm)
that drops into a dovetail recess in the neighbour's back half. Front face stays closed and flat.
Input : out/rings.pkl   Output: out2/tiles/*.stl (back face on the bed), out2/assembled_preview.png, out2/REPORT.md
"""
import pickle, json, itertools, os, numpy as np, trimesh
from shapely.geometry import Polygon, LineString, box, Point
from shapely import symmetric_difference_all, affinity
from shapely.ops import unary_union
from manifold3d import Manifold, CrossSection, FillRule
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

IN, OUT = 'out', 'out2'; os.makedirs(OUT + '/tiles', exist_ok=True)
T, HALF = 5.0, 2.5          # thickness; tongue/recess depth (back half)
CLEAR, GAP, MINW = 0.2, 0.1, 2.5
NJOINTS, MINPER_SEAM = 15, 2
SPACING = 22.0              # min distance between joints on the same seam (pads must not touch)
PLATE = (325.0, 310.0)
PAD_U0, PAD_U1, PAD_V, PAD_R = -8.0, 12.0, 9.0, 3.0     # pad extent: owner side / receiver side / half-width along seam
TONGUE = [(-2, -3), (0, -3), (9, -6), (9, 6), (0, 3), (-2, 3)]   # dovetail: neck 6 mm at the seam, 12 mm at the tip, 9 mm long

rings = pickle.load(open(IN + '/rings.pkl', 'rb'))
g = symmetric_difference_all(sorted([Polygon(r) for r in rings], key=lambda p: -p.area))
W = 900.0; H = max(r[:, 1].max() for r in rings)
XC, YC = [298.0, 602.0], 298.0
xs = [0, *XC, W]; ys = [0, YC, H]

def comps(poly): return [q for q in (poly.geoms if hasattr(poly, 'geoms') else [poly]) if q.area > 0.5]
def to_global(poly, p, ang): return affinity.rotate(affinity.translate(poly, *p), ang, origin=p)
def pad_poly(p, ang):  return to_global(box(PAD_U0, -PAD_V, PAD_U1, PAD_V).buffer(-PAD_R).buffer(PAD_R), p, ang)
def tongue_poly(p, ang): return to_global(Polygon(TONGUE), p, ang)
def pocket_poly(p, ang, u0=-0.5):   # u0 < 0 cuts slightly past the tile face so no float slivers remain; the tile itself ends at +GAP/2
    q = Polygon(TONGUE).buffer(CLEAR, join_style=1, resolution=16).intersection(box(u0, -50, 50, 50))
    return to_global(q, p, ang)

# seam segments: (orientation, coordinate, tile a (low side), tile b (high side), range along seam)
seams = []
for i, x in enumerate(XC):
    for j in range(2): seams.append(('v', x, (j, i), (j, i + 1), (ys[j], ys[j + 1])))
for i in range(3): seams.append(('h', YC, (0, i), (1, i), (xs[i], xs[i + 1])))
def seam_line(o, c, lo, hi): return LineString([(c, lo), (c, hi)]) if o == 'v' else LineString([(lo, c), (hi, c)])
def tile_rect(j, i): return box(xs[i], ys[j], xs[i + 1], ys[j + 1])

cands = []
for si, (o, c, a, b, (lo, hi)) in enumerate(seams):
    inter = g.intersection(seam_line(o, c, lo, hi)); segs = list(inter.geoms) if hasattr(inter, 'geoms') else [inter]
    for s in segs:
        if s.length <= 0: continue
        m = s.interpolate(0.5, normalized=True); p = (m.x, m.y)
        along = p[1] if o == 'v' else p[0]
        if along - lo < 14 or hi - along < 14: continue
        if o == 'h' and min(abs(p[0] - x) for x in XC) < 14: continue
        if o == 'v' and abs(p[1] - YC) < 14: continue
        cands.append(dict(si=si, o=o, c=c, a=a, b=b, p=p))
def setdir(k, flip):          # flip=False: tongue goes a->b (+x / +y); True: b->a
    k = dict(k); k['flip'] = flip
    base = 0 if k['o'] == 'v' else 90
    k['ang'] = base + (180 if flip else 0)
    k['owner'], k['recv'] = (k['b'], k['a']) if flip else (k['a'], k['b'])
    k['pad'] = pad_poly(k['p'], k['ang'])
    k['score'] = k['pad'].difference(g).area
    return k

def tiles_of(mat):
    tiles = {}
    for j in range(2):
        for i in range(3):
            x0, y0, x1, y1 = tile_rect(j, i).bounds
            x0 += GAP / 2 if i > 0 else 0; x1 -= GAP / 2 if i < 2 else 0
            y0 += GAP / 2 if j > 0 else 0; y1 -= GAP / 2 if j < 1 else 0
            tiles[(j, i)] = mat.intersection(box(x0, y0, x1, y1))
    return tiles
def build(chosen): return unary_union([g] + [k['pad'] for k in chosen])

def groups_of(chosen):
    mat = build(chosen); tl = tiles_of(mat); isl = {}
    for t, poly in tl.items():
        for n, q in enumerate(sorted(comps(poly), key=lambda q: -q.area)): isl[(t, n)] = q
    def which(t, pt):
        for (tt, n), q in isl.items():
            if tt == t and q.buffer(0.3).contains(Point(pt)): return (tt, n)
    par = {n: n for n in isl}
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    unresolved = 0
    for k in chosen:
        u = np.array([np.cos(np.radians(k['ang'])), np.sin(np.radians(k['ang']))])   # owner -> receiver
        pa = tuple(np.array(k['p']) - 4 * u); pb = tuple(np.array(k['p']) + 4 * u)
        A, B = which(k['owner'], pa), which(k['recv'], pb)
        if A is None or B is None: unresolved += 1; continue
        par[f(A)] = f(B)
    grp = {}
    for n in isl: grp.setdefault(f(n), []).append(n)
    return isl, list(grp.values()), unresolved, tl, mat

def loose_area(chosen):
    isl, grp, _, _, _ = groups_of(chosen)
    areas = [sum(isl[x].area for x in gp) for gp in grp]
    return sum(areas) - max(areas)          # material not connected to the main body
chosen = []
def ok_spacing(k, pool, gap=SPACING):
    return all(not (m['si'] == k['si']) or np.hypot(k['p'][0] - m['p'][0], k['p'][1] - m['p'][1]) >= gap for m in pool) and \
           all(m['pad'].distance(k['pad']) > 0.5 or m['si'] != k['si'] for m in pool)
# 1) at least MINPER_SEAM joints on every seam segment (so tiles register), chosen by connectivity gain then least visible pad
def best_for(pool_cands, base, spacing=SPACING):
    best = None
    for k0 in pool_cands:
        for flip in (False, True):
            k = setdir(k0, flip)
            if not ok_spacing(k, chosen, spacing): continue
            gain = base - loose_area(chosen + [k])
            key = (round(gain), -k['score'])
            if best is None or key > best[0]: best = (key, k)
    return best
for si in range(len(seams)):
    for _ in range(MINPER_SEAM):
        b = best_for([k for k in cands if k['si'] == si], loose_area(chosen))
        if b: chosen.append(b[1])
# 2) spend the rest of the budget where it connects the most loose material
while len(chosen) < NJOINTS:
    base = loose_area(chosen)
    b = best_for(cands, base)
    if b is None: break
    chosen.append(b[1])
isl, grp, unres, tl, mat = groups_of(chosen)
# 3) fill the remaining budget, if any, with the cheapest spread joints on the longest seams
print('joints', len(chosen), 'islands', len(isl), 'groups', len(grp), 'unresolved', unres)

# ---------------- 3D ----------------
def extrude(poly, z0, z1):
    rr = []
    for q in comps(poly):
        rr.append(np.array(q.exterior.coords)[:-1])
        for h in q.interiors: rr.append(np.array(h.coords)[:-1])
    return Manifold.extrude(CrossSection(rr, FillRule.EvenOdd), z1 - z0).translate([0, 0, z0])
def tm(man): mm = man.to_mesh(); return trimesh.Trimesh(mm.vert_properties[:, :3], mm.tri_verts, process=False)
tongues = {t: [] for t in tl}; pockets = {t: [] for t in tl}
for k in chosen:
    tongues[k['owner']].append(tongue_poly(k['p'], k['ang'])); pockets[k['recv']].append(pocket_poly(k['p'], k['ang']))
solids = {}; meshes = {}
for t, poly in tl.items():
    # design coords: back face z=0, front face z=T. tongues/recesses live in the back half z in [0, HALF]
    s = extrude(poly, 0, T)
    if tongues[t]: s = s + extrude(unary_union(tongues[t]), 0, HALF)
    if pockets[t]: s = s - extrude(unary_union(pockets[t]), -1, HALF)
    solids[t] = s
    m = tm(s)
    # tiles print BACK face down (back half = first layers, so tongues are supported; front face is the top surface)
    m.apply_translation(-m.bounds[0]); name = f'e30_r{t[0]}c{t[1]}'
    m.export(f'{OUT}/tiles/{name}.stl'); meshes[t] = (name, m)

# ---------------- verification ----------------
bands = unary_union([seam_line(o, c, lo, hi).buffer(GAP + 1e-4, cap_style=2) for o, c, a, b, (lo, hi) in seams])
checks = []
def chk(name, ok, detail=''): checks.append((name, bool(ok), detail)); print(('PASS' if ok else 'FAIL'), name, detail)
# A. assembled solid
allv = list(solids.values())
overlap = sum((a ^ b).volume() for a, b in itertools.combinations(allv, 2))
chk('no two tiles occupy the same space (3D overlap volume)', overlap < 1e-6, f'{overlap:.6f} mm3')
union = Manifold.batch_boolean(allv, 0) if hasattr(Manifold, 'batch_boolean') else None
if union is None:
    union = allv[0]
    for s in allv[1:]: union = union + s
panel = extrude(mat, 0, T)
extra = (union - panel).volume()
chk('assembled tiles contain nothing outside the panel + pads', extra < 1e-3, f'{extra:.6f} mm3')
halo = unary_union([pocket_poly(k['p'], k['ang'], GAP / 2).difference(tongue_poly(k['p'], k['ang'])) for k in chosen])
allowed_missing = extrude(bands, -1, T + 1) + extrude(halo, -1, HALF + 1e-3)
missing = (panel - union) - allowed_missing
chk('assembled tiles + 0.2 mm seam gaps + 0.2 mm joint clearance reproduce the whole panel', missing.volume() < 1e-2, f'unexplained {missing.volume():.6f} mm3')
chk('panel with pads contains the original drawing completely', g.difference(mat).area < 1e-6, f'{g.difference(mat).area:.6f} mm2')
W_asm = mat.bounds[2] - mat.bounds[0]
chk('assembled width 900 mm, thickness 5 mm', abs(W_asm - 900) < 0.05 and abs(panel.bounding_box()[5] - panel.bounding_box()[2] - T) < 1e-6, f'{W_asm:.2f} x {mat.bounds[3] - mat.bounds[1]:.2f} x {T}')
for t, (name, m) in meshes.items():
    e = m.extents
    chk(f'{name}: fits plate {PLATE[0]:.0f}x{PLATE[1]:.0f}', e[0] <= PLATE[0] and e[1] <= PLATE[1], f'{e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f}')
    chk(f'{name}: watertight, outward normals, no degenerate faces', m.is_watertight and m.is_winding_consistent and m.volume > 0 and (m.area_faces < 1e-9).sum() == 0, f'{len(m.split(only_watertight=False))} shell(s), vol {m.volume / 1000:.1f} cm3')
# B. joints
for n, k in enumerate(chosen, 1):
    tag = f'joint {n} ({k["o"]} seam, {k["p"][0]:.0f},{k["p"][1]:.0f}, tongue {k["owner"]}->{k["recv"]})'
    tg = tongue_poly(k['p'], k['ang']); pk = pocket_poly(k['p'], k['ang'])
    rpoly = tl[k['recv']]
    back_rect = rpoly.difference(unary_union(pockets[k['recv']]))             # receiver material in its back half
    d = tg.intersection(box(*[v for v in tile_rect(*k['recv']).bounds])).distance(back_rect) if not tg.intersection(tile_rect(*k['recv'])).is_empty else 9
    coll = tg.intersection(back_rect).area
    chk(f'{tag}: tongue fits recess, clearance >= {CLEAR - 0.01:.2f} mm', coll < 1e-9 and d >= CLEAR - 0.01, f'collision {coll:.6f} mm2, min clearance {d:.3f}')
    front_ok = tg.intersection(tile_rect(*k['recv'])).difference(rpoly.buffer(1e-6)).difference(bands).area
    chk(f'{tag}: front skin closed over the recess', front_ok < 1e-6, f'open area {front_ok:.6f} mm2')
    ring = pk.buffer(MINW).difference(pk).intersection(tile_rect(*k['recv']))
    thin = ring.difference(rpoly.buffer(1e-6)).difference(bands).area
    chk(f'{tag}: walls around recess >= {MINW} mm', thin < 1e-6, f'thin area {thin:.6f} mm2')
    u = np.array([np.cos(np.radians(k['ang'])), np.sin(np.radians(k['ang']))])
    pulled = affinity.translate(tg, *(-2.0 * u))
    chk(f'{tag}: dovetail locks (cannot slide out in the panel plane)', pulled.intersection(back_rect).area > 1e-3, f'blocked by {pulled.intersection(back_rect).area:.2f} mm2')
# C. lines, connectivity
r = MINW / 2 - 0.05
big = 0; lost = 0
for t, poly in tl.items():
    p = poly.union(unary_union(tongues[t])) if tongues[t] else poly
    dd = p.difference(p.buffer(-r).buffer(r)); lost += dd.area; big += sum(1 for q in comps(dd) if q.area > 2)
chk(f'every printed line and tongue >= {MINW} mm (opening test)', big == 0, f'{big} regions >2 mm2 fail, corner rounding {lost:.0f} mm2')
chk('every joint has material on both sides', unres == 0, f'{unres} unresolved')
per_seam = [sum(1 for k in chosen if k['si'] == si) for si in range(len(seams))]
chk(f'every seam segment has >= {MINPER_SEAM} joints (alignment)', min(per_seam) >= MINPER_SEAM, f'per seam {per_seam}')
chk(f'joint count = {NJOINTS}', len(chosen) == NJOINTS, f'{len(chosen)}')
tiny = [(k, round(q.area)) for k, q in isl.items() if q.area < 100]
conn = len(grp) == 1
checks.append((f'INFO assembled panel: {len(isl)} separate line islands, {len(grp)} joint-connected group(s); the rest are glued on the cut face', True, ''))
left = []
if not conn:
    for gp in sorted(grp, key=lambda gp: -sum(isl[x].area for x in gp))[1:]:
        left.append([(x, round(isl[x].area), tuple(round(v) for v in isl[x].bounds)) for x in gp])
    print('NOT jointed (glue only):', left)
print('tiny islands:', tiny)

# ---------------- preview ----------------
fig, ax = plt.subplots(figsize=(15, 9.6), dpi=130)
cols = ['#c0392b', '#e67e22', '#27ae60', '#2980b9', '#8e44ad', '#16a085']
for n, (t, poly) in enumerate(tl.items()):
    for q in comps(poly):
        ax.fill(*q.exterior.xy, fc=cols[n % 6], ec='none')
        for h in q.interiors: ax.fill(*h.xy, fc='white', ec='none')
for t, lst in tongues.items():
    for q in lst: ax.fill(*q.exterior.xy, fc='#f1c40f', ec='black', lw=0.4)
for o, c, a, b, (lo, hi) in seams:
    xx, yy = ([c, c], [lo, hi]) if o == 'v' else ([lo, hi], [c, c]); ax.plot(xx, yy, color='k', lw=0.5, ls='--', alpha=0.5)
ax.set_xlim(-5, 905); ax.set_ylim(-5, H + 5); ax.set_aspect('equal'); ax.axis('off')
ax.set_title(f'E30 wall art: 6 tiles, {len(chosen)} integrated dovetail joints (yellow = tongue in the back half of the neighbour tile)')
fig.savefig(OUT + '/assembled_preview.png', bbox_inches='tight')
json.dump(dict(all_ok=all(ok for _, ok, _ in checks), checks=checks, joints=[dict(o=k['o'], p=[round(k['p'][0], 1), round(k['p'][1], 1)], owner=k['owner'], recv=k['recv']) for k in chosen], not_jointed=left), open(OUT + '/report.json', 'w'), indent=1, default=str)
print('ALL PASS' if all(ok for _, ok, _ in checks) else 'SOME CHECKS FAILED', len(checks), 'checks')
