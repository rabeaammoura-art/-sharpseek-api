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
Z0, Z1 = 1.6, 2.2                 # PETG drawing between these heights (TPU cover 0.8 on top); --layers changes all three
ROUND = 0.0                       # radius of the rounded outer edges (--round)
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


def mask_to_mm(m, cx, cy, rpx, up=4, smooth=1.3, clean=True):
    """mask -> shapely geometry in mm, centre (cx, cy) -> (0, 0), y up, rpx pixels = D/2 mm.
    Upsample + gaussian = smooth edges, even-odd for holes."""
    f = gaussian_filter(zoom(m.astype(float), up, order=1), up * smooth)
    lines = contourpy.contour_generator(z=f, line_type="Separate").lines(0.5)
    shapes = sorted((p for p in (Polygon(l).buffer(0) for l in lines if len(l) > 8) if p.area > 20), key=lambda p: -p.area)
    depth = [sum(1 for q in shapes if q.area > p.area and q.contains(p)) for p in shapes]
    res = unary_union([p for p, d in zip(shapes, depth) if d % 2 == 0])
    res = res.difference(unary_union([p for p, d in zip(shapes, depth) if d % 2 == 1]))
    s = D / (2 * rpx) / up
    res = affinity.translate(affinity.scale(res, s, -s, origin=(0, 0)), -cx * D / (2 * rpx), cy * D / (2 * rpx))
    if not clean:
        return res.simplify(0.02)
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


def heart_picture_art(picture, outline, loop_keep, edge=2.4, gap=1.2, grow_top=True):
    """drawings from the owner's heart picture (cream heart with flat red / blue / orange shapes), kept at their places,
    scaled by the picture's heart width and then fitted (common shrink + shift) inside our own heart outline"""
    img = np.array(Image.open(picture).convert("RGB")).astype(float)
    r, g, b = (img[..., i] for i in range(3))
    cream = (r > 235) & (g > 220) & (b > 185)
    ys, xs = np.nonzero(cream)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    inside = np.zeros_like(cream); inside[y0:y1 + 1, x0:x1 + 1] = True
    width = outline.bounds[2] - outline.bounds[0]
    rpx = (x1 - x0) / width * D / 2                     # so that mask_to_mm maps the picture's heart width to ours
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    art = {k: mask_to_mm(m & inside, cx, cy, rpx, up=3, smooth=0.8, clean=False) for k, m in colour_masks(img).items()}
    from shapely.prepared import prep
    inner = prep(outline.buffer(-edge).difference(loop_keep.buffer(edge)))
    pieces = [(k, g) for k, geo in art.items() for g in getattr(geo, "geoms", [geo])]

    def layout(f, sq, dy, pos):                        # shapes scaled f about their own centre, places scaled pos (x) / pos*sq (y)
        out = []
        for k, g in pieces:
            c = g.centroid
            out.append((k, affinity.translate(affinity.scale(g, f, f, origin=c), c.x * pos - c.x, c.y * pos * sq + dy - c.y)))
        return out
    best = None
    for pos in np.arange(0.80, 1.301, 0.05):
        for sq in (1.0, 0.95, 0.9, 0.85):
            for dy in np.arange(-6, 6.01, 0.5):
                lo, hi = 0.4, pos
                if best and hi <= best[0]:
                    continue
                for _ in range(12):
                    f = (lo + hi) / 2
                    L = layout(f, sq, dy, pos)
                    ok = all(inner.contains(g) for _, g in L) and all(
                        a.distance(b) >= gap for i, (_, a) in enumerate(L) for _, b in L[i + 1:])
                    lo, hi = (f, hi) if ok else (lo, f)
                if best is None or lo > best[0] + 1e-3:
                    best = (lo, dy, sq, pos)
    f, dy, sq, pos = best
    print(f"heart picture {img.shape[1]}x{img.shape[0]} px, heart {x1 - x0} px wide; shapes at {f * 100:.0f}%, places at {pos * 100:.0f}% "
          f"(height x{sq:.2f}) shifted {dy:+.1f} mm")
    placed = layout(f, sq, dy, pos)
    if grow_top:
        placed = fill_top(placed, inner, gap, outline)
    gaps = min(a.distance(b) for i, (_, a) in enumerate(placed) for _, b in placed[i + 1:])
    print(f"  smallest gap between shapes {gaps:.2f} mm")
    out = {}
    for k in art:
        geo = unary_union([g for kk, g in placed if kk == k])
        out[k] = geo                                    # traced edge kept as is (no buffer passes: they make the edge beaded)
    return out


