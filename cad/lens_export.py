"""Export the W115 lens: STEP + STL per colour body for RH and LH, a 3MF per side, and renders.

Usage: python lens_export.py      (writes to out/w115_lens/)
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from build123d import Compound, Location, Mesher, export_step, export_stl
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from stl import mesh

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parts"))
import w115_lens as lens  # noqa: E402

OUT = ROOT / "out" / "w115_lens"
COLORS = {"red": (0.84, 0.12, 0.10), "clear": (0.86, 0.90, 0.93), "amber": (0.96, 0.58, 0.10)}
VIEWS = [  # (title, elev, azim) — chosen to match the reference photos
    ("front (from behind car)", 0, -90),
    ("front angled", 28, -125),
    ("inside", 0, 90),
    ("inside angled", 40, 55),
    ("top (plan)", 90, -90),
    ("inboard end (side)", 0, 180),
]


def _cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def bed_tilt(pts):
    """Angle (deg, about +Y) that puts the widest lower-hull edge of the (x, z) points flat."""
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    hull = []
    for q in pts:                                    # lower convex hull, monotone chain
        while len(hull) >= 2 and _cross2(hull[-1] - hull[-2], q - hull[-2]) <= 0:
            hull.pop()
        hull.append(q)
    a, b = max(zip(hull, hull[1:]), key=lambda e: e[1][0] - e[0][0])
    return np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))


def export_all():
    OUT.mkdir(parents=True, exist_ok=True)
    bodies, d = lens.make_bodies()
    sides = {"RH": bodies, "LH": {k: lens.mirror_lh(v) for k, v in bodies.items()}}
    for side, parts in sides.items():
        for name, part in parts.items():
            export_stl(part, str(OUT / f"{side}_{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
        export_step(Compound(children=list(parts.values())), str(OUT / f"{side}_lens.step"))
        # Print orientation: back (seal flange) toward the bed, outer face up -> no supports on the face.
        # Rotate -90 deg about X (car +Y -> print -Z), then drop onto Z=0 and centre on the H2D bed.
        rot = {k: v.moved(Location((0, 0, 0), (-90, 0, 0))) for k, v in parts.items()}
        # The amber wrap reaches below the flat flange; tilt about the print Y axis so the
        # lower hull edge (inboard back edge -> amber tip) lies on the bed: shorter supports.
        pts = np.array([[v.X, v.Z] for p in rot.values() for v in p.vertices()])
        tilt = bed_tilt(pts)
        rot = {k: v.moved(Location((0, 0, 0), (0, tilt, 0))) for k, v in rot.items()}
        bb = Compound(children=list(rot.values())).bounding_box()
        shift = Location((175 - bb.center().X, 160 - bb.center().Y, -bb.min.Z))
        mesher = Mesher()
        for name, part in rot.items():
            pp = part.moved(shift)
            pp.label = f"{side}_{name}"
            export_stl(pp, str(OUT / f"{side}_{name}_print.stl"), tolerance=0.02, angular_tolerance=0.1)
            mesher.add_shape(pp, linear_deflection=0.02, angular_deflection=0.1)
        mesher.write(str(OUT / f"{side}_lens_multicolour_print.3mf"))
        tot = sum(p.volume for p in parts.values())
        bb = Compound(children=list(parts.values())).bounding_box()
        print(f"{side}: {tot / 1000:.1f} cm3, {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, print tilt {tilt:.1f} deg")
    return d


def render(side="RH", views=VIEWS, fname=None, ncols=3):
    tris, cols = [], []
    light = np.array([0.3, -0.6, 0.75]); light /= np.linalg.norm(light)
    for name, c in COLORS.items():
        m = mesh.Mesh.from_file(str(OUT / f"{side}_{name}.stl"))
        n = m.normals / (np.linalg.norm(m.normals, axis=1, keepdims=True) + 1e-12)
        shade = 0.35 + 0.65 * np.abs(n @ light)
        tris.append(m.vectors); cols.append(np.outer(shade, c))
    tris, cols = np.concatenate(tris), np.concatenate(cols)
    pts = tris.reshape(-1, 3); lo, hi = pts.min(0), pts.max(0); mid = (lo + hi) / 2; span = (hi - lo).max()
    nrows = -(-len(views) // ncols)
    fig = plt.figure(figsize=(6 * ncols, 4.2 * nrows))
    for i, (title, elev, azim) in enumerate(views):
        ax = fig.add_subplot(nrows, ncols, i + 1, projection="3d")
        ax.set_proj_type("ortho")
        ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolor="none"))
        for setlim, c in zip((ax.set_xlim, ax.set_ylim, ax.set_zlim), mid):
            setlim(c - span / 2, c + span / 2)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(title)
    plt.tight_layout()
    out = OUT / (fname or f"{side}_renders.png")
    fig.savefig(out, dpi=90); plt.close(fig)
    return out


if __name__ == "__main__":
    export_all()
    for s in ("RH", "LH"):
        print(render(s))
