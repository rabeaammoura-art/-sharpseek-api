"""Rebuild the chest-heart lid + body from Manus' v2 files and the ORIGINAL 200 mm bear.

Fixes: clean geometric heart outline (two round lobes + tangent sides + rounded cleft/tip), smooth pocket, 7 mm LED recess,
uniform 2.0 mm lid shell (front face = Manus' lid dome, low-passed), cable channel that starts behind the pocket floor,
trench to the rear edge, pins + bosses with bores, and removal of the feather edges the pocket leaves in the bear's surface.
Nothing is written over the inputs.

usage: python fix_manus.py <original bear stl> <manus lid stl> <out dir> [heart outline .dxf (mm; sketch x,y = bear x,z) or - ] [photo for the lithophane]
"""
import sys
import time

import numpy as np
import shapely
import trimesh
from PIL import Image, ImageFilter, ImageOps
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter, map_coordinates
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from skimage import measure
import manifold3d as m3d

sys.path.insert(0, '.')
from teddy_edit import boolean, prism_xz   # noqa: E402

ORIG, LID, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DXF = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None    # your own heart outline replaces the geometric one
PHOTO = sys.argv[5] if len(sys.argv) > 5 else None                         # photo: relief on the inside of the front wall
TAG = 'v7' if PHOTO else ('v6' if DXF else 'v5')
X0 = 84.5                    # heart centre line
LED_C = (84.6, 63.6)         # LED recess centre (x, z)
FLOOR_Y = 78.0               # pocket floor
RECESS_R, RECESS_D = 16.5, 7.0
CH_R, CH_Y, CH_TOP = 6.0, 87.0, 60.0
TR_W, TR_D = 12.0, 5.0
PINS = [(52.0, 70.0), (116.0, 70.0)] if PHOTO else [(68.0, 74.0), (101.0, 74.0)]   # with a photo the pins sit at the rim, away from the picture
PIN_R, PIN_TIP_Y = 2.4, 67.5
BOSS_R, BORE_R, BORE_Y = (4.5 if PHOTO else 5.0), 3.0, 66.0
BOSS_FRONT_Y = 62.0           # with a photo the boss stubs start here, so they never touch the front wall (no dark spots)
T_MIN, T_MAX, GAMMA = 0.8, 3.2, 1.0           # lithophane thickness: bright pixel = thin
PHOTO_BOX = (8, 295, 712, 995)                # the heart inside the photo (px)
RIM_OUT, RIM_IN = 2.0, 5.0                    # photo fades into the plain 2 mm wall within this distance of the outline
WALL = 2.0
SIDE_CLEAR = 0.30
H = 0.2
HEART_W, HEART_TOP, HEART_TIP = 85.0, 94.0, 26.5   # outline: width, top of the lobes, tip (z, mm)
LOBE_R, TIP_R, CLEFT_R = 22.0, 6.0, 5.0            # lobe radius and the fillet radii of the tip and the cleft
SMOOTH_MM = 3.5               # low-pass of the dome surface (removes the faceting of the source mesh)
SLIVER_R = 1.3                # material thinner than 2*SLIVER_R next to the pocket is removed (feather edges)
SLIVER_BAND = 8.0             # ... within this distance of the pocket wall
RIM_SMOOTH = 0.9              # smoothing (mm) of the bear's pebbled surface in that band
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


