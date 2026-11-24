"""Procedural Minnie-style artwork (personal gift, private theme): flat shapes drawn in code, written to motifs/minnie.json.

    python minnie_art.py

Layers per motif: black (the sticker outline + head + ears, = base slab colour), red (bow, hearts), white (face, polka dots), yellow (stars).
Units: mm, y up, bottom of the art at y = 0 (the name pill is added below by the generator).
"""
import json
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).parent


def ell(cx, cy, rx, ry, rot=0.0):
    return affinity.rotate(affinity.scale(Point(cx, cy).buffer(1, 48), rx, ry), rot, origin=(cx, cy))


def star(cx, cy, r, ri=None, rot=90.0):
    ri = ri or r * 0.48
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else ri
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return Polygon(pts).buffer(r * 0.12, join_style=1).buffer(-r * 0.12, join_style=1)


def heart(cx, cy, w):
    pts = []
    for i in range(121):
        t = math.radians(i * 3)
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x, y))
    g = Polygon(pts)
    g = affinity.scale(g, w / 32.0, w / 32.0)
    b = g.bounds
    return affinity.translate(g, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)


def lobe(cx, cy, s, sign):
    """One triangular bow lobe (sign -1 = left, +1 = right), rounded corners."""
    pts = [(0, 0), (sign * 17, 8.5), (sign * 18.5, -8.0)]
    g = Polygon([(cx + x * s, cy + y * s) for x, y in pts])
    return g.buffer(2.2 * s, join_style=1).buffer(-0.6 * s, join_style=1)


def bow(cx, cy, s=1.0, dots=True):
    """Red polka-dot bow: two triangular lobes + knot.  Returns (red, white_dots)."""
    red = unary_union([lobe(cx, cy, s, -1), lobe(cx, cy, s, 1), Point(cx, cy).buffer(4.2 * s, 48)])
    d = [(-9.0, 0.5, 1.9), (-14.5, 0.5, 2.2), (9.0, 0.5, 1.9), (14.5, 0.5, 2.2)]
    white = unary_union([Point(cx + x * s, cy + y * s).buffer(r * s, 24) for x, y, r in d]) if dots else Polygon()
    return red, white.intersection(red.buffer(-0.9 * s))


def head(cx, cy, s=1.0, with_bow=True):
    """Minnie head: black head + ears, white face with eyes/nose cut out, red polka-dot bow on top.  (black, red, white)"""
    h = Point(cx, cy).buffer(20.5 * s, 64)
    ears = [Point(cx - 17.5 * s, cy + 15.5 * s).buffer(12.5 * s, 48), Point(cx + 17.5 * s, cy + 15.5 * s).buffer(12.5 * s, 48)]
    black = unary_union([h] + ears)
    face = ell(cx, cy - 4.2 * s, 14.5 * s, 12.8 * s)
    eyes = unary_union([ell(cx - 5.2 * s, cy + 0.2 * s, 1.9 * s, 3.3 * s), ell(cx + 5.2 * s, cy + 0.2 * s, 1.9 * s, 3.3 * s)])
    nose = ell(cx, cy - 6.0 * s, 3.8 * s, 2.7 * s)
    white = face.difference(unary_union([eyes, nose]))
    red, wd = Polygon(), Polygon()
    if with_bow:
        red, wd = bow(cx, cy + 20.5 * s, s * 0.95)
    return black, red, unary_union([white, wd]) if with_bow else white


def to_json(layers, tab_x=None):
    out = {}
    allg = unary_union([g for g in layers.values() if not g.is_empty])
    minx, miny, maxx, maxy = allg.bounds
    for c, g in layers.items():
        g = affinity.translate(g, -minx, -miny)
        polys = [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon" and not p.is_empty]
        out[c] = [{"ext": [[round(x, 3), round(y, 3)] for x, y in p.exterior.coords], "holes": [[[round(x, 3), round(y, 3)] for x, y in r.coords] for r in p.interiors]} for p in polys]
    return {"width_mm": round(maxx - minx, 3), "height_mm": round(maxy - miny, 3), "tab_x_mm": None if tab_x is None else round(tab_x - minx, 3), "layers": out}


def outline(shapes, w):
    return unary_union(shapes).buffer(w, join_style=1)


def build_head_motif(s, tab=True, bow_dots=True, side_stars=True):
    black, red, white = head(0, 0, s)
    stars = unary_union([star(-27 * s, -12 * s, 5.2 * s), star(27 * s, -12 * s, 5.2 * s)]) if side_stars else Polygon()
    shapes = [black, red, stars]
    out = outline(shapes, 1.8 * s)
    layers = {"black": unary_union([out, black]), "red": red, "white": white}
    if side_stars:
        layers["yellow"] = stars
    return to_json(layers, tab_x=0.0 if tab else None)


def main():
    data = {}
    data["tag"] = build_head_motif(1.0)
    data["bottle"] = build_head_motif(0.8)
    # pencil: bow on the left, heart + star on the right
    red, wd = bow(0, 0, 0.6)
    layers = {"black": outline([red], 1.0), "red": red, "white": wd}
    data["pencil_l"] = to_json(layers)
    hr, st = heart(0, 0, 8.5), star(11.5, 0.3, 4.2)
    layers = {"black": outline([hr, st], 1.0), "red": hr, "yellow": st}
    data["pencil_r"] = to_json(layers)
    # ruler: head on the left, big bow + star on the right
    data["ruler_l"] = build_head_motif(0.6, tab=False, side_stars=False)
    red, wd = bow(0, 0, 1.15)
    st = star(21, 5.5, 4.4)
    layers = {"black": outline([red, st], 1.0), "red": red, "white": wd, "yellow": st}
    data["ruler_r"] = to_json(layers)
    (HERE / "motifs" / "minnie.json").write_text(json.dumps(data, separators=(",", ":")))
    for k, v in data.items():
        print(k, v["width_mm"], "x", v["height_mm"], {c: len(p) for c, p in v["layers"].items()})


if __name__ == "__main__":
    main()
