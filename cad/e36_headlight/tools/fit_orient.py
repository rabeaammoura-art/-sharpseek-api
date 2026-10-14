"""Search rotations of a mesh for one whose axis-aligned bbox fits a build volume (with margin)."""
import sys, numpy as np, trimesh
from scipy.spatial.transform import Rotation as Rr
from scipy.optimize import minimize
m = trimesh.load(sys.argv[1]); V = m.convex_hull.vertices
vol = np.array([float(v) for v in sys.argv[2].split("x")]) - 4.0      # 2 mm margin each side
def excess(q):
    R = Rr.from_rotvec(q).as_matrix(); P = V @ R.T; e = P.max(0) - P.min(0)
    return np.maximum(e - vol, 0).sum() + 1e-3 * e[2]           # prefer low height once it fits
best = None; rng = np.random.default_rng(1)
for i in range(400):
    r = minimize(excess, Rr.random(random_state=rng).as_rotvec(), method="Nelder-Mead", options=dict(xatol=1e-4, fatol=1e-6, maxiter=4000))
    R = Rr.from_rotvec(r.x).as_matrix(); P = V @ R.T; e = P.max(0) - P.min(0)
    over = np.maximum(e - vol, 0).sum()
    if best is None or (over, e[2]) < (best[0], best[2][2]): best = (over, r.x, e)
over, q, e = best
print("best overshoot %.2f mm, extents %s, build %s" % (over, e.round(1), (vol + 4)))
print("euler xyz deg", Rr.from_rotvec(q).as_euler("xyz", degrees=True).round(2).tolist())
np.save(sys.argv[3], Rr.from_rotvec(q).as_matrix())
