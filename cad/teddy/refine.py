"""Conformal local refinement (no T-junctions): split marked edges, then retriangulate every touched face."""
import numpy as np
import trimesh


def _split_once(V, F, face_mask):
    n = len(V)
    tri_edges = np.stack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 1)         # (nf,3,2)
    key = np.sort(tri_edges, axis=2)
    key = key[..., 0].astype(np.int64) * n + key[..., 1]
    marked = np.unique(key[face_mask].ravel())
    mid_index = n + np.arange(len(marked))
    a, b = marked // n, marked % n
    V2 = np.vstack([V, (V[a] + V[b]) / 2])
    pos = np.searchsorted(marked, key)
    pos = np.clip(pos, 0, len(marked) - 1)
    is_m = marked[pos] == key                                                   # (nf,3)
    mid = np.where(is_m, mid_index[pos], -1)
    cnt = is_m.sum(1)
    out = [F[cnt == 0]]
    p, q, r = F[:, 0], F[:, 1], F[:, 2]
    # cnt==1 : rotate so the marked edge is (p,q)
    for k, (P, Q, R) in enumerate([(p, q, r), (q, r, p), (r, p, q)]):
        s = (cnt == 1) & is_m[:, k]
        m = mid[s, k]
        out.append(np.c_[P[s], m, R[s]]); out.append(np.c_[m, Q[s], R[s]])
    # cnt==2 : marked edges (P,Q) and (Q,R) share vertex Q
    for k, (P, Q, R) in enumerate([(p, q, r), (q, r, p), (r, p, q)]):
        s = (cnt == 2) & is_m[:, k] & is_m[:, (k + 1) % 3]
        m1, m2 = mid[s, k], mid[s, (k + 1) % 3]
        out.append(np.c_[m1, Q[s], m2]); out.append(np.c_[P[s], m1, m2]); out.append(np.c_[P[s], m2, R[s]])
    s = cnt == 3
    m1, m2, m3 = mid[s, 0], mid[s, 1], mid[s, 2]
    out += [np.c_[p[s], m1, m3], np.c_[m1, q[s], m2], np.c_[m3, m2, r[s]], np.c_[m1, m2, m3]]
    return V2, np.vstack(out)


def refine_zone(mesh, in_zone, max_edge, iters=5):
    """in_zone(centroids)->bool mask; faces in the zone with an edge longer than max_edge are split."""
    V, F = mesh.vertices.copy(), mesh.faces.copy()
    for _ in range(iters):
        tri = V[F]
        el = np.max(np.linalg.norm(tri - np.roll(tri, 1, axis=1), axis=2), axis=1)
        mask = in_zone(tri.mean(1)) & (el > max_edge)
        if not mask.any():
            break
        V, F = _split_once(V, F, mask)
    return trimesh.Trimesh(V, F, process=True)
