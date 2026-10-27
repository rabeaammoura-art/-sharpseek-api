"""Rebuild the chest-heart lid + body from Manus' v2 files and the ORIGINAL 200 mm bear.

Fixes: smooth pocket, 7 mm LED recess, uniform 2.0 mm lid shell (front face = Manus' lid front surface), cable channel
that starts behind the pocket floor, trench to the rear edge, pins + bosses with bores.  Nothing is written over the inputs.

usage: python fix_manus.py <original bear stl> <manus lid stl> <out dir>
"""
import sys
import time

import numpy as np
import shapely
import trimesh
from scipy.ndimage import distance_transform_edt, gaussian_filter
from shapely.affinity import scale as sh_scale
from shapely.geometry import Polygon
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
H = 0.25
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


def smooth_outline(poly, harmonics=36):
    ring = np.array(poly.exterior.coords)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))]
    t = np.linspace(0, d[-1], 2048, endpoint=False)
    z = np.interp(t, d, ring[:, 0]) + 1j * np.interp(t, d, ring[:, 1])
    f = np.fft.fft(z); k = np.fft.fftfreq(len(z), 1 / len(z)); f[np.abs(k) > harmonics] = 0
    s = np.fft.ifft(f); p = Polygon(np.c_[s.real, s.imag]).buffer(0)
    return p.intersection(sh_scale(p, xfact=-1, origin=(X0, 0))).simplify(0.01)


orig = trimesh.load(ORIG); F = trimesh.load(LID)
# ---------------------------------------------------------------- outline
sil = unary_union([Polygon(t) for t in F.triangles[:, :, [0, 2]] if Polygon(t).area > 1e-9]).buffer(0.05).buffer(-0.05)
P = smooth_outline(sil)
log('lid outline: bounds', np.round(P.bounds, 2).tolist(), 'area %.0f (silhouette %.0f)' % (P.area, sil.area))

# ---------------------------------------------------------------- lid from fields (exact front surface, 2 mm shell)
xs = np.arange(40.0, 129.0, H); zs = np.arange(22.0, 100.0, H); ys = np.arange(18.0, 80.0, H)
XX, ZZ = np.meshgrid(xs, zs, indexing='ij')
o = np.c_[XX.ravel(), np.full(XX.size, 0.0), ZZ.ravel()]
loc, ir, _ = F.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=False)
yf = np.full(XX.size, np.nan); yf[ir] = loc[:, 1]; yf = yf.reshape(XX.shape)
hole = ~np.isfinite(yf)
idx = distance_transform_edt(hole, return_distances=False, return_indices=True)
yf = yf[tuple(idx)]
yf = gaussian_filter(yf, 1.2)                                   # removes the faint faceting of the source surface
gx, gz = np.gradient(yf, H)
sdf = np.where(shapely.contains_xy(P, XX.ravel(), ZZ.ravel()), 1.0, -1.0) * shapely.distance(
    P.exterior, shapely.points(XX.ravel(), ZZ.ravel()))
sdf = sdf.reshape(XX.shape)
yi = yf + WALL * np.sqrt(1 + gx ** 2 + gz ** 2)
Yv = ys[None, :, None]
L = np.minimum(np.minimum(Yv - yf[:, None, :], FLOOR_Y - Yv), sdf[:, None, :])                 # outer solid
L = np.minimum(L, -np.minimum(Yv - yi[:, None, :], sdf[:, None, :] - WALL))                    # minus cavity
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
save(lid, OUT + 'chest_heart_lid_v3.stl')

# ---------------------------------------------------------------- body from the original bear
pocket = prism_xz(P.buffer(SIDE_CLEAR, resolution=32), -12.0, FLOOR_Y)
recess = y_cyl(RECESS_R, FLOOR_Y - 1.0, FLOOR_Y + RECESS_D, LED_C[0], LED_C[1])
chan = trimesh.creation.cylinder(radius=CH_R, height=CH_TOP + 1.0, sections=96,
                                 transform=trimesh.transformations.translation_matrix([LED_C[0], CH_Y, (CH_TOP - 1.0) / 2]))
trench = trimesh.creation.box(bounds=[[LED_C[0] - TR_W / 2, CH_Y, -1.0], [LED_C[0] + TR_W / 2, 172.0, TR_D]])
body = boolean('difference', [orig, pocket, recess, chan, trench])
body = boolean('union', [body] + [y_cyl(PIN_R, PIN_TIP_Y, FLOOR_Y + 2.0, px, pz, 48) for px, pz in PINS])
body = simplify(body, 0.005)
parts = [p for p in body.split(only_watertight=False) if abs(p.volume) > 1000.0]          # drop the stray 0.002 cm3 floating fragment found in the source mesh
body = max(parts, key=lambda p: p.volume)
log('body', len(body.faces), body.is_watertight)
save(body, OUT + 'teddy_body_chest_led_v3.stl')
log('done')
