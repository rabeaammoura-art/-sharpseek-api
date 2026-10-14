"""Wall thickness survey: from sampled surface points cast a ray inward (-normal), distance to the exit hit."""
import sys, json, numpy as np, trimesh
m = trimesh.load(sys.argv[1])
pts, fi = trimesh.sample.sample_surface_even(m, 60000, seed=1)
n = m.face_normals[fi]; o = pts - n * 0.01
loc, ri, _ = m.ray.intersects_location(o, -n, multiple_hits=False)
t = np.full(len(pts), np.nan); t[ri] = np.linalg.norm(loc - o[ri], axis=1)
ok = ~np.isnan(t)
pc = np.percentile(t[ok], [1, 5, 25, 50, 75, 95]).round(2)
thin = ok & (t < 2.0)
cl = pts[thin]
print(json.dumps(dict(samples=int(ok.sum()), percentiles_1_5_25_50_75_95=pc.tolist(),
                      share_below_2mm=round(float(thin.sum() / ok.sum()), 4), share_below_1_2mm=round(float((ok & (t < 1.2)).sum() / ok.sum()), 4),
                      thin_regions_bbox=[cl.min(0).round(0).tolist(), cl.max(0).round(0).tolist()] if len(cl) else None)))
np.save(sys.argv[2], np.c_[pts[thin], t[thin]])