# small hanging heart (owner 2026-11-20): only a few shapes, picked from the heart picture by their pixel position there.
# (colour, picture x, picture y, target centre as fraction of the heart width (x, y), target size as fraction of width)
PICKS = {"bird_2hearts": [("blue", 660, 370, (0.02, -0.10), 0.58),
                          ("red", 670, 195, (-0.25, 0.17), 0.22),
                          ("red", 1130, 480, (0.25, 0.17), 0.22)],
         # owner 2026-11-20: swallow (--shape-pic) higher up, the hearts trailing behind its tail
         "swallow_trail": [("blue", 660, 370, (0.07, 0.08), 0.58),
                           ("red", 790, 830, (-0.25, 0.17), 0.24),      # owner: one more, a bit bigger, above the tail
                           ("red", 670, 195, (-0.22, -0.13), 0.19),
                           ("red", 1130, 480, (0.0, -0.27), 0.14)]}


def trace_shape(picture, smooth=1.6):
    """one flat dark/coloured shape on white (e.g. the owner's swallow) -> shapely geometry centred at (0, 0), size arbitrary"""
    im = Image.open(picture)
    rgba = np.array(im.convert("RGBA")).astype(float)
    m = (rgba[..., :3].min(2) < 160) & (rgba[..., 3] > 128)          # not white and not transparent
    ys, xs = np.nonzero(m)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    g = mask_to_mm(m, cx, cy, D / 2 / 0.05, up=2, smooth=smooth, clean=False)   # 1 px = 0.05 mm before rescaling
    return max(getattr(g, "geoms", [g]), key=lambda q: q.area)


def heart_picks(picture, outline, loop_keep, preset, edge=1.6, gap=1.0, shape_pic=None):
    """a few shapes from the heart picture, placed at fixed spots and scaled together as big as the heart allows"""
    img = np.array(Image.open(picture).convert("RGB")).astype(float)
    r, g, b = (img[..., i] for i in range(3))
    cream = (r > 235) & (g > 220) & (b > 185)
    ys, xs = np.nonzero(cream)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    inside = np.zeros_like(cream); inside[y0:y1 + 1, x0:x1 + 1] = True
    width = outline.bounds[2] - outline.bounds[0]
    rpx = (x1 - x0) / width * D / 2
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mm = width / (x1 - x0)
    art = {k: mask_to_mm(m & inside, cx, cy, rpx, up=4, smooth=0.8, clean=False) for k, m in colour_masks(img).items()}
    from shapely.prepared import prep
    inner = prep(outline.buffer(-edge).difference(loop_keep.buffer(edge)))
    chosen = []
    for k, px, py, (tx, ty), size in PICKS[preset]:
        p = Point((px - cx) * mm, -(py - cy) * mm)
        g = min(getattr(art[k], "geoms", [art[k]]), key=lambda q: q.distance(p))
        c = g.centroid; bx = g.bounds
        g = affinity.translate(g, -c.x, -c.y)
        chosen.append((k, g, max(bx[2] - bx[0], bx[3] - bx[1]), (tx * width, ty * width), size * width))
    if shape_pic:                                       # replace the first (main) shape by the owner's own picture
        k, _, _, t, sz = chosen[0]
        g = trace_shape(shape_pic); bx = g.bounds
        chosen[0] = (k, g, max(bx[2] - bx[0], bx[3] - bx[1]), t, sz)
    oc = outline.centroid

    # one shape at a time (main shape first, at its full target size): the free spot nearest its target,
    # shrinking that shape 4% at a time only if no spot fits
    grid = [(x, y) for x in np.arange(-width / 2, width / 2, 0.25) for y in np.arange(-width / 2, width / 2, 0.25)]
    L, occ = [], None
    for k, g, d, t, sz in chosen:
        tx, ty = oc.x + t[0], oc.y + t[1]
        cand = sorted(grid, key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2)[:4000]
        m = 1.0
        while m > 0.5:
            g0 = affinity.scale(g, m * sz / d, m * sz / d, origin=(0, 0))
            hit = next((q for q in (affinity.translate(g0, x, y) for x, y in cand)
                        if inner.contains(q) and (occ is None or not occ.intersects(q))), None)
            if hit is not None:
                break
            m -= 0.04
        L.append((k, hit)); occ = unary_union([q for _, q in L]).buffer(gap)
        c = hit.centroid
        print(f"  {k}: size {m * 100:.0f}% of target, {np.hypot(c.x - tx, c.y - ty):.1f} mm from its target spot")
    print(f"picked {len(L)} shapes ({preset})")
    return {k: unary_union([q for kk, q in L if kk == k]) for k in COLOURS}


