"""Render a PNG preview of an STL (headless). Usage: python preview.py out/part.stl"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh

path = Path(sys.argv[1])
m = mesh.Mesh.from_file(str(path))
fig = plt.figure(figsize=(10, 5))
for i, (elev, azim) in enumerate([(25, -60), (25, 120)]):
    ax = fig.add_subplot(1, 2, i + 1, projection="3d")
    # Flat shading: brightness from each face normal against a fixed light direction.
    n = m.normals / (np.linalg.norm(m.normals, axis=1, keepdims=True) + 1e-12)
    shade = 0.35 + 0.65 * np.clip(n @ np.array([0.4, -0.5, 0.75]), 0, 1)
    colors = np.outer(shade, [0.29, 0.56, 0.85])
    ax.add_collection3d(Poly3DCollection(m.vectors, facecolors=colors, edgecolor="none"))
    pts = m.points.reshape(-1, 3)
    lo, hi = pts.min(0), pts.max(0)
    span = (hi - lo).max()
    mid = (hi + lo) / 2
    for setlim, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), mid):
        setlim(c - span / 2, c + span / 2)
    ax.view_init(elev, azim)
    ax.set_xlabel("X mm"); ax.set_ylabel("Y mm"); ax.set_zlabel("Z mm")
fig.suptitle(path.stem)
out = path.with_suffix(".png")
fig.savefig(out, dpi=110, bbox_inches="tight")
print(out)
