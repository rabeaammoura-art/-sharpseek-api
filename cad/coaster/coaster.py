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


def build(picture, heart=None):
    img = np.array(Image.open(picture).convert("RGB")).astype(float)
    img = img[:, : img.shape[1] // 2]                       # left half = colour version
    cx, cy, rpx = find_circle(img)
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 < (rpx - 12) ** 2
    art = {k: mask_to_mm(m & inside, cx, cy, rpx) for k, m in colour_masks(img).items()}
    disc = Point(0, 0).buffer(D / 2, 256)
    if heart:
        disc, art = pack_heart(art, heart)
    allart = unary_union(list(art.values()))
    margin = min(disc.exterior.distance(Point(c)) for g in allart.geoms for c in g.exterior.coords)
    print(f"picture {img.shape[1]}x{img.shape[0]} px (left half), ring r={rpx:.0f} px, TPU margin to edge {margin:.1f} mm")
    for k, g in art.items():
        thin = g.difference(g.buffer(-0.35).buffer(0.35))
        print(f"  {k}: {len(getattr(g, 'geoms', [g]))} shapes, {g.area:.0f} mm2, under 0.7 mm: {thin.area:.2f} mm2")
    tpu = trimesh.boolean.union([extrude(disc, 0, Z0), extrude(disc.difference(allart), Z0 - 0.01, Z1 + 0.01),
                                 extrude(disc, Z1, T)], engine="manifold")
    parts = [("clear_tpu", tpu, 1)] + [(f"petg_{k}", extrude(art[k], Z0, Z1), i) for i, k in enumerate(COLOURS, start=2)]
    return parts, art


def heart_outline(width):
    """classic heart curve scaled to `width`, centred, tip and top notch rounded (1.5 mm)"""
    t = np.linspace(0, 2 * np.pi, 600)
    x = 16 * np.sin(t) ** 3
    y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
    h = Polygon(np.c_[x, y]).buffer(0)
    h = affinity.scale(h, width / 32, width / 32, origin=(0, 0)).buffer(-1.5).buffer(1.5)
    h = affinity.scale(h, width / (h.bounds[2] - h.bounds[0]), width / (h.bounds[2] - h.bounds[0]), origin=(0, 0))
    b = h.bounds
    return affinity.translate(h, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)


def printable(g):
    """after shrinking: thicken a little, close gaps < 0.8 mm (they would fuse anyway), keep everything >= 0.7 mm"""
    g = g.buffer(0.15).buffer(0.4).buffer(-0.4)
    thin = g.difference(g.buffer(-0.36).buffer(0.36))
    if thin.area > 0.01:
        g = g.union(thin.buffer(0.3)).buffer(0.4).buffer(-0.4)
    return g


def hang_loop(outline, outer=(7.0, 9.0), hole=(3.6, 5.0)):
    """oval TPU loop in the top notch of the heart (owner's mark 2026-11-20) -> (loop ring, keep-out for the drawings)"""
    from shapely.geometry import LineString
    top = outline.intersection(LineString([(0, -200), (0, 200)])).bounds[3]      # bottom of the notch on the centre line
    cy = top                                                                       # raise the loop until its hole is clear of the
    while True:                                                                    # two lobes (0.8 mm TPU wall at least)
        ring = affinity.scale(Point(0, cy).buffer(1, 64), outer[0] / 2, outer[1] / 2)
        hole_ = affinity.scale(Point(0, cy + 0.5).buffer(1, 64), hole[0] / 2, hole[1] / 2)
        if not hole_.intersects(outline.buffer(0.8)):
            break
        cy += 0.1
    ring = ring.union(Point(0, top).buffer(1.2)).convex_hull                     # fill the V between loop and notch
    return ring.difference(hole_), ring


def pack_heart(art, width, gap=2.0, edge=2.6):
    """re-place every shape inside a heart, biggest first, as near as possible to its spot on the round picture;
    the largest common shrink factor that fits all shapes wins"""
    from shapely.prepared import prep
    outline = heart_outline(width)
    loop, ring = hang_loop(outline)
    inner = prep(outline.buffer(-edge).difference(ring.buffer(edge)))
    outline = outline.union(loop)
    items = sorted(((k, g) for k, geo in art.items() for g in geo.geoms), key=lambda kg: -kg[1].area)
    grid = [(x, y) for x in np.arange(-width / 2, width / 2, 0.5) for y in np.arange(-width / 2, width / 2, 0.5)]
    for f in np.arange(0.85, 0.30, -0.02):
        placed, occ = [], None
        for k, g in items:
            c = g.centroid
            g0 = printable(affinity.translate(affinity.scale(g, f, f, origin=c), -c.x, -c.y))
            tx, ty = c.x * width / D, c.y * width / D * 0.95
            for x, y in sorted(grid, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2):
                gg = affinity.translate(g0, x, y)
                if inner.contains(gg) and (occ is None or not occ.intersects(gg)):
                    placed.append((k, gg)); occ = unary_union([p for _, p in placed]).buffer(gap); break
            else:
                break
        if len(placed) == len(items):
            print(f"heart {width:.0f} mm: {len(placed)} shapes at {f * 100:.0f}% of their round-coaster size")
            return outline, {k: unary_union([g for kk, g in placed if kk == k]) for k in art}
    raise SystemExit("shapes do not fit in the heart")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture")
    ap.add_argument("--out", default=str(HERE.parent / "print_files" / "coaster" / "coaster_birds.3mf"))
    ap.add_argument("--set4", action="store_true", help="4 coasters on one plate (45 min each instead of 58); slice with --tower-x 270 --tower-y 140 --tower-width 30")
    ap.add_argument("--heart", type=float, metavar="WIDTH", help="heart-shaped coaster this wide (mm), same drawings re-placed inside")
    ap.add_argument("--stl", action="store_true", help="also write one STL per part (for print_test.py)")
    a = ap.parse_args()
    parts, _ = build(a.picture, a.heart)
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
        write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
