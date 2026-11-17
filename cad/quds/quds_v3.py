"""Dome of the Rock wall art, version 3: the owner's final flat picture (GPT, 1086 x 1448) turned into clean outlines.

    python cad/quds/quds_v3.py picture.png out.json

The picture is flat (pure black / gold / white), so it is traced directly: 4x upsampling, hairline white gaps closed,
edges smoothed. The ring on top of the dome is replaced by a crescent (owner's request). The picture stays out of git.
Units: picture pixels, y down.  -> black (one piece), gold (visible cells), plate (gold area under the dome grid).
"""
import json
import sys

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Point, Polygon, box, mapping
from shapely.ops import unary_union

UP = 4
FRAME_OUT = (21.0, 17.0, 1064.5, 1427.5)
MIN_GAP = 4.0          # white gaps narrower than this (0.8 mm at 290 mm) are closed
MIN_LINE = 4.8         # black hairs thinner than this are removed


def disk(r):
    k = int(np.ceil(r)); y, x = np.mgrid[-k:k + 1, -k:k + 1]
    return x * x + y * y <= r * r


def polys(mask, sigma=0.8, min_area=8.0):
    f = ndi.gaussian_filter(mask.astype(float), sigma * UP)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 9.0)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] / UP for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        q = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4 and Polygon(r).area >= min_area]).buffer(0)
        if q.area >= min_area:
            out.append(q)
    return unary_union(out).simplify(0.1)


def crescent(cx=541.0, cy=238.0, r=36.0):
    c = Point(cx, cy).buffer(r, 64).difference(Point(cx, cy - 10).buffer(r - 8, 64))
    c = c.buffer(-2.2).buffer(2.2)                               # blunt the two horns (no needle tips)
    return unary_union([c, box(cx - 8, cy + r - 6, cx + 8, cy + r + 6)])


def build(path):
    im = Image.open(path).convert("RGB")
    big = np.asarray(im.resize((im.width * UP, im.height * UP), Image.LANCZOS)).astype(float)
    gold = (big[..., 0] - big[..., 2] > 90) & (big[..., 0] > 150)
    blk = (big.mean(2) < 120) & ~gold
    raw = blk
    dome = ndi.binary_dilation(ndi.binary_fill_holes(ndi.binary_closing(gold, structure=disk(6 * UP))), structure=disk(3 * UP))
    blk = ndi.binary_closing(blk, structure=disk(MIN_GAP / 2 * UP)) & ~gold
    blk = ndi.binary_opening(blk, structure=disk(MIN_LINE / 2 * UP))
    # the dome grid sits on the gold plate: keep every line (no thinning-out), just make the lines a little fatter
    blk = np.where(dome, ndi.binary_dilation(raw, structure=disk(0.7 * UP)), blk)
    black = polys(blk)
    black = unary_union([black.difference(box(495, 190, 587, 268)), crescent()])
    black = black.intersection(box(*FRAME_OUT)).buffer(0)
    plate = polys(ndi.binary_fill_holes(ndi.binary_closing(gold, structure=disk(6 * UP))), sigma=1.5)
    return {"black": black, "gold": plate.difference(black), "plate": plate}


if __name__ == "__main__":
    m = build(sys.argv[1])
    g = getattr(m["black"], "geoms", [m["black"]])
    loose = [x for x in g if x.area < max(y.area for y in g) and not x.intersects(m["plate"])]
    print("black pieces:", len(g), "| loose (not on the gold plate):", [(round(x.area), [round(v) for v in x.bounds]) for x in loose])
    json.dump({k: mapping(v) for k, v in m.items()}, open(sys.argv[2], "w"))
