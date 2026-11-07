"""Quick painter's-algorithm renders of the wedding plaque assembled in its box (front and back views).
Usage: python cad/wedding/render3d.py <build3d_out_dir> <png_prefix>
"""
import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import kickstand as ks  # noqa: E402


def rot(ax, deg):
    return trimesh.transformations.rotation_matrix(math.radians(deg), ax)


def draw(items, path, yaw, pitch, size=1400, bg=(58, 51, 48)):
    """z-buffer rasteriser. items: [(mesh, (r, g, b))] in world coords (y up, +z toward the viewer at yaw 0)."""
    M = rot((1, 0, 0), pitch) @ rot((0, 1, 0), yaw)
    allv = np.vstack([m.vertices for m, _ in items])
    c = (allv.min(0) + allv.max(0)) / 2
    V = [(np.c_[m.vertices - c, np.ones(len(m.vertices))] @ M.T)[:, :3] for m, _ in items]
    span = max(np.ptp(np.vstack(V)[:, 0]), np.ptp(np.vstack(V)[:, 1]))
    sc = size * 0.93 / span
    light = np.array([-0.35, 0.55, 0.75]); light /= np.linalg.norm(light)
    img = np.zeros((size, size, 3), float); img[:] = bg
    zb = np.full((size, size), -1e9)
    for (m, col), v in zip(items, V):
        P = np.c_[size / 2 + v[:, 0] * sc, size / 2 - v[:, 1] * sc, v[:, 2]]
        t = v[m.faces]
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]); nn = np.linalg.norm(n, axis=1, keepdims=True); nn[nn == 0] = 1; n = n / nn
        shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
        for f, sh in zip(m.faces, shade):
            a, b, c3 = P[f[0]], P[f[1]], P[f[2]]
            x0, x1 = int(max(0, min(a[0], b[0], c3[0]))), int(min(size - 1, max(a[0], b[0], c3[0])) + 1)
            y0, y1 = int(max(0, min(a[1], b[1], c3[1]))), int(min(size - 1, max(a[1], b[1], c3[1])) + 1)
            if x1 <= x0 or y1 <= y0:
                continue
            den = (b[1] - c3[1]) * (a[0] - c3[0]) + (c3[0] - b[0]) * (a[1] - c3[1])
            if abs(den) < 1e-9:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            w1 = ((b[1] - c3[1]) * (xs - c3[0]) + (c3[0] - b[0]) * (ys - c3[1])) / den
            w2 = ((c3[1] - a[1]) * (xs - c3[0]) + (a[0] - c3[0]) * (ys - c3[1])) / den
            w3 = 1 - w1 - w2
            inside = (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6)
            if not inside.any():
                continue
            z = w1 * a[2] + w2 * b[2] + w3 * c3[2]
            sub = zb[y0:y1, x0:x1]
            upd = inside & (z > sub)
            sub[upd] = z[upd]
            img[y0:y1, x0:x1][upd] = np.array(col) * sh
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)


def main():
    out = Path(sys.argv[1])
    pre = sys.argv[2]
    ld = lambda n: trimesh.load(out / n)
    box, base, cream, gold, navy = (ld(f"wedding_{n}.stl") for n in ("box", "base", "cream", "gold", "navy"))
    mod, leg, pin = (ld(f"wedding_kick_{n}.stl") for n in ("module", "leg", "pin"))
    size = 280
    fp = np.load(out / "fix_points.npy")
    # kickstand layout of THIS box (same override as build3d)
    y_bot = box.bounds[0][1]
    H = box.bounds[1][1] - box.bounds[0][1]
    # hinge height: read back from the module position -> recompute like build3d: largest fraction that fit; stored by build3d? use env
    frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.79
    ks.OVERRIDE = {"y_axis": y_bot + frac * H, "y_bot": y_bot}
    plaque = []
    for m, col in ((base, (245, 245, 240)), (cream, (255, 233, 176)), (gold, (217, 162, 27)), (navy, (22, 29, 60))):
        mm = m.copy(); mm.apply_translation((0, 0, 11.6)); plaque.append((mm, col))
    tilt = rot((1, 0, 0), -12.0)
    for view, yaw, pitch in (("front", -22, 8), ("back", 158, 14)):
        items = [(box, (225, 225, 225))] + plaque
        items += [(ks.module_in_box(mod, size), (70, 130, 220)), (ks.leg_in_box(leg, size, 23.5), (70, 130, 220)), (ks.pin_in_box(pin, size), (230, 120, 40))]
        tilted = []
        for m, col in items:
            mm = m.copy(); mm.apply_translation((0, -y_bot, 0)); mm.apply_transform(tilt); tilted.append((mm, col))
        draw(tilted, f"{pre}_{view}.png", yaw, pitch)
        print("wrote", f"{pre}_{view}.png")


if __name__ == "__main__":
    main()
