"""Technical views + shaded render of the wrench key holder from the exported STLs (software renderer).
Usage: python cad/wrench_render.py <out_dir> [disc|drum]"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.collections import PolyCollection

COL = {"black": (0.12, 0.12, 0.14), "orange": (1.0, 0.48, 0.0), "white": (0.90, 0.90, 0.92), "red": (0.82, 0.09, 0.09)}


def load(out, variant):
    items = []
    for f in sorted((out / "stl").glob("*.stl")):
        name, col = f.stem.split("__")
        if name.startswith("brake_") and name != f"brake_{variant}":
            continue
        m = trimesh.load(f)
        items.append((m, COL[col]))
    return items


def view(items, R, ax, light=(0.3, 0.5, 0.8)):
    polys, cols, depth = [], [], []
    L = np.array(light) / np.linalg.norm(light)
    for m, c in items:
        v = m.vertices @ R.T
        tri = v[m.faces]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        front = n[:, 2] > 0
        sh = 0.35 + 0.65 * np.clip(n @ L, 0, 1)
        for t, s, d in zip(tri[front], sh[front], t_depth(tri[front])):
            polys.append(t[:, :2]); cols.append(np.clip(np.array(c) * s, 0, 1)); depth.append(d)
    o = np.argsort(depth)
    ax.add_collection(PolyCollection([polys[i] for i in o], facecolors=[cols[i] for i in o], edgecolors="none", linewidths=0))
    allv = np.vstack([m.vertices @ R.T for m, _ in items])
    ax.set_xlim(allv[:, 0].min() - 5, allv[:, 0].max() + 5); ax.set_ylim(allv[:, 1].min() - 5, allv[:, 1].max() + 5)
    ax.set_aspect("equal"); ax.axis("off")


def t_depth(tri):
    return tri[:, :, 2].mean(axis=1)


def rot(rx, ry, rz=0):
    def r(a, ax):
        c, s = np.cos(np.radians(a)), np.sin(np.radians(a))
        return {"x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]), "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
                "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])}[ax]
    return r(rx, "x") @ r(ry, "y") @ r(rz, "z")


if __name__ == "__main__":
    out = Path(sys.argv[1]); variant = sys.argv[2] if len(sys.argv) > 2 else "disc"
    items = load(out, variant)
    views = {"front": rot(0, 0), "side": rot(0, 90), "top": rot(-90, 0), "iso": rot(-32, 0) @ rot(0, -28)}
    (out / "views").mkdir(exist_ok=True)
    for k, R in views.items():
        fig, ax = plt.subplots(figsize=(16 if k != "side" else 5, 5 if k != "side" else 5), dpi=130)
        fig.patch.set_facecolor("#c9c9cc"); ax.set_facecolor("#c9c9cc")
        view(items, R, ax); fig.savefig(out / "views" / f"{variant}_{k}.png", bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig); print(k)
