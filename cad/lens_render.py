"""Z-buffer renders of the W115 lens colour bodies and a side-by-side sheet with reference photos.

Usage: python lens_render.py [ref_dir]   (after lens_export.py)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from stl import mesh

OUT = Path(__file__).parent / "out" / "w115_lens"
COLORS = {"red": (215, 30, 25), "clear": (225, 232, 238), "amber": (245, 150, 25)}


def load(side):
    tris, cols = [], []
    for name, c in COLORS.items():
        m = mesh.Mesh.from_file(str(OUT / f"{side}_{name}.stl"))
        tris.append(m.vectors.astype(np.float64)); cols.append(np.tile(c, (len(m.vectors), 1)))
    return np.concatenate(tris), np.concatenate(cols).astype(np.float64)


def view_matrix(elev, azim):
    """Rows = screen right, screen up, toward camera (matplotlib-style elev/azim)."""
    e, a = np.radians(elev), np.radians(azim)
    to_cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    up = np.array([0, 0, 1.0]) if abs(elev) < 89 else np.array([-np.sin(a), np.cos(a), 0]) * -1
    right = np.cross(up, to_cam); right /= np.linalg.norm(right)
    up = np.cross(to_cam, right)
    return np.stack([right, up, to_cam])


def render(tris, cols, elev, azim, size=(900, 600), margin=30):
    M = view_matrix(elev, azim)
    v = tris @ M.T                                   # (n,3,3) in camera space
    xy = v[..., :2].reshape(-1, 2)
    lo, hi = xy.min(0), xy.max(0)
    s = min((size[0] - 2 * margin) / (hi - lo)[0], (size[1] - 2 * margin) / (hi - lo)[1])
    off = (np.array(size) - (hi - lo) * s) / 2
    px = (v[..., 0] - lo[0]) * s + off[0]
    py = size[1] - ((v[..., 1] - lo[1]) * s + off[1])
    pz = v[..., 2]
    n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([-0.35, 0.55, 0.75]); light /= np.linalg.norm(light)
    shade = 0.30 + 0.55 * np.abs(n @ light) + 0.25 * np.abs(n[:, 2]) ** 8   # lambert + soft spec
    rgb = np.clip(cols * shade[:, None], 0, 255)
    W, H = size
    zbuf = np.full((H, W), -np.inf); img = np.full((H, W, 3), 255.0)
    for i in range(len(tris)):
        x0, y0, z0 = px[i], py[i], pz[i]
        xmin, xmax = int(max(np.floor(x0.min()), 0)), int(min(np.ceil(x0.max()), W - 1))
        ymin, ymax = int(max(np.floor(y0.min()), 0)), int(min(np.ceil(y0.max()), H - 1))
        if xmin > xmax or ymin > ymax:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        d = (y0[1] - y0[2]) * (x0[0] - x0[2]) + (x0[2] - x0[1]) * (y0[0] - y0[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((y0[1] - y0[2]) * (gx - x0[2]) + (x0[2] - x0[1]) * (gy - y0[2])) / d
        w1 = ((y0[2] - y0[0]) * (gx - x0[2]) + (x0[0] - x0[2]) * (gy - y0[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not inside.any():
            continue
        z = w0 * z0[0] + w1 * z0[1] + w2 * z0[2]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        img[ymin:ymax + 1, xmin:xmax + 1][upd] = rgb[i]
    return Image.fromarray(img.astype(np.uint8))


# (label, elev, azim, reference photo filename in ref_dir or None)
COMPARE = {
    "RH": [
        ("front, straight (vs ClassicEuro RH)", 6, -90, "ref5_rh.png"),
        ("front, straight - inboard end (vs Allums RH)", 6, -96, "allums_rh_left.png"),
        ("front angled from inboard end (vs ClassicEuro close-up)", 22, -122, "ref2.jpg"),
        ("inboard end close (vs ClassicEuro)", 18, -125, "ref2_leftend.png"),
        ("top view (plan wrap)", 89.9, -90, None),
    ],
    "LH": [
        ("LH front angled (vs Soon Heng ARIC LH)", 12, -70, "soon_front.png"),
        ("LH inboard end, rib crests/valleys (vs Soon Heng)", 14, -55, "soon_front_rightend.png"),
        ("LH inside, straight (vs Soon Heng inside)", 5, 90, "soon_inside.png"),
    ],
}


def sheet(ref_dir):
    rows = []
    for side, views in COMPARE.items():
        tris, cols = load(side)
        for label, elev, azim, ref in views:
            r = render(tris, cols, elev, azim)
            r.save(OUT / f"{side}_{label.split(' (')[0].replace(' ', '_').replace(',', '').replace('/', '')}.png")
            row = Image.new("RGB", (1820, 640), "white")
            if ref and (ref_dir / ref).exists():
                p = Image.open(ref_dir / ref).convert("RGB"); p.thumbnail((900, 600)); row.paste(p, (10, 30))
            row.paste(r, (910, 30))
            ImageDraw.Draw(row).text((10, 8), f"{side}: {label}    [left: reference photo | right: model]", fill="black")
            rows.append(row)
    out = Image.new("RGB", (1820, 640 * len(rows)), "white")
    for i, r in enumerate(rows):
        out.paste(r, (0, 640 * i))
    out.save(OUT / "comparison_sheet.png")
    return OUT / "comparison_sheet.png"


if __name__ == "__main__":
    print(sheet(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")))
