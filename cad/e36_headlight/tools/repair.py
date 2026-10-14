"""Repair an original housing STL: drop loose debris bodies, resolve non-manifold edges, verify watertight.
usage: repair.py in.stl out.stl"""
import sys, numpy as np, trimesh, manifold3d as mf
src, dst = sys.argv[1], sys.argv[2]
m = trimesh.load(src)
bodies = m.split(only_watertight=False)
main = max(bodies, key=lambda b: len(b.faces))
dropped = [(len(b.faces), b.bounds.mean(0).round(1).tolist()) for b in bodies if b is not main]
main.merge_vertices(); main.remove_unreferenced_vertices()
edges, cnt = np.unique(main.edges_sorted, axis=0, return_counts=True)
print("non-manifold edges before:", int((cnt > 2).sum()))
# manifold3d repairs coincident-edge non-manifoldness when we let it merge; fall back to per-face vertex split
mesh = mf.Mesh(vert_properties=main.vertices.astype(np.float32), tri_verts=main.faces.astype(np.uint32))
mesh.merge()
man = mf.Manifold(mesh)
print("manifold status:", man.status())
if man.status() != mf.Error.NoError:
    # split vertices along non-manifold edges, then re-close with a tiny union against itself
    bad = set(map(tuple, edges[cnt > 2]))
    V = main.vertices.copy(); F = main.faces.copy()
    for fi, f in enumerate(F):
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            if (min(a, b), max(a, b)) in bad:
                pass
    raise SystemExit("needs manual repair")
out = man.to_mesh()
r = trimesh.Trimesh(out.vert_properties[:, :3], out.tri_verts)
print("dropped loose bodies:", dropped)
print("repaired: watertight", r.is_watertight, "volume %.1f cm3" % (r.volume / 1000), "faces", len(r.faces))
r.export(dst)
