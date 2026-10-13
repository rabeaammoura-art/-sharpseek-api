"""Animate the Mercedes tray opening and closing (rendered from the real model).

Lift sequence is physical: the frame rises with the handle; ring k leaves the table once the
frame has risen k * travel (each larger ring's bottom lip catches the next ring's top lip).
Writes out/mercedes_animation.mp4 and out/mercedes_animation.gif. Needs a display:
    xvfb-run -a python animate_mercedes.py
"""
import sys
import tempfile
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
import pyvista as pv

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parts"))
from build123d import export_stl  # noqa: E402

from _mercedes import P, handle, tray_bodies  # noqa: E402

OUT = ROOT / "out"
FPS = 20
N, TRAVEL = P.n_rings, P.travel
LIFT = N * TRAVEL


def smooth(t):
    return t * t * (3 - 2 * t)


def timeline():
    """(handle angle deg, frame lift mm, caption) per frame."""
    seq = [(0.6, lambda t: (0, 0), "Collapsed: 19 mm flat"),
           (1.4, lambda t: (90 * smooth(t), 0), "Lift the handle"),
           (3.4, lambda t: (90, LIFT * smooth(t)), "Rings drop open one by one"),
           (1.2, lambda t: (90, LIFT), f"Open: 3 compartments, {LIFT:.0f} mm deep"),
           (3.0, lambda t: (90, LIFT * (1 - smooth(t))), "Set it down: rings nest again"),
           (1.4, lambda t: (90 * (1 - smooth(t)), 0), "Fold the handle"),
           (0.6, lambda t: (0, 0), "Collapsed: 19 mm flat")]
    frames = []
    for dur, f, cap in seq:
        n = int(dur * FPS)
        frames += [(*f(i / max(n - 1, 1)), cap) for i in range(n)]
    return frames


def load_meshes():
    meshes = {}
    with tempfile.TemporaryDirectory() as tmp:
        shapes = dict(tray_bodies(P, 0.0))
        shapes["handle"] = handle(P, 0)
        for name, s in shapes.items():
            f = f"{tmp}/{name}.stl"
            export_stl(s, f, tolerance=0.03, angular_tolerance=0.15)
            meshes[name] = pv.read(f)
    return meshes


def color(name):
    if name == "frame":
        return "#8a96a3"
    if name == "handle":
        return "#7a4ad9"
    k = int(name.split("_r")[1])
    if k == N:
        return "#e08a3c"
    c0, c1 = np.array([0x3a, 0x78, 0xc9]), np.array([0x9c, 0xc8, 0xf0])
    return tuple((c0 + (c1 - c0) * (k - 1) / (N - 1)) / 255)


def main():
    meshes = load_meshes()
    pl = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1600, 720), border=False)
    actors = [{}, {}]
    for col, cut in ((0, False), (1, True)):
        pl.subplot(0, col)
        pl.set_background("#f4f5f7")
        for name, m in meshes.items():
            if cut and name == "handle":
                continue  # keep the section view clear
            mesh = m.clip_closed_surface(normal=(-1, 0, 0), origin=(0, 0, 0)) if cut else m
            if mesh.n_points == 0:
                continue
            actors[col][name] = pl.add_mesh(mesh, color=color(name), smooth_shading=False,
                                            specular=0.25, ambient=0.18)
        pl.add_mesh(pv.Plane(center=(0, 0, -0.3), i_size=420, j_size=420), color="#d9dde2", ambient=0.4)
        if cut:
            pl.camera_position = [(330, -95, 75), (0, -62, 30), (0, 0, 1)]
            pl.add_text("Section through one compartment", font_size=12, color="#333333")
        else:
            pl.camera_position = [(330, -430, 330), (0, 0, 40), (0, 0, 1)]
        for a in actors[col].values():
            if a is actors[col].get("handle"):
                a.SetOrigin(0, 0, P.hinge_z)
    caption = None
    frames = []
    for angle, lift, cap in timeline():
        for col in (0, 1):
            for name, a in actors[col].items():
                if name == "frame":
                    a.position = (0, 0, lift)
                elif name == "handle":
                    a.SetOrientation(angle, 0, 0)
                    a.position = (0, 0, lift)
                else:
                    k = int(name.split("_r")[1])
                    a.position = (0, 0, max(0.0, lift - k * TRAVEL))
        pl.subplot(0, 0)
        if caption is not None:
            pl.remove_actor(caption)
        caption = pl.add_text(cap, position="upper_left", font_size=14, color="#222222")
        frames.append(pl.screenshot(return_img=True))
    pl.close()

    imageio.mimwrite(OUT / "mercedes_animation.mp4", frames, fps=FPS, quality=8, macro_block_size=8)
    small = [f[::2, ::2] for f in frames[::2]]
    imageio.mimwrite(OUT / "mercedes_animation.gif", small, duration=1000 * 2 / FPS, loop=0)
    imageio.imwrite(OUT / "mercedes_open.png", frames[len(frames) // 2])
    print(f"{len(frames)} frames ->", OUT / "mercedes_animation.mp4", OUT / "mercedes_animation.gif")


if __name__ == "__main__":
    main()
