"""Clear TPU coaster with PETG drawings sealed inside -> Bambu Studio 3MF (H2D: TPU on one nozzle, PETG on the other).

    python cad/coaster/coaster.py PICTURE.png [--out cad/print_files/coaster/coaster_birds.3mf]

PICTURE: flat 2D art (owner's ChatGPT picture, prompt in cad/coaster/README.md): the LEFT half holds the colour version,
a thin grey circle = the coaster edge, solid red / blue / orange shapes on white. The picture itself stays out of git.

Layers (printed flat, 0.2 mm layers):  TPU base 1.6  |  PETG drawing 0.6 (TPU fills around and inside it)  |  TPU cover 0.8
Slots: 1 clear TPU (nozzle 2, external spool), 2 red, 3 blue, 4 orange PETG (nozzle 1, AMS).
"""
import argparse
import json
import sys
from pathlib import Path

import contourpy
import numpy as np
import trimesh
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from threemf import write_bambu_3mf, write_bambu_3mf_multi  # noqa: E402

D, T = 95.0, 3.0                  # coaster diameter, thickness (owner, 2026-11-20)
Z0, Z1 = 1.6, 2.2                 # PETG drawing between these heights (TPU cover 0.8 on top)
MIN_W = 0.7                       # narrowest printable feature
COLOURS = {"red": "#C8102E", "blue": "#1F5FA8", "orange": "#E07A1F"}
TPU_COLOUR = "#E8F1F5"            # clear


def colour_masks(img):
    r, g, b = (img[..., i] for i in range(3))
    sat = img.max(2) - img.min(2)
    return {"red": (r > 150) & (g < 90) & (b < 100) & (sat > 80),
            "blue": (b > 110) & (r < 80) & (sat > 60),
            "orange": (r > 180) & (g > 90) & (g < 190) & (b < 80)}


def find_circle(img):
    """the thin grey ring = coaster edge: centre and radius in pixels"""
    r, g, b = (img[..., i] for i in range(3))
    grey = (abs(r - g) < 20) & (abs(g - b) < 20) & (r > 60) & (r < 200)
    ys, xs = np.nonzero(grey)
    return (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min()) / 2


def mask_to_mm(m, cx, cy, rpx, up=4, smooth=1.3):
    """mask -> shapely geometry in mm, centre (0, 0), y up. Upsample + gaussian = smooth edges, even-odd for holes."""
    f = gaussian_filter(zoom(m.astype(float), up, order=1), up * smooth)
    lines = contourpy.contour_generator(z=f, line_type="Separate").lines(0.5)
    shapes = sorted((p for p in (Polygon(l).buffer(0) for l in lines if len(l) > 8) if p.area > 20), key=lambda p: -p.area)
    depth = [sum(1 for q in shapes if q.area > p.area and q.contains(p)) for p in shapes]
    res = unary_union([p for p, d in zip(shapes, depth) if d % 2 == 0])
    res = res.difference(unary_union([p for p, d in zip(shapes, depth) if d % 2 == 1]))
    s = D / (2 * rpx) / up
    res = affinity.translate(affinity.scale(res, s, -s, origin=(0, 0)), -cx * D / (2 * rpx), cy * D / (2 * rpx))
    h = MIN_W / 2
    return res.buffer(-h).buffer(h).buffer(h).buffer(-h).simplify(0.03)   # drop features and gaps < 0.7 mm


def extrude(geom, z0, z1):
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if isinstance(g, Polygon) and g.area > 0.05:
            m = trimesh.creation.extrude_polygon(g, z1 - z0)
            m.apply_translation((0, 0, z0))
            out.append(m)
    return trimesh.util.concatenate(out)


def build(picture):
    img = np.array(Image.open(picture).convert("RGB")).astype(float)
    img = img[:, : img.shape[1] // 2]                       # left half = colour version
    cx, cy, rpx = find_circle(img)
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 < (rpx - 12) ** 2
    art = {k: mask_to_mm(m & inside, cx, cy, rpx) for k, m in colour_masks(img).items()}
    disc = Point(0, 0).buffer(D / 2, 256)
    allart = unary_union(list(art.values()))
    margin = D / 2 - max(Point(0, 0).distance(Point(c)) for g in allart.geoms for c in g.exterior.coords)
    print(f"picture {img.shape[1]}x{img.shape[0]} px (left half), ring r={rpx:.0f} px, TPU margin to edge {margin:.1f} mm")
    for k, g in art.items():
        print(f"  {k}: {len(getattr(g, 'geoms', [g]))} shapes, {g.area:.0f} mm2")
    tpu = trimesh.boolean.union([extrude(disc, 0, Z0), extrude(disc.difference(allart), Z0 - 0.01, Z1 + 0.01),
                                 extrude(disc, Z1, T)], engine="manifold")
    parts = [("clear_tpu", tpu, 1)] + [(f"petg_{k}", extrude(art[k], Z0, Z1), i) for i, k in enumerate(COLOURS, start=2)]
    return parts, art


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture")
    ap.add_argument("--out", default=str(HERE.parent / "print_files" / "coaster" / "coaster_birds.3mf"))
    ap.add_argument("--set4", action="store_true", help="4 coasters on one plate (45 min each instead of 58); slice with --tower-x 270 --tower-y 140 --tower-width 30")
    ap.add_argument("--stl", action="store_true", help="also write one STL per part (for print_test.py)")
    a = ap.parse_args()
    parts, _ = build(a.picture)
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = [TPU_COLOUR] + list(COLOURS.values())
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    cfg["filament_type"] = ["TPU", "PETG", "PETG", "PETG"]
    cfg["sparse_infill_density"], cfg["sparse_infill_pattern"] = "100%", "zig-zag"   # solid = clearer TPU (grid fails at 100%)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    if a.set4:
        write_bambu_3mf_multi(out, [(f"coaster_{i + 1}", parts, (105 + 100 * (i % 2), 110 + 100 * (i // 2))) for i in range(4)],
                              json.dumps(cfg, indent=4))
    else:
        write_bambu_3mf(out, parts, (175.0, 160.0), "coaster_birds", json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
