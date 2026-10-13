"""Mechanism diagrams for the Mercedes tray, cut from the real B-rep.

out/mercedes_diagram.png : top view + section through one compartment, collapsed and
                            extended, with a zoom on the stop lips.
out/mercedes_3d.png      : shaded 3D views (collapsed / extended with handle up).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parts"))
from build123d import Face, Location, Plane, Rectangle  # noqa: E402

from _mercedes import P, handle, tray_bodies  # noqa: E402

OUT = ROOT / "out"
FRAME_C, RING_C, FLOOR_C, HANDLE_C = "#5b6b7a", "#4a90d9", "#e08a3c", "#7a4ad9"


def section_polys(shape, plane=Plane.YZ):
    """Polygons (in plane coordinates) of shape cut by a plane through the origin."""
    cut = shape & Face(Rectangle(800, 800).wrapped).moved(Location(plane.location))
    polys = []
    for f in cut.faces():
        pts = [plane.to_local_coords(v) for v in f.outer_wire().positions(np.linspace(0, 1, 400))]
        polys.append([(q.X, q.Y) for q in pts])
    return polys


def draw_section(ax, bodies, title):
    for name, s in bodies.items():
        color = FRAME_C if name == "frame" else (FLOOR_C if name.endswith(f"r{P.n_rings:02d}") else RING_C)
        for poly in section_polys(s):
            ax.add_patch(Polygon(poly, closed=True, fc=color, ec="black", lw=0.3))
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)


def main():
    b0, b1 = tray_bodies(P, 0.0), tray_bodies(P, 1.0)
    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 0.6, 1.0])

    # top view
    ax = fig.add_subplot(gs[0, 0])
    for name, s in b0.items():
        color = FRAME_C if name == "frame" else (FLOOR_C if name.endswith(f"r{P.n_rings:02d}") else RING_C)
        for poly in section_polys(s, Plane.XY.offset(P.lip_flat / 2)):
            ax.add_patch(Polygon(poly, closed=True, fc=color, ec="black", lw=0.15))
    for poly in section_polys(handle(P, 0), Plane.XY.offset(P.hinge_z)):
        ax.add_patch(Polygon(poly, closed=True, fc=HANDLE_C, ec="black", lw=0.3, alpha=0.55))
    ax.plot([0, 0], [-140, 0], "k--", lw=0.8)
    ax.annotate("section A-A", (0, -135), (8, -150), fontsize=8)
    ax.set_xlim(-150, 150); ax.set_ylim(-155, 150); ax.set_aspect("equal")
    ax.set_title(f"Top view (cut at z={P.lip_flat / 2:.1f} mm): Ø{P.tray_d:.0f} flange, 3 x 120° compartments,\n"
                 f"{P.n_rings} nested rings each (orange = floor), handle folded over +Y half (purple)", fontsize=10)

    # text box with key numbers
    ax = fig.add_subplot(gs[0, 1]); ax.axis("off")
    txt = (f"Key dimensions (mm)\n"
           f"  tray Ø {P.tray_d:.0f}, flange {P.flange_w:.0f} wide, divider ribs {2 * P.divider_half:.0f}\n"
           f"  rings per compartment N = {P.n_rings} (+ fixed frame)\n"
           f"  wall {P.wall}, gap {P.clear}, lip {P.lip} @45°, land {P.lip_flat}\n"
           f"  plan pitch {P.pitch:.1f}  -> wall slope {np.degrees(np.arctan(P.travel / P.pitch)):.0f}° from horizontal\n"
           f"  ring height {P.ring_h}, frame height {P.frame_h}\n"
           f"  travel per step {P.travel:.1f}  ->  depth {P.n_rings * P.travel:.1f}\n"
           f"  floor: inscribed circle Ø {2 * P.floor_inradius:.1f}, {P.floor_t} thick\n"
           f"  collapsed height {P.post_top:.1f} (hinge posts), rings {P.ring_h}\n"
           f"  extended height {P.frame_h + P.n_rings * P.travel:.1f}\n\n"
           f"How it works\n"
           f"  Lift the handle -> frame rises, each ring hangs\n"
           f"  from the next larger one by its top lip resting on\n"
           f"  the larger ring's bottom lip (45° faces, self-centring).\n"
           f"  Set it down -> gravity nests everything flat again.")
    ax.text(0, 1, txt, va="top", family="monospace", fontsize=10)

    # sections
    ax = fig.add_subplot(gs[1, :])
    draw_section(ax, b0, "Section A-A (x = 0) — COLLAPSED, as printed (left: compartment 270°, right: divider rib)")
    ax.set_xlim(-145, 145); ax.set_ylim(-3, 22)
    ax = fig.add_subplot(gs[2, 0])
    draw_section(ax, b1, f"Section A-A — EXTENDED (handle lifted): frame up {P.n_rings * P.travel:.1f} mm")
    ax.set_xlim(-125, 5); ax.set_ylim(-3, 72)

    # lip zoom
    ax = fig.add_subplot(gs[2, 1])
    for state, bodies, dx in (("collapsed", b0, 0), ("extended", b1, 14)):
        for name in ("c270_r03", "c270_r04"):
            for poly in section_polys(bodies[name]):
                poly = [(y + dx, z - (bodies is b1) * (P.n_rings - 4) * P.travel) for y, z in poly]
                ax.add_patch(Polygon(poly, closed=True, fc=RING_C if name.endswith("3") else "#9cc3ec",
                                     ec="black", lw=0.6))
    ring3 = -(120 - P.ring_inset(3))
    ax.set_xlim(ring3 - 1, ring3 + 22); ax.set_ylim(-1, 12.5); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    ax.set_title("Lip detail, rings 3 (dark) & 4 (light): collapsed (left) / extended (right)\n"
                 f"gap {P.clear} everywhere when collapsed; 45° lips meet face-to-face when extended,\n"
                 f"radial engagement {P.lip - P.clear:.1f} mm", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "mercedes_diagram.png", dpi=110)
    print(OUT / "mercedes_diagram.png")

    # 3D views
    import trimesh
    from build123d import Compound, export_stl
    fig = plt.figure(figsize=(16, 7))
    for i, (ext, ang, title) in enumerate(((0.0, 0, "Collapsed, handle down (print state)"),
                                           (1.0, 90, "Extended, handle lifted"))):
        bodies = tray_bodies(P, ext)
        h = handle(P, ang).moved(Location((0, 0, P.n_rings * P.travel * ext)))
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        for shape, base in ((Compound(list(bodies.values())), (0.29, 0.56, 0.85)), (h, (0.48, 0.29, 0.85))):
            export_stl(shape, "/tmp/_r.stl", tolerance=0.2, angular_tolerance=0.3)
            m = trimesh.load("/tmp/_r.stl")
            n = m.face_normals
            shade = 0.35 + 0.65 * np.clip(n @ np.array([0.3, -0.5, 0.8]), 0, 1)
            ax.add_collection3d(Poly3DCollection(m.triangles, facecolors=np.outer(shade, base), edgecolor="none"))
        ax.set_xlim(-140, 140); ax.set_ylim(-140, 140); ax.set_zlim(-60, 220)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(28, -60); ax.set_title(title)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT / "mercedes_3d.png", dpi=100)
    print(OUT / "mercedes_3d.png")


if __name__ == "__main__":
    main()
