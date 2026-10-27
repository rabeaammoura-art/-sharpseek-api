"""Rebuild the chest-heart lid + body from Manus' v2 files and the ORIGINAL 200 mm bear.

Fixes: clean geometric heart outline (two round lobes + tangent sides + rounded cleft/tip), smooth pocket, 7 mm LED recess,
uniform 2.0 mm lid shell (front face = Manus' lid dome, low-passed), cable channel that starts behind the pocket floor,
trench to the rear edge, pins + bosses with bores, and removal of the feather edges the pocket leaves in the bear's surface.
Nothing is written over the inputs.

usage: python fix_manus.py <original bear stl> <manus lid stl> <out dir>
"""
import sys
import time

import numpy as np
import shapely
import trimesh
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
from shapely.geometry import Point
from shapely.ops import unary_union
from skimage import measure
import manifold3d as m3d

sys.path.insert(0, '.')
from teddy_edit import boolean, prism_xz   # noqa: E402

ORIG, LID, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
X0 = 84.5                    # heart centre line
LED_C = (84.6, 63.6)         # LED recess centre (x, z)
FLOOR_Y = 78.0               # pocket floor
RECESS_R, RECESS_D = 16.5, 7.0
CH_R, CH_Y, CH_TOP = 6.0, 87.0, 60.0
TR_W, TR_D = 12.0, 5.0
PINS = [(68.0, 74.0), (101.0, 74.0)]
PIN_R, PIN_TIP_Y = 2.4, 67.5
BOSS_R, BORE_R, BORE_Y = 5.0, 3.0, 66.0
WALL = 2.0
SIDE_CLEAR = 0.30
H = 0.2
HEART_W, HEART_TOP, HEART_TIP = 85.0, 94.0, 26.5   # outline: width, top of the lobes, tip (z, mm)
LOBE_R, TIP_R, CLEFT_R = 22.0, 6.0, 5.0            # lobe radius and the fillet radii of the tip and the cleft
SMOOTH_MM = 3.5               # low-pass of the dome surface (removes the faceting of the source mesh)
SLIVER_R = 1.3                # material thinner than 2*SLIVER_R next to the pocket is removed (feather edges)
SLIVER_BAND = 8.0             # ... within this distance of the pocket wall
EDGE_R = 4.0                 # radius of the rounded edge all around the heart
t0 = time.time()
log = lambda *a: print('[%4.0fs]' % (time.time() - t0), *a, flush=True)


def simplify(m, tol):
    mf = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32),
                               tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    mm = mf.simplify(tol).to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3].astype(float), np.asarray(mm.tri_verts), process=True)


def snap32(m):
    r = trimesh.Trimesh(np.asarray(m.vertices, dtype=np.float32).astype(np.float64), m.faces, process=True)
    r.update_faces(r.nondegenerate_faces()); r.remove_unreferenced_vertices()
    if not r.is_watertight:
        trimesh.repair.fill_holes(r); trimesh.repair.fix_normals(r)
    return r


def save(m, path):
    log('before save: watertight', m.is_watertight, 'volume-ok', m.is_volume, 'tiny faces', int((m.area_faces < 1e-6).sum()))
    m.export(path); c = trimesh.load(path)
    if not (c.is_watertight and c.is_volume):
        e = np.sort(c.edges, axis=1); u, cn = np.unique(e, axis=0, return_counts=True)
        log('reloaded: open edges', int((cn == 1).sum()), 'nonmanifold', int((cn > 2).sum()), 'winding', c.is_winding_consistent)
    ok = c.is_watertight and c.is_winding_consistent and c.is_volume
    log('saved', path, len(c.faces), 'faces', 'OK' if ok else 'NOT A CLEAN VOLUME', 'volume %.1f cm3' % (c.volume / 1000))
    if not ok:
        raise SystemExit('export check failed')


def y_cyl(r, y0, y1, x, z, sections=96):
    c = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([x, (y0 + y1) / 2, z]); return c


def rmin(a, b, r):
    """Intersection of two inside-positive distance fields with a circular fillet of radius r (r<=0: sharp)."""
    if r <= 0:
        return np.minimum(a, b)
    both = (a < r) & (b < r)
    return np.where(both, r - np.sqrt((r - a) ** 2 + (r - b) ** 2), np.minimum(a, b))


