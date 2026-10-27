"""Hollow the teddy: constant wall, internal vertical pillars + 45-degree (diamond) beams, protected zones around the
LED recess / pocket / cable path.  Voxel distance field + marching cubes, then a boolean difference."""
import numpy as np
import trimesh
from scipy.ndimage import distance_transform_edt
from skimage import measure
from heart import X0

H = 0.5
WALL = 2.0
PROTECT_WALL = 3.0
PITCH = 28.0
PILLAR_R = 3.0
BEAM_R = 3.5          # half diagonal of the diamond beam
BEAM_DZ = 40.0
Y0C = 838.8


def occupancy(mesh, lo, hi, h=H):
    xs = np.arange(lo[0], hi[0], h) + h / 2 + 0.0137
    ys = np.arange(lo[1], hi[1], h) + h / 2 + 0.0071
    zs = np.arange(lo[2], hi[2], h) + h / 2
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    o = np.c_[X.ravel(), Y.ravel(), np.full(X.size, lo[2] - 5.0)]
    loc, ir, _ = mesh.ray.intersects_location(o, np.tile([0, 0, 1.0], (len(o), 1)), multiple_hits=True)
    order = np.lexsort((loc[:, 2], ir)); loc = loc[order]; ir = ir[order]
    occ = np.zeros((len(xs), len(ys), len(zs)), bool).reshape(-1, len(zs))
    starts = np.r_[0, np.where(np.diff(ir) != 0)[0] + 1]; ends = np.r_[starts[1:], len(ir)]
    for s, e in zip(starts, ends):
        z = loc[s:e, 2]
        if len(z) % 2: z = z[:-1]
        for a, b in zip(z[0::2], z[1::2]):
            occ[ir[s], np.searchsorted(zs, a):np.searchsorted(zs, b)] = True
    return occ.reshape(len(xs), len(ys), len(zs)), xs, ys, zs


def cavity_field(occ, xs, ys, zs, h=H):
    depth = distance_transform_edt(occ) * h - h / 2
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing='ij')
    protect_box = (((X > 815) & (X < 908) & (Y > 770) & (Y < 796) & (Z > 10) & (Z < 100)) |
                   ((X > 848) & (X < 876) & (Y > 790) & (Y < 925) & (Z < 66)))
    pair = (~occ) & protect_box
    dprot = distance_transform_edt(~pair) * h - h / 2
    f = np.minimum(depth - WALL, dprot - PROTECT_WALL)
    # pillars (vertical) and diamond beams
    wrap = lambda v, c, p: ((v - c + p / 2) % p) - p / 2
    dx = wrap(X, X0, PITCH); dy = wrap(Y, Y0C, PITCH); dz = wrap(Z, 15.0, BEAM_DZ)
    pillar = np.hypot(dx, dy) - PILLAR_R
    beam_x = np.abs(dy) + np.abs(dz) - BEAM_R          # beams running along x
    beam_y = np.abs(dx) + np.abs(dz) - BEAM_R          # beams running along y
    f = np.minimum(f, np.minimum(pillar, np.minimum(beam_x, beam_y)))
    return f.astype(np.float32)


def cavity_mesh(f, xs, ys, zs, h=H, min_volume=500.0):
    f = np.pad(f, 1, constant_values=-1.0)
    verts, faces, _, _ = measure.marching_cubes(f, level=0.0, spacing=(h, h, h))
    verts += np.array([xs[0] - h, ys[0] - h, zs[0] - h])
    m = trimesh.Trimesh(verts, faces, process=True)
    parts = [p for p in m.split(only_watertight=False) if abs(p.volume) > min_volume]
    for p in parts:
        p.fix_normals()
        if p.volume < 0:
            p.invert()
    return parts
