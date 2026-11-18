"""Assembly checks for printed lock/lid designs (lessons from the lit dome, 2026-11-18).

Use before sending a multi-part print:
  ledge_under(walls, angles_deg, r, z)  -> fraction of sample points under each lug that are solid (1.0 = fully supported)
  overlap(a, b)                          -> interference volume mm3 (0 = parts do not collide)
  thin_spots(mesh, face_angle, ...)      -> grid points where the wall is thinner than `t_min` (light slits)
A plain total-overlap number hides a single unsupported lug: always check each lug on its own."""
import numpy as np
import trimesh


def overlap(a, b):
    return float(trimesh.boolean.intersection([a, b], engine="manifold").volume)


def ledge_under(walls, angles_deg, r=59.3, z=1.2, half_width_deg=6.0, step=1.0):
    out = {}
    for a in angles_deg:
        ts = np.radians(np.arange(a - half_width_deg, a + half_width_deg + 1e-6, step))
        pts = np.c_[r * np.cos(ts), r * np.sin(ts), np.full(len(ts), z)]
        out[a] = float(np.mean(walls.contains(pts)))
    return out


def thin_spots(mesh, face_angle_deg, x_range, z_range, apothem, t_min=0.5, step=0.25):
    """Rays through one wall face (outward normal at face_angle_deg); returns (x, z) points thinner than t_min."""
    m = mesh.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(-face_angle_deg - 90), [0, 0, 1]))
    xs = np.arange(*x_range, step); zs = np.arange(*z_range, step); X, Z = np.meshgrid(xs, zs)
    o = np.c_[X.ravel(), np.full(X.size, -apothem - 30.0), Z.ravel()]
    loc, idx, _ = m.ray.intersects_location(o, np.tile([0, 1.0, 0], (X.size, 1)), multiple_hits=True)
    t = np.zeros(X.size); hits = {}
    for j in np.lexsort((loc[:, 1], idx)):
        if loc[j, 1] < -apothem + 10: hits.setdefault(idx[j], []).append(loc[j, 1])
    for k, ys in hits.items():
        ys = sorted(ys); t[k] = sum(ys[i + 1] - ys[i] for i in range(0, len(ys) - 1, 2))
    bad = t.reshape(X.shape) < t_min
    return [(round(float(X[i]), 1), round(float(Z[i]), 1)) for i in zip(*np.nonzero(bad))]