def heart_outline():
    ax, zc = HEART_W / 2 - LOBE_R, HEART_TOP - LOBE_R
    tip = Point(X0, HEART_TIP)
    discs = [Point(X0 - ax, zc).buffer(LOBE_R, 256), Point(X0 + ax, zc).buffer(LOBE_R, 256)]
    p = unary_union([unary_union([d, tip]).convex_hull for d in discs])      # lobes + tangent sides down to the tip
    p = p.buffer(CLEFT_R, resolution=64).buffer(-CLEFT_R, resolution=64)     # closing: fillet in the cleft
    p = p.buffer(-TIP_R, resolution=64).buffer(TIP_R, resolution=64)         # opening: rounded tip
    return p.simplify(0.005)


def trim_slivers(body, P):
    """Pocket walls cut the bear's curved surface at grazing angles and leave knife edges and thin skins.  Opening the
    material with a ball of radius SLIVER_R inside a band around the pocket removes everything thinner than 2*SLIVER_R."""
    h = 0.25
    xs = np.arange(38.0, 132.0, h); zs = np.arange(24.0, 100.0, h); ys = np.arange(18.0, 82.0, h)
    gx_, gz_ = np.meshgrid(xs, zs, indexing='ij')
    o = np.c_[gx_.ravel(), np.full(gx_.size, 0.0), gz_.ravel()]
    loc, ir, _ = body.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=True)
    order = np.lexsort((loc[:, 1], ir)); ir, ly = ir[order], loc[order, 1]
    first = np.r_[0, np.flatnonzero(np.diff(ir)) + 1]
    rank = np.arange(len(ir)) - np.repeat(first, np.diff(np.r_[first, len(ir)]))
    ev = np.zeros((len(xs), len(ys), len(zs)), np.int8)
    ij, k = np.divmod(ir, len(zs))
    np.add.at(ev, (ij, np.clip(np.searchsorted(ys, ly), 0, len(ys) - 1), k), np.where(rank % 2 == 0, 1, -1).astype(np.int8))
    occ = np.cumsum(ev, axis=1, dtype=np.int8) > 0
    del ev
    dist = shapely.distance(P.buffer(SIDE_CLEAR).exterior, shapely.points(gx_.ravel(), gz_.ravel())).reshape(gx_.shape)
    band = (dist < SLIVER_BAND) & ~shapely.contains_xy(P.buffer(SIDE_CLEAR), gx_.ravel(), gz_.ravel()).reshape(gx_.shape)
    eroded = distance_transform_edt(occ) > SLIVER_R / h
    kept = distance_transform_edt(~eroded) <= SLIVER_R / h                       # the opened material
    rem = occ & ~kept & band[:, None, :]
    log('sliver material to remove: %.1f mm3' % (rem.sum() * h ** 3))
    cut = rem | (binary_dilation(rem, iterations=3) & ~occ)                    # reach out into the air so the boolean cuts cleanly
    cut = np.pad(gaussian_filter(cut.astype(np.float32), 1.0), 1)
    v, f, _, _ = measure.marching_cubes(cut, 0.5, spacing=(h, h, h))
    v += np.array([xs[0] - h, ys[0] - h, zs[0] - h])
    pieces = []
    for c in trimesh.Trimesh(v, f, process=True).split(only_watertight=False):
        c.fix_normals()
        if c.volume < 0: c.invert()
        if c.is_volume and c.volume > 0.5: pieces.append(c)
    log('sliver tool: %d pieces, body is_volume %s' % (len(pieces), body.is_volume))
    return boolean('difference', [body] + pieces)


orig = trimesh.load(ORIG); F = trimesh.load(LID)
# ---------------------------------------------------------------- outline
P = heart_outline()
log('lid outline: bounds', np.round(P.bounds, 2).tolist(), 'area %.0f' % P.area)
for px, pz in PINS + [LED_C]:
    log('  clearance of (%.0f, %.0f) to the outline: %.1f mm' % (px, pz, shapely.distance(P.exterior, shapely.points(px, pz))))

