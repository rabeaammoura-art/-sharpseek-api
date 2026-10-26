"""Keep the original lithophane (outline, dome, border ring, tongue that locks into the teddy) and replace only the
relief inside the border with a new photo.  Outer-surface vertices are moved along y: y = y_inner - thickness."""
import numpy as np
import trimesh
from scipy.ndimage import distance_transform_edt, map_coordinates

from litho import load_photo, smoothstep

BORDER = (3.6, 5.8)   # mm from the outline: old geometry kept inside the first number, new relief fully on after the second


def swap_relief(old: trimesh.Trimesh, photo_path, crop=(360, 700, 640), gamma=1.0, t_range=None, res=0.1):
    V = old.vertices.copy()
    (x0, _, z0), (x1, _, z1) = old.bounds
    # coverage mask in (x,z) -> distance to the outline
    gx = np.arange(x0 - 1, x1 + 1, res)
    gz = np.arange(z0 - 1, z1 + 1, res)
    X, Z = np.meshgrid(gx, gz)
    o = np.c_[X.ravel(), np.full(X.size, 700.0), Z.ravel()]
    d = np.tile([0, 1.0, 0], (len(o), 1))
    loc, ir, _ = old.ray.intersects_location(o, d, multiple_hits=False)
    cover = np.zeros(X.size, bool)
    cover[ir] = True
    cover = cover.reshape(X.shape)
    edist = distance_transform_edt(cover) * res

    def edge_at(px, pz):
        iu = np.clip(((px - gx[0]) / res).astype(int), 0, len(gx) - 1)
        iv = np.clip(((pz - gz[0]) / res).astype(int), 0, len(gz) - 1)
        return edist[iv, iu]

    # first/second hit along +y for every vertex
    o = np.c_[V[:, 0], np.full(len(V), 700.0), V[:, 2]]
    loc, ir, _ = old.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=True)
    order = np.lexsort((loc[:, 1], ir))
    loc, ir = loc[order], ir[order]
    first = np.full(len(V), np.nan)
    second = np.full(len(V), np.nan)
    start = np.r_[0, np.where(np.diff(ir) != 0)[0] + 1]
    ridx = ir[start]
    first[ridx] = loc[start, 1]
    has2 = np.r_[np.diff(ir) == 0, False][start]
    sec_pos = start[has2] + 1
    second[ir[sec_pos]] = loc[sec_pos, 1]
    on_outer = np.isfinite(first) & np.isfinite(second) & (np.abs(V[:, 1] - first) < 0.05)

    px, pz = V[:, 0], V[:, 2]
    t_old = second - first
    photo = load_photo(photo_path, crop[0], crop[1], crop[2], (x1 - x0) / (z1 - z0))
    ph, pw = photo.shape
    u = (px - x0) / (x1 - x0) * (pw - 1)
    v = (z1 - pz) / (z1 - z0) * (ph - 1)
    Lum = map_coordinates(photo, [v, u], order=1, mode="nearest")
    if t_range is None:
        inner = on_outer & (edge_at(px, pz) > BORDER[1])
        t_range = tuple(np.percentile(t_old[inner], [3, 97]))
    t_new = t_range[0] + (1 - Lum) ** gamma * (t_range[1] - t_range[0])
    w_old = smoothstep(BORDER[1], BORDER[0], edge_at(px, pz))        # 1 near the outline
    t = t_new * (1 - w_old) + t_old * w_old
    V2 = V.copy()
    V2[on_outer, 1] = second[on_outer] - t[on_outer]
    out = trimesh.Trimesh(V2, old.faces, process=False)
    return out, t_range, on_outer.mean()
