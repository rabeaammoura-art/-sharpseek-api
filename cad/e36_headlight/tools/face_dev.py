"""Deviation of the modified front face from the restored surface F (finds steps/seams)."""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parents[1]))
import numpy as np, trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import geom as G
m = trimesh.load(sys.argv[1]); out = sys.argv[2]
xs = np.arange(-175, 166, 1.0) + 0.37; zs = np.arange(122, 255, 1.0) + 0.29  # off-grid rays
X, Z = np.meshgrid(xs, zs)
o = np.stack([X.ravel(), np.full(X.size, -400.0), Z.ravel()], 1)
loc, idx, _ = m.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=False)
y = np.full(X.size, np.nan); y[idx] = loc[:, 1]; d = (y - G.F(X.ravel(), Z.ravel())).reshape(X.shape)
fig, ax = plt.subplots(figsize=(16, 7)); im = ax.pcolormesh(X, Z, np.clip(d, -1.5, 1.5), cmap="RdBu", shading="auto")
plt.colorbar(im, label="face Y - F (mm), clipped ±1.5"); ax.set_aspect("equal"); ax.set_title("front face deviation from restored surface")
fig.savefig(out, dpi=75, bbox_inches="tight")
inner = (np.abs(X) < 1e9) & (Z > 135) & (Z < 241) & (X > -163) & (X < 150)
dd = d[inner & ~np.isnan(d) & (np.abs(d) < 5)]
print("in-bezel face deviation: p1 %.2f p50 %.2f p99 %.2f mm" % tuple(np.percentile(dd, [1, 50, 99])))
