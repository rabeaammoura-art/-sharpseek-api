"""Clear TPU coaster from a FLAT colour picture (owner 2026-11-23: monogram R + leafy branch), face down.

    python cad/coaster/coaster_picture.py PICTURE --out OUT.3mf [--stl]

Picture: a round flat design (background circle in one colour, inks in a few flat colours). Colours are fixed below
(black letter, olive leaves/berries, brown stems). Layers like coaster_text.py: TPU 0.4 (face, on the plate) |
inlay 0.6 | TPU 2.0, rounded edges, mirrored. Thin stems are thickened to >= 0.9 mm. Picture stays out of git.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import coaster, coaster_text as ct     # noqa: E402
from threemf import write_bambu_3mf    # noqa: E402

INKS = {  # name: (rgb, tolerance, slot colour)
    "black": ((15, 15, 15), 70, "#141414"),
    "olive": ((128, 130, 55), 45, "#8F8B3A"),
    "brown": ((160, 85, 30), 45, "#B4703A"),
}
ART_D = 88.0    # the picture's background circle -> this diameter (mm); keeps the art >= 3 mm inside the Ø95 edge


WHITE_PALETTE = {"purple": (110, 62, 148), "crimson": (205, 40, 88), "rose_dark": (145, 5, 48), "olive": (125, 122, 38), "brown": (145, 100, 60),
                 "white": (242, 242, 242)}
WHITE_COLS = {"purple": "#7B4FA0", "crimson": "#B0123F", "olive": "#8F8B3A", "brown": "#B4703A"}
FIT_R = 43.5    # mm: farthest ink from the centre (TPU edge >= 4 mm)


def rose_template(pic, head_only=False):
    """rose HEAD of a black stencil picture (petals = white gaps): (filled silhouette, white gap lines) in px units, centred"""
    im = np.array(Image.open(pic).convert("L")).astype(float)
    im = np.pad(im, 12, constant_values=255)        # white margin: a shape touching the picture edge must still close
    m = im < 90
    w = m.sum(1); rows = np.nonzero(w)[0]
    top = rows.min(); cut = top + int(0.45 * (rows.max() - top))     # head = upper part, above the leaves
    for y in range(top + 21, rows.max()):                             # first narrow row (neck of the stem) below the head
        if w[y] < 0.4 * w[top + 20:y].max() and y > top + 0.35 * (rows.max() - top):
            cut = y; break
    head = m.copy()
    if not head_only:
        head[cut:] = False
    big = max(im.shape) > 600                                         # sharp, large picture: little upsampling needed
    g = coaster.mask_to_mm(head, im.shape[1] / 2, im.shape[0] / 2, 47.5, up=1 if big else 4, smooth=1.0 if big else 0.6, clean=False)
    full = unary_union([q for q in getattr(g, "geoms", [g]) if q.area > 4])   # all head pieces (the white lines split it)
    rc = 0.03 * max(im.shape) if big else 6                           # closing radius ~ white line width
    fill = full.buffer(rc, 16).buffer(-rc, 16)                        # close the gaps -> silhouette
    from shapely.geometry import Polygon as _P
    fill = unary_union([_P(q.exterior) for q in getattr(fill, "geoms", [fill])])   # no holes
    if head_only and not big:   # drop the sepals / stem stub under the bloom of the small screenshot rose (drips at 17 mm)
        from shapely.geometry import box as _box
        b = fill.bounds; keep = _box(b[0] - 1, b[1] + 0.17 * (b[3] - b[1]), b[2] + 1, b[3] + 1)
        fill = fill.intersection(keep).buffer(-2, 16).buffer(2, 16); full = full.intersection(fill)
    lines = fill.difference(full).buffer(-0.5).buffer(0.5)
    c = fill.centroid
    return affinity.translate(fill, -c.x, -c.y), affinity.translate(lines, -c.x, -c.y)


def main_white(a):
    img = np.array(Image.open(a.picture).convert("RGB")).astype(float)
    names = list(WHITE_PALETTE)
    d = np.stack([np.sqrt(((img - np.array(WHITE_PALETTE[k])) ** 2).sum(2)) for k in names], -1)
    lab = d.argmin(-1)                                   # nearest palette colour (rose swirls -> crimson)
    ink = lab != names.index("white")
    ys, xs = np.nonzero(ink)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    rmax = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2).max()
    rpx = rmax * (ct.D / 2) / FIT_R
    print(f"picture {img.shape[1]}x{img.shape[0]}, design {xs.max() - xs.min()}x{ys.max() - ys.min()} px -> {2 * FIT_R / (2 * rmax) * (xs.max() - xs.min()):.0f} mm wide")
    geo = {}
    dark = lab == names.index("rose_dark")
    lab = np.where(dark, names.index("crimson"), lab)    # roses as one colour, the dark swirls cut out below
    for k in ("purple", "crimson", "olive", "brown"):
        m = lab == names.index(k)
        geo[k] = coaster.mask_to_mm(m, cx, cy, rpx, up=4 if k == "brown" else 2, smooth=1.6 if k == "brown" else 0.9, clean=False)
        geo[k] = geo[k].buffer(-0.12, 8).buffer(0.12, 8)  # drop anti-alias specks
    # owner 2026-11-26: damask roses must look like roses. The picture's swirls are ~1 mm bands in a ~10 mm rose (too fine
    # to trace), so each open rose gets a clean drawn swirl cut as CLEAR lines (0.7 mm): spiral heart + two petal arcs.
    from shapely.geometry import LineString
    roses = [q for q in getattr(geo["crimson"], "geoms", [geo["crimson"]]) if q.area > 40]
    cuts = []
    for q in roses:
        c = q.centroid; R = np.sqrt(q.area / np.pi)
        turns = 1.75                                   # one continuous spiral (rose seen from above): 0.7 mm clear line,
        t = np.linspace(0.6, turns * 2 * np.pi, 260)    # ~1.2 mm crimson petal band between its turns
        rr = 0.78 * R * t / t[-1]
        cy0 = c.y + 0.08 * R
        spiral = LineString(np.c_[c.x + rr * np.cos(t), cy0 + 0.9 * rr * np.sin(t)])
        arcs = []
        cuts.append(spiral.buffer(0.35, 8).intersection(q.buffer(-0.55)))
    swirls = unary_union(cuts)
    if a.rose_pic:   # owner 2026-11-26: real rose head from a stencil picture instead of the drawn spiral
        tpl_fill, tpl_lines = rose_template(a.rose_pic, a.rose_head_only)
        new_fill, new_lines = [], []
        for q in roses:
            c = q.centroid; R = np.sqrt(q.area / np.pi) * a.rose_scale
            b = tpl_fill.bounds; k = 2 * R / max(b[2] - b[0], b[3] - b[1])
            place = lambda g: affinity.translate(affinity.scale(g, k, k, origin=(0, 0)), c.x, c.y)
            f = place(tpl_fill); ln0 = place(tpl_lines)
            ln = ln0.union(ln0.difference(ln0.buffer(-0.35, 8).buffer(0.35, 8)).buffer(0.15, 8))   # only thin lines grow, to ~0.7 mm
            new_fill.append(f); new_lines.append(ln.intersection(f.buffer(-0.3)))
        fill = unary_union(new_fill); lines = unary_union(new_lines).buffer(0.0)
        geo["crimson"] = geo["crimson"].difference(unary_union([r.buffer(0.2) for r in roses])).union(fill).difference(lines)
        geo["crimson"] = geo["crimson"].buffer(-0.2, 8).buffer(0.2, 8)
        swirls = lines
        geo["olive"] = geo["olive"].difference(fill.buffer(0.6)); geo["brown"] = geo["brown"].difference(fill.buffer(0.6))
    if not a.rose_pic:
        geo["crimson"] = geo["crimson"].difference(swirls).buffer(-0.3, 8).buffer(0.3, 8)
    if a.black and not a.clear_lines:   # owner 2026-11-26: swirls black (not clear) and the letter black too -> one black slot
        geo["purple"] = geo["purple"].union(swirls.buffer(-0.02).buffer(0.02))
    print(f"roses with a drawn swirl: {len(roses)} (R {', '.join(f'{np.sqrt(q.area / np.pi):.1f}' for q in roses)} mm)")
    geo["brown"] = geo["brown"].buffer(0.22, 16).buffer(0.35, 16).buffer(-0.35, 16).buffer(-0.25, 16).buffer(0.25, 16).simplify(0.03)
    taken = None
    for k in ("purple", "crimson", "olive", "brown"):    # no two colours on one spot
        if taken is not None:
            geo[k] = geo[k].difference(taken)
        taken = geo[k] if taken is None else taken.union(geo[k])
    for k, gg in geo.items():
        t = gg.difference(gg.buffer(-0.35).buffer(0.35))
        print(f"{k}: {len(getattr(gg, 'geoms', [gg]))} pieces, {gg.area:.0f} mm2, under 0.7 mm {t.area:.2f} mm2")
    order = ["purple", "crimson", "olive", "brown"]
    inks = [(k, coaster.extrude(geo[k].buffer(0.01, 4).buffer(-0.01, 4).simplify(0.01), ct.Z0, ct.Z1), i) for i, k in enumerate(order, start=2)]
    for k, m, _ in inks:
        if not m.is_volume:
            m.merge_vertices(); m.update_faces(m.nondegenerate_faces()); m.fix_normals()
        print(f"  ink {k}: volume ok={m.is_volume}")
    allink = trimesh.boolean.union([m for _, m, _ in inks], engine="manifold")
    tpu = trimesh.boolean.difference([ct.rounded_disc(), allink], engine="manifold")
    parts = [(n, coaster.mirror_x(m), s) for n, m, s in [("clear_tpu", tpu, 1)] + inks]
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    from threemf import widen_filaments
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg = widen_filaments(cfg, 5, (HERE.parent / "config" / "bambu_project_settings.config").read_bytes())
    cols = dict(WHITE_COLS, purple="#141414") if a.black else WHITE_COLS
    cfg["filament_colour"] = ["#E8F1F5"] + [cols[k] for k in order]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1", "1"]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture"); ap.add_argument("--out", required=True); ap.add_argument("--stl", action="store_true")
    ap.add_argument("--purple", action="store_true", help="letter + berries purple instead of black / olive")
    ap.add_argument("--rose-pic", help="with --white: replace each rose by the head of this black rose stencil picture")
    ap.add_argument("--rose-head-only", action="store_true", help="the rose picture is already cropped to the head")
    ap.add_argument("--rose-scale", type=float, default=1.7, help="rose size vs the picture's roses")
    ap.add_argument("--clear-lines", action="store_true", help="rose petal lines clear (TPU) even with --black (letter stays black)")
    ap.add_argument("--black", action="store_true", help="with --white: letter + rose swirls black (swirls otherwise clear)")
    ap.add_argument("--white", action="store_true", help="design on a WHITE background (no circle): purple letter, crimson "
                    "roses, olive leaves, brown stems (owner 2026-11-26); the whole design is fitted inside the coaster")
    a = ap.parse_args()
    if a.white:
        return main_white(a)
    img = np.array(Image.open(a.picture).convert("RGB")).astype(float)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    tan = (abs(r - 205) < 30) & (abs(g - 172) < 30) & (abs(b - 128) < 35)
    ys, xs = np.nonzero(tan)
    cx, cy, rpx = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min()) / 2
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 < (rpx - 6) ** 2
    scale_r = rpx * ct.D / ART_D                       # mask_to_mm maps scale_r pixels to D/2 mm
    geo = {}
    for k, (rgb, tol, _) in INKS.items():
        m = (np.sqrt(((img - np.array(rgb)) ** 2).sum(2)) < tol) & inside
        sm = 1.6 if k == "brown" else 0.8             # stems: smoother trace (owner mark 2026-11-23: rough stem)
        geo[k] = coaster.mask_to_mm(m, cx, cy, scale_r, up=4 if k == "brown" else 2, smooth=sm, clean=False)
    # thin stems / stalks (~0.65 mm in the picture): +0.44 mm all round -> ~1.1 mm
    st = geo["brown"].buffer(0.22, 16)                                                   # even thickening
    geo["brown"] = st.buffer(0.35, 16).buffer(-0.35, 16).buffer(-0.25, 16).buffer(0.25, 16).simplify(0.03)   # close + open = smooth
    if a.purple:   # owner 2026-11-23: berries and the letter in purple (berries = small round olive blobs)
        ol = list(getattr(geo["olive"], "geoms", [geo["olive"]]))
        berry = lambda q: q.area < 15.0 and 4 * np.pi * q.area / q.length ** 2 > 0.75   # berries 6-11 mm2, leaves >= 21
        geo["purple"] = unary_union([geo["black"]] + [q for q in ol if berry(q)])
        geo["olive"] = unary_union([q for q in ol if not berry(q)])
        del geo["black"]
        print(f"berries -> purple: {sum(1 for q in ol if berry(q))}")
    taken = None
    for k in [c for c in ("black", "purple", "olive", "brown") if c in geo]:   # no two colours on one spot (leaves win over stems)
        if taken is not None:
            geo[k] = geo[k].difference(taken)
        taken = geo[k] if taken is None else taken.union(geo[k])
    for k, gg in geo.items():
        t = gg.difference(gg.buffer(-0.35).buffer(0.35))
        print(f"{k}: {len(getattr(gg, 'geoms', [gg]))} pieces, {gg.area:.0f} mm2, under 0.7 mm {t.area:.2f} mm2, bounds {[round(v, 1) for v in gg.bounds]}")
    order = [c for c in ("black", "purple", "olive", "brown") if c in geo]
    inks = [(k, coaster.extrude(geo[k].buffer(0), ct.Z0, ct.Z1), i) for i, k in enumerate(order, start=2)]
    allink = trimesh.boolean.union([m for _, m, _ in inks], engine="manifold")
    tpu = trimesh.boolean.difference([ct.rounded_disc(), allink], engine="manifold")
    parts = [(n, coaster.mirror_x(m), s) for n, m, s in [("clear_tpu", tpu, 1)] + inks]
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cols = {"black": "#141414", "purple": "#7B4FA0", "olive": "#8F8B3A", "brown": "#B4703A"}
    cfg["filament_colour"] = ["#E8F1F5"] + [cols[k] for k in order]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
