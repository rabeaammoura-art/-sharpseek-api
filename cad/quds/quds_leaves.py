"""Olive branches for the Dome of the Rock wall art: the only traced part (organic silhouettes).

    python cad/quds/quds_leaves.py picture.png leaves.json

Black pixels of the picture inside the two branch regions, minus everything the parametric model already draws;
thin leftovers (under 1 mm) are dropped, the edge is smoothed. The picture and the trace stay out of git.
"""
import json
import sys

import contourpy
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box, mapping, shape
from shapely.ops import unary_union

import quds_shapes as Q

UP = 3                                                    # work at 3x the picture resolution
REGIONS = [box(149, 139, 720, 625).difference(Q.dome_silhouette().buffer(14)).difference(box(515, 325, 600, 480)),  # top-left
           Polygon([(490, 1310), (490, 1255), (560, 1170), (625, 1098), (795, 1098), (795, 955), (930, 955), (930, 1310)])]


def raster(geom, shape_hw):
    im = Image.new("L", (shape_hw[1], shape_hw[0]), 0); d = ImageDraw.Draw(im)
    for g in getattr(geom, "geoms", [geom]):
        d.polygon([(x * UP, y * UP) for x, y in g.exterior.coords], fill=1)
        for r in g.interiors:
            d.polygon([(x * UP, y * UP) for x, y in r.coords], fill=0)
    return np.asarray(im).astype(bool)


def disk(r):
    k = int(np.ceil(r)); y, x = np.mgrid[-k:k + 1, -k:k + 1]
    return x * x + y * y <= r * r


def trace(path, min_w=4.4, sigma=0.9):
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    lum = ndi.zoom(im.mean(2), UP, order=3)
    gold = ndi.zoom(((im[..., 0] - im[..., 2] > 95) & (im[..., 0] > 150)).astype(float), UP, order=1) > 0.5
    T = (lum < 68) & ~gold                                  # 68: the frame's soft shadow on the wall stays out
    P = raster(Q.build()["black"], T.shape)
    R = raster(unary_union(REGIONS), T.shape)
    T = ndi.binary_closing(T & R, structure=disk(1.7 * UP)) & R      # highlight lines between overlapping leaves
    D = ndi.binary_opening(T & ~P, structure=disk(min_w / 2 * UP))
    holes = ndi.binary_fill_holes(D) & ~D                   # vein highlights inside a leaf
    lab, n = ndi.label(holes)
    if n:
        sizes = ndi.sum(holes, lab, range(1, n + 1))
        D |= np.isin(lab, 1 + np.flatnonzero(sizes < 150 * UP * UP))
    lab, n = ndi.label(D)                                   # drop specks
    if n:
        sizes = ndi.sum(D, lab, range(1, n + 1))
        D = np.isin(lab, 1 + np.flatnonzero(sizes > 60 * UP * UP))
    f = ndi.gaussian_filter(D.astype(float), sigma * UP)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 9.0)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] / UP for i in range(len(o) - 1)]
        if len(rings[0]) >= 4:
            out.append(Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0))
    return unary_union(out).simplify(0.12)


def load(path):
    return shape(json.load(open(path)))


if __name__ == "__main__":
    g = trace(sys.argv[1])
    json.dump(mapping(g), open(sys.argv[2], "w"))
    print("leaf pieces:", len(getattr(g, "geoms", [g])), "area px2:", round(g.area))