# ---------------------------------------------------------------- lid from fields (exact front surface, 2 mm shell)
xs = np.arange(40.0, 129.0, H); zs = np.arange(22.0, 100.0, H); ys = np.arange(18.0, 80.0, H)
XX, ZZ = np.meshgrid(xs, zs, indexing='ij')
o = np.c_[XX.ravel(), np.full(XX.size, 0.0), ZZ.ravel()]
loc, ir, _ = F.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=False)
yf = np.full(XX.size, np.nan); yf[ir] = loc[:, 1]; yf = yf.reshape(XX.shape)
hole = ~np.isfinite(yf)
idx = distance_transform_edt(hole, return_distances=False, return_indices=True)
yf = yf[tuple(idx)]
yf = gaussian_filter(yf, SMOOTH_MM / H)                                   # removes the faint faceting of the source surface
gx, gz = np.gradient(yf, H)
sdf = np.where(shapely.contains_xy(P, XX.ravel(), ZZ.ravel()), 1.0, -1.0) * shapely.distance(
    P.exterior, shapely.points(XX.ravel(), ZZ.ravel()))
sdf = sdf.reshape(XX.shape)
sl = np.sqrt(1 + gx ** 2 + gz ** 2)
Yv = ys[None, :, None]
a_n = (Yv - yf[:, None, :]) / sl[:, None, :]                        # distance to the front surface (along its normal)
b_n = sdf[:, None, :]                                                # distance to the heart outline (side wall)
outer = np.minimum(rmin(a_n, b_n, EDGE_R), FLOOR_Y - Yv)             # rounded edge, flat rim plane
cavity = rmin(a_n - WALL, b_n - WALL, EDGE_R - WALL)                 # offset of the rounded edge: wall stays 2 mm
L = np.minimum(outer, -cavity)
Xg = xs[:, None, None]; Zg = zs[None, None, :]
for px, pz in PINS:
    r = np.hypot(Xg - px, Zg - pz)
    boss = np.minimum(np.minimum(BOSS_R - r, Yv - (yf[:, None, :] + 0.8)), FLOOR_Y - Yv)
    L = np.maximum(L, boss)
for px, pz in PINS:
    r = np.hypot(Xg - px, Zg - pz)
    L = np.minimum(L, -np.minimum(BORE_R - r, Yv - BORE_Y))
log('lid field ready', L.shape)
Lp = np.pad(L, 1, constant_values=-1.0)
v, f, _, _ = measure.marching_cubes(Lp.astype(np.float32), 0.003, spacing=(H, H, H))   # tiny offset: exact-zero plateaus (rim plane) break the mesh
v += np.array([xs[0] - H, ys[0] - H, zs[0] - H])
lid = trimesh.Trimesh(v, f, process=True)
parts = sorted(lid.split(only_watertight=False), key=lambda p: -abs(p.volume))
lid = parts[0]; lid.fix_normals()
if lid.volume < 0: lid.invert()
lid = simplify(lid, 0.03)
log('lid', len(lid.faces), 'watertight', lid.is_watertight, 'volume %.1f cm3' % (lid.volume / 1000), 'components', len(parts))
save(lid, OUT + 'chest_heart_lid_v5.stl')

# ---------------------------------------------------------------- body from the original bear
pocket = prism_xz(P.buffer(SIDE_CLEAR, resolution=32), -12.0, FLOOR_Y)
recess = y_cyl(RECESS_R, FLOOR_Y - 1.0, FLOOR_Y + RECESS_D, LED_C[0], LED_C[1])
chan = trimesh.creation.cylinder(radius=CH_R, height=CH_TOP + 1.0, sections=96,
                                 transform=trimesh.transformations.translation_matrix([LED_C[0], CH_Y, (CH_TOP - 1.0) / 2]))
trench = trimesh.creation.box(bounds=[[LED_C[0] - TR_W / 2, CH_Y, -1.0], [LED_C[0] + TR_W / 2, 172.0, TR_D]])
body = boolean('difference', [orig, pocket, recess, chan, trench])
body = boolean('union', [body] + [y_cyl(PIN_R, PIN_TIP_Y, FLOOR_Y + 2.0, px, pz, 48) for px, pz in PINS])
body = trim_slivers(body, P)
body = simplify(body, 0.005)
parts = [p for p in body.split(only_watertight=False) if abs(p.volume) > 1000.0]          # drop the stray 0.002 cm3 floating fragment found in the source mesh
body = max(parts, key=lambda p: p.volume)
log('body', len(body.faces), body.is_watertight)
save(body, OUT + 'teddy_body_chest_led_v5.stl')
log('done')
