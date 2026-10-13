"""Mechanism diagrams for the Mercedes tray, cut from the real B-rep.

out/mercedes_diagram.png : top view + section through one compartment, collapsed and
                            extended, with a zoom on the stop lips.
out/mercedes_3d.png      : shaded 3D views (collapsed / open on the base, handle up).
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

from _mercedes import P, assembly, frame, frame_lift, handle, tray_bodies  # noqa: E402

OUT = ROOT / "out"
FRAME_C, RING_C, FLOOR_C, HANDLE_C, BASE_C = "#5b6b7a", "#4a90d9", "#e08a3c", "#7a4ad9", "#7a5c43"


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
        color = (FRAME_C if name == "frame" else BASE_C if name == "base"
                 else FLOOR_C if name.endswith(f"r{P.n_rings:02d}") else RING_C)
        for poly in section_polys(s):
            ax.add_patch(Polygon(poly, closed=True, fc=color, ec="black", lw=0.3))
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)


def side_view(ax):
    """Projection along the hinge axis (X) of base, frame and handle at three angles."""
    from matplotlib.collections import PolyCollection
    for i, (ang, alpha) in enumerate(((0.0, 0.25), (50.0, 0.4), (P.stop_deg, 0.9))):
        lift = frame_lift(P, ang)
        for shape, col in ((handle(P, ang).moved(Location((0, 0, lift))), HANDLE_C),
                           (frame(P).moved(Location((0, 0, lift))), FRAME_C)):
            v, t = shape.tessellate(0.5, 0.5)
            yz = np.array([[q.Y, q.Z] for q in v])
            tris = [yz[list(tri)] for tri in t if np.array([v[k].X for k in tri]).min() > 100]
            ax.add_collection(PolyCollection(tris, facecolor=col, edgecolor="none", alpha=alpha))
        ax.annotate(f"{ang:.0f}°", (P.handle_r1 * 0.55 if ang < 60 else -40, lift + 75 if ang > 60 else lift + 30),
                    fontsize=9, color=HANDLE_C)
    ax.add_patch(Polygon([(-150, -P.base_t), (150, -P.base_t), (150, 0), (-150, 0)], fc=BASE_C, alpha=0.8))
    ax.set_xlim(-150, 150); ax.set_ylim(-10, 160); ax.set_aspect("equal"); ax.grid(alpha=0.3)
    ax.set_title("Side view along the hinge axis (x > 100 only): handle at 0°, 50°, 100°.\n"
                 "The legs swing down onto the base and lift the frame (grey).", fontsize=9)
    ax.set_xlabel("y (mm)"); ax.set_ylabel("z (mm)")


def main():
    b0 = tray_bodies(P, 0.0)
    b1 = {k: v for k, v in assembly(P, P.stop_deg).items() if k != 'handle'}
    fig = plt.figure(figsize=(16, 13))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.25, 0.6, 1.0])

    # top view
    ax = fig.add_subplot(gs[0, 0])
    for name, s in b0.items():
        color = FRAME_C if name == "frame" else (FLOOR_C if name.endswith(f"r{P.n_rings:02d}") else RING_C)
        for poly in section_polys(s, Plane.XY.offset(P.lip_flat / 2)):
            ax.add_patch(Polygon(poly, closed=True, fc=color, ec="black", lw=0.15))
    for poly in section_polys(handle(P, 0), Plane.XY.offset(P.lip_flat / 2)):
        ax.add_patch(Polygon(poly, closed=True, fc=HANDLE_C, ec="black", lw=0.3, alpha=0.55))
    ax.plot([0, 0], [-140, 0], "k--", lw=0.8)
    ax.annotate("section A-A", (0, -135), (8, -150), fontsize=8)
    ax.set_xlim(-150, 150); ax.set_ylim(-155, 150); ax.set_aspect("equal")
    ax.set_title(f"Top view (cut at z={P.lip_flat / 2:.1f} mm): Ø{2 * P.handle_r1:.0f} overall, 3 x 120° compartments,\n"
                 f"{P.n_rings} nested rings each (orange = floor), handle ring + legs printed in place (purple)", fontsize=10)

    # text box with key numbers + side view of the lever action
    sub = gs[0, 1].subgridspec(2, 1, height_ratios=[1.35, 1.0], hspace=0.35)
    side_view(fig.add_subplot(sub[1]))
    ax = fig.add_subplot(sub[0]); ax.axis("off")
    txt = (f"Key dimensions (mm)\n"
           f"  Ø {2 * P.handle_r1:.0f} overall (flange Ø {P.tray_d:.0f}, {P.flange_w:.0f} wide), dividers {2 * P.divider_half:.0f}\n"
           f"  rings per compartment N = {P.n_rings} (+ fixed frame)\n"
           f"  wall {P.wall}, gap {P.clear}, lip {P.lip} @45°, land {P.lip_flat}\n"
           f"  plan pitch {P.pitch:.1f}  -> wall slope {np.degrees(np.arctan(P.travel / P.pitch)):.0f}° from horizontal\n"
           f"  ring height {P.ring_h}, frame height {P.frame_h}\n"
           f"  travel per step {P.travel:.1f}  ->  depth {P.n_rings * P.travel:.1f}\n"
           f"  floor: inscribed circle Ø {2 * P.floor_inradius:.1f}, {P.floor_t} thick\n"
           f"  collapsed height {P.frame_h:.0f} (+ base {P.base_t:.0f})\n"
           f"  open: frame top {frame_lift(P, P.stop_deg) + P.frame_h:.1f} above the base\n"
           f"  handle: ring {P.handle_w:.0f} wide, legs {P.leg_deg:.1f}° past the hinges\n\n"
           f"How it works\n"
           f"  Flip the handle up: its legs push down on the base and\n"
           f"  lift the frame; each ring hangs from the next larger one\n"
           f"  (45° lips, self-centring) until the floors touch the base.\n"
           f"  Past {P.stop_deg - 6:.0f}° the weight drives the feet into the pocket\n"
           f"  stop ({P.stop_deg:.0f}°): it stays open. Flip it back -> flat.")
    ax.text(0, 1.02, txt, va="top", family="monospace", fontsize=8.6)

    # sections
    ax = fig.add_subplot(gs[1, :])
    draw_section(ax, b0, "Section A-A (x = 0) — COLLAPSED, as printed (left: compartment 270°, right: divider rib)")
    ax.set_xlim(-145, 145); ax.set_ylim(-3, 22)
    ax = fig.add_subplot(gs[2, 0])
    draw_section(ax, b1, f"Section A-A — OPEN on the base (handle at {P.stop_deg:.0f}°): frame up {frame_lift(P, P.stop_deg):.1f} mm")
    ax.set_xlim(-150, 5); ax.set_ylim(-8, 72)

    # lip zoom
    ax = fig.add_subplot(gs[2, 1])
    b1 = tray_bodies(P, 1.0)
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
    for i, (ang, title) in enumerate(((0.0, "Collapsed (print state, on its base)"),
                                      (P.stop_deg, "Open: handle up, locked on the base"))):
        asm = assembly(P, ang)
        h = asm.pop("handle")
        bodies = asm
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
