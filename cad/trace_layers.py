"""Turn a flat-ish picture of a design (e.g. an AI mock-up) into colour layers (shapely polygons) for the plaque generator.

    python cad/trace_layers.py picture.png --crop x0,y0,x1,y1 --out cad/plaque/horse_layers.json

Every pixel is assigned to the nearest palette colour; the thin glow lines around the design are absorbed by their
neighbours, boundaries are smoothed, the biggest blob is the silhouette. Result (JSON): role -> list of polygons
(lists of rings, in design units, y up, silhouette width = 300). Roles: base (the silhouette), main, accent, animal.
"""
import argparse
import json

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union

# nearest-colour palette: label -> (rgb, role).  role None = background / ignored, "base" = plate colour (navy)
PALETTE = {
    "navy": ((30, 50, 100), "base"), "dark": ((40, 30, 35), "base"),
    "blue": ((45, 120, 215), "accent"), "cream": ((238, 214, 170), "main"),
    "yellow": ((245, 190, 35), "animal"), "bg": ((120, 90, 70), None),
}


def classify(rgb, palette=PALETTE):
    names = list(palette)
    cols = np.array([palette[n][0] for n in names], float)
    d = ((rgb[:, :, None, :] - cols[None, None]) ** 2).sum(-1)
    return d.argmin(-1), names


def smooth_labels(lab, n, sigma=1.4):
    stack = np.stack([ndi.gaussian_filter((lab == i).astype(float), sigma) for i in range(n)])
    return stack.argmax(0)


def polys_from_mask(mask, min_area=12):
    gen = contourpy.contour_generator(z=mask.astype(float), fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        poly = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if poly.area >= min_area:
            out.append(poly)
    return unary_union(out) if out else Polygon()


def trace(path, crop=None, width=300.0, sigma=1.4, glow=4, simplify=0.5, palette=None, solid_only=True, inner_bg=None):
    im = Image.open(path).convert("RGB")
    if crop:
        im = im.crop(crop)
    rgb = np.array(im).astype(float)
    palette = palette or PALETTE
    lab, names = classify(rgb, palette)
    bg = names.index("bg")
    # the silhouette comes from the solid colours only (yellow is also the glow on the floor around the design)
    fg = (lab != bg) & ((lab != names.index("yellow")) if solid_only else True)
    fg = ndi.binary_opening(fg, iterations=2)
    fg = ndi.binary_closing(fg, iterations=4)
    fg = ndi.binary_fill_holes(fg)
    comp, n = ndi.label(fg)
    if n > 1:
        sizes = ndi.sum(fg, comp, range(1, n + 1))
        fg = comp == (1 + int(np.argmax(sizes)))
    # thin yellow glow lines: an opened yellow keeps only real blobs (stars, buttons); the rest takes the neighbour's label
    lab = lab.copy()
    if glow:
        yi = names.index("yellow")
        yel = lab == yi
        blobs = ndi.binary_opening(yel, structure=np.ones((glow, glow)))
        lab[yel & ~blobs] = bg
    if inner_bg:      # background-coloured pixels enclosed by the design (e.g. the white smoke cloud) belong to this label
        lab[fg & (lab == bg)] = names.index(inner_bg)
    # fill every non-fg or thin pixel inside the silhouette with the nearest real label
    keep = fg & (lab != bg)
    idx = ndi.distance_transform_edt(~keep, return_distances=False, return_indices=True)
    lab = lab[idx[0], idx[1]]
    lab = np.where(fg, lab, bg)
    lab = smooth_labels(lab, len(names), sigma)
    lab = np.where(ndi.binary_erosion(fg, iterations=1) | (lab != bg), lab, bg)
    h, w = lab.shape
    ys, xs = np.nonzero(fg)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    s = width / (x1 - x0 + 1)
    def to_design(g):
        # pixel (col,row) -> design (x,y up), centred on the silhouette bbox
        from shapely import affinity
        g = affinity.scale(g, s, -s, origin=(0, 0))
        return affinity.translate(g, -(x0 + x1) / 2 * s, (y0 + y1) / 2 * s)
    roles = {"base": [], "main": [], "accent": [], "animal": [], "animal2": []}
    for i, nme in enumerate(names):
        role = palette[nme][1]
        if role is None:
            continue
        g = polys_from_mask(lab == i)
        if not g.is_empty:
            roles[role].append(g)
    sil = polys_from_mask(fg)
    result = {"base": to_design(sil).simplify(simplify * s)}
    # navy label areas are the plate itself: base layer = silhouette only
    for role in ("main", "accent", "animal", "animal2"):
        g = unary_union(roles[role]) if roles[role] else Polygon()
        result[role] = to_design(g).simplify(simplify * s) if not g.is_empty else g
    return result, (x1 - x0 + 1) * s, (y1 - y0 + 1) * s, {"s": s, "cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in pixels")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=float, default=300.0)
    ap.add_argument("--opts", default="{}", help="JSON of extra trace() options (palette, glow, solid_only, inner_bg)")
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    res, w, h, meta = (lambda r: r)(trace(a.image, crop, a.width, **json.loads(a.opts)))
    json.dump({"width": w, "height": h, "meta": meta, **{k: mapping(v) for k, v in res.items()}}, open(a.out, "w"))
    print(f"traced: {w:.0f} x {h:.0f} design units", {k: round(v.area) for k, v in res.items()})


if __name__ == "__main__":
    main()