def fill_top(placed, inner, gap, outline, max_grow=1.6, rounds=3):
    """owner 2026-11-20: enlarge the shapes in the upper half and push them into the empty lobes.
    Each upper shape (top first) takes the biggest scale (about its centre, up to max_grow) and a shift within 8 mm,
    preferring up / outward, that stays inside the heart with `gap` to every other shape."""
    ymid = outline.centroid.y
    placed = list(placed)
    shifts = sorted(((dx, dy) for dx in np.arange(-8, 8.01, 0.5) for dy in np.arange(-3, 8.01, 0.5)),
                    key=lambda d: d[0] ** 2 + d[1] ** 2)
    for _ in range(rounds):
        order = sorted((i for i, (_, g) in enumerate(placed) if g.centroid.y > ymid), key=lambda i: -placed[i][1].centroid.y)
        for i in order:
            k, g = placed[i]
            others = unary_union([h for j, (_, h) in enumerate(placed) if j != i]).buffer(gap)
            c = g.centroid
            best = None
            amax = max(h.area for _, h in placed)
            cap = min(max_grow, np.sqrt(0.55 * amax / g.area)) if g.area < 0.55 * amax else 1.15   # small shapes stay small-ish
            for sc in np.arange(cap, 1.0, -0.05):
                gs = affinity.scale(g, sc, sc, origin=c)
                for dx, dy in shifts:
                    if dx * np.sign(c.x) < -2:          # do not move towards the centre line by more than 2 mm
                        continue
                    gg = affinity.translate(gs, dx, dy)
                    if inner.contains(gg) and not others.intersects(gg):
                        best = gg
                        break
                if best is not None:
                    break
            if best is not None:
                placed[i] = (k, best)
    return placed