def drop_nonmanifold(c):
    """Delete the faces on edges shared by more than two faces, then close the (tiny) holes that leaves with triangle fans."""
    e = np.sort(c.edges, axis=1); _, inv, cn = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    keep = np.ones(len(c.faces), bool); keep[np.flatnonzero(cn[inv] > 2) // 3] = False
    f = c.faces[keep]
    de = np.c_[f[:, 0], f[:, 1], f[:, 1], f[:, 2], f[:, 2], f[:, 0]].reshape(-1, 2)
    have = set(map(tuple, de))
    fill = {b: a for a, b in have if (b, a) not in have}                    # needed edge b->a for every boundary edge a->b
    new = []
    while fill:
        v0, v1 = fill.popitem()
        loop = [v0, v1]
        while loop[-1] != loop[0]:
            nxt = fill.pop(loop[-1], None)
            if nxt is None: break
            loop.append(nxt)
        loop = loop[:-1] if loop[-1] == loop[0] else loop
        new += [(loop[0], loop[i], loop[i + 1]) for i in range(1, len(loop) - 1)]
    log('dropped %d faces, closed %d holes with %d triangles' % ((~keep).sum(), 0, len(new)))
    r = trimesh.Trimesh(c.vertices, np.vstack([f, np.array(new, dtype=f.dtype).reshape(-1, 3)]), process=False)
    return r


def save(m, path):
    """Export, reload and check.  A float32 round trip can collapse the tiny triangles the booleans leave at seams; when the
    reloaded file is not a clean volume, the mesh is simplified with a small tolerance and the few faces on the bad edges are
    dropped and their holes closed (a second round trip is exact because the vertices are already float32)."""
    log('before save: watertight', m.is_watertight, 'volume-ok', m.is_volume, 'tiny faces', int((m.area_faces < 1e-6).sum()))
    for tol in (None, 0.001, 0.002, 0.004, 0.008, 0.016):
        cand = m if tol is None else simplify(m, tol)
        for attempt in range(4):
            cand.export(path); c = trimesh.load(path)
            e = np.sort(c.edges, axis=1); u, cn = np.unique(e, axis=0, return_counts=True)
            ok = c.is_watertight and c.is_winding_consistent and c.is_volume
            log('saved', path, len(c.faces), 'faces (simplify %s, repair round %d); reloaded open edges' % (tol, attempt), int((cn == 1).sum()),
                'nonmanifold', int((cn > 2).sum()), 'OK' if ok else 'NOT A CLEAN VOLUME', 'volume %.1f cm3' % (c.volume / 1000))
            if ok:
                return
            cand = drop_nonmanifold(c)
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


def load_dxf_outline(path):
    """First closed LWPOLYLINE of an ASCII DXF as a shapely polygon (x, y of the sketch = x, z of the bear), lightly cleaned."""
    t = [l.strip() for l in open(path, errors='ignore').read().splitlines()]
    i = t.index('LWPOLYLINE'); j = next(k for k in range(i + 1, len(t) - 1) if t[k] == '0' and t[k + 1] in ('ENDSEC', 'LWPOLYLINE', 'LINE', 'SPLINE', 'CIRCLE'))
    xs, ys_ = [], []
    for k in range(i + 1, j, 2):
        if t[k] == '10': xs.append(float(t[k + 1]))
        elif t[k] == '20': ys_.append(float(t[k + 1]))
    p = Polygon(np.c_[xs, ys_]).buffer(0)
    r = 2.0                                                                    # remove polyline kinks: every corner gets radius >= r
    p = p.buffer(r, resolution=32).buffer(-2 * r, resolution=32).buffer(r, resolution=32)
    return p.simplify(0.005)


def heart_outline():
    ax, zc = HEART_W / 2 - LOBE_R, HEART_TOP - LOBE_R
    tip = Point(X0, HEART_TIP)
    discs = [Point(X0 - ax, zc).buffer(LOBE_R, 256), Point(X0 + ax, zc).buffer(LOBE_R, 256)]
    p = unary_union([unary_union([d, tip]).convex_hull for d in discs])      # lobes + tangent sides down to the tip
    p = p.buffer(CLEFT_R, resolution=64).buffer(-CLEFT_R, resolution=64)     # closing: fillet in the cleft
    p = p.buffer(-TIP_R, resolution=64).buffer(TIP_R, resolution=64)         # opening: rounded tip
    return p.simplify(0.005)


def rebuild_rim(body, P):
    """The pocket wall meets the bear's pebbled surface at grazing angles: that leaves knife edges, thin skins and a rim made
    of beads.  In a band around the pocket the bear's surface is rebuilt: (1) material thinner than 2*SLIVER_R is opened away,
    (2) the surface profile is carried 2 mm into the pocket so the smoothing sees no wall, (3) the band is smoothed (RIM_SMOOTH)
    and re-meshed, then swapped in for the old band; the pocket wall plane itself is the cutting plane, so it stays exact."""
    h = 0.25
    xs = np.arange(26.0, 144.0, h); zs = np.arange(14.0, 112.0, h); ys = np.arange(18.0, 80.0, h)       # covers the whole band
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
    Pk = P.buffer(SIDE_CLEAR, resolution=32)
    dist = shapely.distance(Pk.exterior, shapely.points(gx_.ravel(), gz_.ravel())).reshape(gx_.shape)
    inside = shapely.contains_xy(Pk, gx_.ravel(), gz_.ravel()).reshape(gx_.shape)
    band = ~inside & (dist < SLIVER_BAND)
    eroded = distance_transform_edt(occ) > SLIVER_R / h
    kept = distance_transform_edt(~eroded) <= SLIVER_R / h                       # the opened material
    del eroded
    rem = occ & ~kept & band[:, None, :]
    log('sliver material to remove: %.1f mm3' % (rem.sum() * h ** 3))
    occ &= ~rem
    del kept, rem
    # carry the profile 2 mm into the pocket (nearest column outside the outline), only in front of the floor
    _, (ix, iz) = distance_transform_edt(inside, return_indices=True)
    near = inside & (dist < 2.0)
    front = ys < FLOOR_Y - 0.5
    ext = occ.copy()
    sel = np.flatnonzero(near.ravel())
    ii, kk = np.divmod(sel, near.shape[1])
    for a0 in range(0, len(sel), 4000):                                          # chunks keep the fancy indexing small
        i0, k0 = ii[a0:a0 + 4000], kk[a0:a0 + 4000]
        ext[i0[:, None], np.flatnonzero(front)[None, :], k0[:, None]] = occ[ix[i0, k0][:, None], np.flatnonzero(front)[None, :], iz[i0, k0][:, None]]
    f = gaussian_filter(ext.astype(np.float32), RIM_SMOOTH / h)
    zone_m = (~inside & (dist < SLIVER_BAND + 1.5)) | near
    f *= zone_m[:, None, :]
    del ext
    v, f_, _, _ = measure.marching_cubes(np.pad(f, 1), 0.5, spacing=(h, h, h))
    v += np.array([xs[0] - h, ys[0] - h, zs[0] - h])
    pieces = []
    for c in trimesh.Trimesh(v, f_, process=False).split(only_watertight=False):
        if c.volume < 0: c.invert()
        log('  piece: %d faces, watertight %s, winding %s, volume %.0f mm3' % (len(c.faces), c.is_watertight, c.is_winding_consistent, c.volume))
        if c.is_volume and c.volume > 5.0: pieces.append(simplify(c, 0.02))
    log('band surface: %d closed pieces, %d faces' % (len(pieces), sum(len(c.faces) for c in pieces)))
    zone = prism_xz(Pk.buffer(SLIVER_BAND, resolution=32).difference(Pk.buffer(-0.05)), ys[0], FLOOR_Y - 1.0)   # reaches 0.05 mm into the void: no coplanar faces with the old wall
    zone_new = prism_xz(Pk.buffer(SLIVER_BAND + 0.3, resolution=32).difference(Pk), ys[0] - 0.3, FLOOR_Y - 0.5)   # overlaps the rest of the body by 0.3 mm
    zone = boolean('difference', [zone, trimesh.creation.box(bounds=[[0, -10, -5], [200, 100, 21.5]])])             # the base disc is left alone
    zone_new = boolean('difference', [zone_new, trimesh.creation.box(bounds=[[0, -10, -5], [200, 100, 21.2]])])
    new_band = [c for c in (boolean('intersection', [c, zone_new]) for c in pieces) if len(c.faces) and c.is_volume]
    out = boolean('union', [boolean('difference', [body, zone])] + new_band)
    e = np.sort(out.edges, axis=1); _, cn = np.unique(e, axis=0, return_counts=True)
    log('rebuilt band: watertight %s, open edges %d, non-manifold %d' % (out.is_watertight, (cn == 1).sum(), (cn > 2).sum()))
    return out


orig = trimesh.load(ORIG); F = trimesh.load(LID)
# ---------------------------------------------------------------- outline
P = load_dxf_outline(DXF) if DXF else heart_outline()
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
b_n = sdf[:, None, :]                                                # distance to the heart outline (side wall)
T = np.full(XX.shape, WALL)                                          # wall thickness at every (x, z)
if PHOTO:                                                            # lithophane: bright pixel = thin wall
    ph = ImageOps.autocontrast(Image.open(PHOTO).convert('L'), cutoff=1.5).crop(PHOTO_BOX).filter(ImageFilter.GaussianBlur(1.1))
    ph = np.asarray(ph, dtype=float) / 255.0
    x0, z0, x1, z1 = P.bounds
    lum = map_coordinates(ph, [(z1 - ZZ) / (z1 - z0) * (ph.shape[0] - 1), (XX - x0) / (x1 - x0) * (ph.shape[1] - 1)], order=1, mode='nearest')
    t_photo = T_MIN + (1 - lum) ** GAMMA * (T_MAX - T_MIN)
    wgt = np.clip((sdf - RIM_OUT) / (RIM_IN - RIM_OUT), 0, 1); wgt = wgt * wgt * (3 - 2 * wgt)
    T = WALL + wgt * (t_photo - WALL)
    plt_img = np.clip(np.exp(-0.75 * (T - T_MIN)), 0, 1) * (sdf > 0)    # back-lit look: thin = bright
    Image.fromarray((255 * plt_img.T[::-1]).astype(np.uint8)).save(OUT + 'lithophane_backlit_preview.png')
# The relief is on the OUTSIDE of the front wall (printed facing up, no supports on it); the inner ceiling is a smooth dome
# T_MAX behind the original dome, so the wall thickness is T at every point.
yf_out = yf + (T_MAX - T) if PHOTO else yf
yf_in = yf + T_MAX if PHOTO else yf + WALL
a_out = (Yv - yf_out[:, None, :]) / sl[:, None, :]                   # distance to the outer front surface (along its normal)
a_in = (Yv - yf_in[:, None, :]) / sl[:, None, :]                     # ... and to the smooth inner ceiling
outer = np.minimum(rmin(a_out, b_n, EDGE_R), FLOOR_Y - Yv)           # rounded edge, flat rim plane
cavity = rmin(a_in, b_n - WALL, EDGE_R - WALL)                       # offset of the rounded edge: side wall stays 2 mm
L = np.minimum(outer, -cavity)
Xg = xs[:, None, None]; Zg = zs[None, None, :]
for px, pz in PINS:
    r = np.hypot(Xg - px, Zg - pz)
    boss = np.minimum(np.minimum(BOSS_R - r, Yv - (BOSS_FRONT_Y if PHOTO else yf[:, None, :] + 0.8)), FLOOR_Y - Yv)
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
save(lid, OUT + 'chest_heart_lid_' + TAG + '.stl')

# ---------------------------------------------------------------- body from the original bear
pocket = prism_xz(P.buffer(SIDE_CLEAR, resolution=32), -12.0, FLOOR_Y)
recess = y_cyl(RECESS_R, FLOOR_Y - 1.0, FLOOR_Y + RECESS_D, LED_C[0], LED_C[1])
chan = trimesh.creation.cylinder(radius=CH_R, height=CH_TOP + 1.0, sections=96,
                                 transform=trimesh.transformations.translation_matrix([LED_C[0], CH_Y, (CH_TOP - 1.0) / 2]))
trench = trimesh.creation.box(bounds=[[LED_C[0] - TR_W / 2, CH_Y, -1.0], [LED_C[0] + TR_W / 2, 172.0, TR_D]])
body = boolean('difference', [orig, pocket, recess, chan, trench])
body = boolean('union', [body] + [y_cyl(PIN_R, PIN_TIP_Y, FLOOR_Y + 2.0, px, pz, 48) for px, pz in PINS])
body = simplify(body, 0.005)
body = rebuild_rim(body, P)
parts = [p for p in body.split(only_watertight=False) if abs(p.volume) > 1000.0]          # drop the stray 0.002 cm3 floating fragment found in the source mesh
body = max(parts, key=lambda p: p.volume)
log('body', len(body.faces), body.is_watertight)
save(body, OUT + 'teddy_body_chest_led_' + TAG + '.stl')
log('done')