def build(picture, heart=None, heart_art=None, picks=None, shape_pic=None):
    img = np.array(Image.open(picture).convert("RGB")).astype(float)
    img = img[:, : img.shape[1] // 2]                       # left half = colour version
    cx, cy, rpx = find_circle(img)
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inside = (xs - cx) ** 2 + (ys - cy) ** 2 < (rpx - 12) ** 2
    art = {k: mask_to_mm(m & inside, cx, cy, rpx) for k, m in colour_masks(img).items()}
    disc = Point(0, 0).buffer(D / 2, 256)
    if heart and heart_art:
        outline = heart_outline(heart)
        loop, ring = hang_loop(outline, (5.6, 7.0), (2.8, 3.6)) if heart < 50 else hang_loop(outline)
        art = heart_picks(heart_art, outline, ring, picks, shape_pic=shape_pic) if picks else heart_picture_art(heart_art, outline, ring)
        disc = outline.union(loop)
    elif heart:
        disc, art = pack_heart(art, heart)
    allart = unary_union(list(art.values()))
    margin = min(disc.exterior.distance(Point(c)) for g in allart.geoms for c in g.exterior.coords)
    print(f"picture {img.shape[1]}x{img.shape[0]} px (left half), ring r={rpx:.0f} px, TPU margin to edge {margin:.1f} mm")
    for k, g in art.items():
        thin = g.difference(g.buffer(-0.35).buffer(0.35))
        print(f"  {k}: {len(getattr(g, 'geoms', [g]))} shapes, {g.area:.0f} mm2, under 0.7 mm: {thin.area:.2f} mm2")
    if ROUND > 0:   # rounded outer edges top and bottom (owner 2026-11-20: the heart edges were sharp): stack of 0.1 mm slabs
        n = int(round(T / 0.1)); slabs = []
        for i in range(n):
            za, zb = i * T / n, (i + 1) * T / n
            zm = (za + zb) / 2
            d = max(0.0, ROUND - zm, zm - (T - ROUND))
            inset = ROUND - np.sqrt(max(ROUND ** 2 - d ** 2, 0.0))
            sh = disc.buffer(-inset, 32)
            if Z0 < zm < Z1:
                sh = sh.difference(allart)
            slabs.append(extrude(sh, za - (0.005 if i else 0), zb + (0.005 if i < n - 1 else 0)))
        tpu = trimesh.boolean.union(slabs, engine="manifold")
    else:
        tpu = trimesh.boolean.union([extrude(disc, 0, Z0), extrude(disc.difference(allart), Z0 - 0.01, Z1 + 0.01),
                                     extrude(disc, Z1, T)], engine="manifold")
    parts = [("clear_tpu", tpu, 1)] + [(f"petg_{k}", extrude(art[k], Z0, Z1), i) for i, k in enumerate(COLOURS, start=2)
                                       if not art[k].is_empty]                 # slots stay 2 red / 3 blue / 4 orange
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
    ap.add_argument("--heart-art", metavar="PICTURE", help="with --heart: take the drawings and their places from this heart picture")
    ap.add_argument("--picks", choices=sorted(PICKS), help="with --heart-art: only these few shapes (small hanging heart)")
    ap.add_argument("--shape-pic", metavar="PICTURE", help="with --picks: replace the main shape by this flat picture (one colour on white)")
    ap.add_argument("--layers", default="1.6,0.6,0.8", help="TPU under, PETG drawing, TPU over (mm), e.g. 0.6,0.6,0.6 = "
                    "drawing in the middle, seen from both sides (owner 2026-11-20 for the hanging heart)")
    ap.add_argument("--round", type=float, default=0.0, help="round the outer edges top and bottom with this radius (mm)")
    ap.add_argument("--stl", action="store_true", help="also write one STL per part (for print_test.py)")
    a = ap.parse_args()
    global Z0, Z1, T, ROUND
    lo, mid, hi = (float(v) for v in a.layers.split(","))
    Z0, Z1, T, ROUND = lo, lo + mid, lo + mid + hi, a.round
    parts, _ = build(a.picture, a.heart, a.heart_art, a.picks, a.shape_pic)
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = [TPU_COLOUR] + list(COLOURS.values())
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    cfg["filament_type"] = ["TPU", "PETG", "PETG", "PETG"]
    cfg["sparse_infill_density"], cfg["sparse_infill_pattern"] = "100%", "zig-zag"   # solid = clearer TPU (grid fails at 100%)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    if a.set4:
        sx, sy = (a.heart + 10, a.heart + 5) if a.heart else (100, 100)
        write_bambu_3mf_multi(out, [(f"coaster_{i + 1}", parts, (205 - sx - 5 + sx * (i % 2), 110 + sy * (i // 2))) for i in range(4)],
                              json.dumps(cfg, indent=4))
    else:
        write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
