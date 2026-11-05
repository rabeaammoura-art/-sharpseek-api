"""Personal keychain: big letter S with a little cartoon girl (wavy brown hair, white T-shirt with
pink bows, thumbs up) in front of it. Four colours, flat, for a multi-colour FDM print.

Structure (bottom to top):
  0 .. BASE   whole silhouette in the outline colour (dark brown)  -> no colour changes here
  BASE .. TOP colour regions, separated by dark-brown outline strokes
Output: out/<colour>.stl (shared coordinates), out/keychain.3mf, out/preview.png

Usage: python make_keychain.py [height_mm]
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent
OUT = HERE / "out"
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"

COLOURS = {  # name: (hex, Bambu PLA Basic colour it maps to)
    "brown": "#4A2C1A",
    "white": "#FFFFFF",
    "skin": "#F3C9A3",
    "pink": "#F27BA8",
}
STROKE = 0.45       # half-width of outline strokes (0.9 mm lines: two 0.45 mm extrusions)
BORDER = 1.6        # outer brown border around everything
BASE, TOP = 2.0, 3.2  # mm: brown backing, then 6 colour layers at 0.2 mm
DESIGN_H = 60.0     # the drawing below is laid out ~60 mm tall


def ell(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, 64), rx, ry)
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), cx, cy)


def arc_stroke(cx, cy, r, a0, a1, w):
    import math
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in [a0 + (a1 - a0) * i / 24 for i in range(25)]]
    from shapely.geometry import LineString
    return LineString(pts).buffer(w, cap_style=1)


def letter(ch, height, x, y):
    tp = TextPath((0, 0), ch, size=100, prop=FontProperties(fname=FONT))
    polys = [Polygon(p) for p in tp.to_polygons() if len(p) > 2]
    # even-odd: outer contours minus holes
    shape = Polygon()
    for p in sorted(polys, key=lambda q: -q.area):
        shape = shape.symmetric_difference(p.buffer(0))
    minx, miny, maxx, maxy = shape.bounds
    s = height / (maxy - miny)
    shape = affinity.scale(shape, s, s, origin=(minx, miny))
    return affinity.translate(shape, x - minx, y - miny).buffer(1.0)  # chunkier than Bold


def design():
    """Draw order list of (shape, colour, outlined). Later items cover earlier ones."""
    items = []
    S = letter("S", 50, 0, 8)
    items.append((S, "pink", True))

    # --- girl, head centre (37, 31) ---
    hx, hy = 37.0, 31.0
    back_hair = unary_union([ell(hx, hy + 1.5, 13.5, 13.5)] +
                            [ell(hx + dx, hy - 9 + dy, 4.2, 6.0) for dx, dy in
                             ((-11.5, 0), (-9, -4), (11.5, 0), (9, -4))])
    items.append((back_hair, "brown", True))

    body = Polygon([(22.5, 3.5), (51.5, 3.5), (50, 13.5), (44.5, 17.5), (29.5, 17.5), (24, 13.5)]).buffer(1.2)
    items.append((body, "white", True))
    for bx, by in ((31, 10.5), (37, 7.5), (43, 10.5)):  # pink bows on the shirt
        bow = unary_union([Polygon([(bx, by), (bx - 2.6, by + 1.5), (bx - 2.6, by - 1.5)]),
                           Polygon([(bx, by), (bx + 2.6, by + 1.5), (bx + 2.6, by - 1.5)]),
                           Point(bx, by).buffer(0.8)]).buffer(0.25)
        items.append((bow, "pink", False))

    items.append((box(hx - 2.6, 16.5, hx + 2.6, 22), "skin", True))           # neck
    items.append((ell(hx, hy, 9.6, 10.4), "skin", True))                       # face
    bangs = unary_union([ell(hx - 4, hy + 8.5, 8, 4.5, -12), ell(hx + 5, hy + 8, 7, 4.2, 15),
                         ell(hx, hy + 11, 10, 3.5)])
    items.append((bangs, "brown", False))

    for ex in (hx - 3.6, hx + 3.6):                                            # eyes
        items.append((ell(ex, hy - 0.5, 1.25, 1.65), "brown", False))
        items.append((Point(ex + 0.35, hy + 0.15).buffer(0.5, 24), "white", False))
        side = -1 if ex < hx else 1
        items.append((ell(ex + side * 2.0, hy - 3.6, 1.3, 0.95), "pink", False))  # cheek, outer side
    items.append((arc_stroke(hx, hy - 3.2, 2.0, 205, 335, STROKE), "brown", False))  # smile

    # thumbs-up hand, beside the face on her right (our left)
    fist = box(18.5, 17.5, 25.5, 23.5).buffer(1.4)
    thumb = box(20.2, 22.5, 22.8, 28.5).buffer(1.2)
    items.append((unary_union([fist, thumb]), "skin", True))
    for fy in (19.3, 21.5):                                                    # finger lines
        items.append((box(19.5, fy - STROKE, 24.5, fy + STROKE), "brown", False))
    return items


def colour_regions(items):
    silhouette = unary_union([s for s, _, _ in items])
    outline = silhouette.buffer(BORDER)
    # keyring tab on the top-left of the S
    minx, miny, maxx, maxy = outline.bounds
    tab_c = (minx + 9, maxy + 1.5)
    outline = unary_union([outline, Point(tab_c).buffer(5.2, 64)])
    hole = Point(tab_c).buffer(2.4, 64)

    visible, covered, strokes = {}, Polygon(), []
    for shape, col, outlined in reversed(items):
        v = shape.difference(covered)
        visible[col] = unary_union([visible.get(col, Polygon()), v])
        if outlined:  # outline only the part of this shape that is actually seen
            strokes.append(shape.boundary.buffer(STROKE).intersection(v.buffer(STROKE)))
        covered = covered.union(shape)
    strokes = unary_union(strokes)
    regions = {c: g.difference(strokes) for c, g in visible.items() if c != "brown"}
    regions = {c: g.buffer(-0.05).buffer(0.05) for c, g in regions.items()}  # drop slivers
    regions["brown_top"] = outline.difference(unary_union(list(regions.values())))
    return outline.difference(hole), {c: g.difference(hole) for c, g in regions.items()}


def to_solids(outline, regions, scale):
    from build123d import Compound, Face, Mesher, Wire, extrude, export_stl, Location

    def solid(geom, z0, z1):
        geom = affinity.scale(geom, scale, scale, origin=(0, 0))
        parts = []
        for poly in getattr(geom, "geoms", [geom]):
            if poly.is_empty or poly.area < 0.05:
                continue
            outer = Wire.make_polygon([(x, y, 0) for x, y in poly.exterior.coords[:-1]], close=True)
            holes = [Wire.make_polygon([(x, y, 0) for x, y in r.coords[:-1]], close=True) for r in poly.interiors]
            parts.append(extrude(Face(outer, holes), amount=z1 - z0).moved(Location((0, 0, z0))))
        return Compound(children=parts)

    bodies = {
        "brown": Compound(children=solid(outline, 0, BASE).solids() + solid(regions["brown_top"], BASE, TOP).solids()),
        **{c: solid(regions[c], BASE, TOP) for c in ("white", "skin", "pink")},
    }
    OUT.mkdir(exist_ok=True)
    mesher = Mesher()
    for name, b in bodies.items():
        export_stl(b, str(OUT / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.1)
        b.label = name
        mesher.add_shape(b, linear_deflection=0.01, angular_deflection=0.1)
    mesher.write(str(OUT / "keychain.3mf"))
    return bodies


def preview(outline, regions, scale, path):
    fig, ax = plt.subplots(figsize=(6, 6.6))
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    def draw(g, col):  # polygons with real holes
        g = affinity.scale(g, scale, scale, origin=(0, 0))
        for p in getattr(g, "geoms", [g]):
            if p.is_empty:
                continue
            rings = [list(p.exterior.coords)] + [list(r.coords) for r in p.interiors]
            verts = [v for r in rings for v in r]
            codes = [c for r in rings for c in [MPath.MOVETO] + [MPath.LINETO] * (len(r) - 2) + [MPath.CLOSEPOLY]]
            ax.add_patch(PathPatch(MPath(verts, codes), color=col, lw=0))
    for c in ("white", "skin", "pink"):
        draw(regions[c], COLOURS[c])
    draw(regions["brown_top"], COLOURS["brown"])   # on top: outlines, eyes, mouth, hair
    minx, miny, maxx, maxy = affinity.scale(outline, scale, scale, origin=(0, 0)).bounds
    ax.set_title(f"{maxx - minx:.0f} x {maxy - miny:.0f} mm, {TOP:.1f} mm thick")
    ax.set_xlim(minx - 2, maxx + 2); ax.set_ylim(miny - 2, maxy + 2)
    ax.set_aspect("equal"); ax.axis("off"); fig.patch.set_facecolor("#ECECEC")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    height = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    outline, regions = colour_regions(design())
    scale = height / (outline.bounds[3] - outline.bounds[1])
    preview(outline, regions, scale, OUT.mkdir(exist_ok=True) or OUT / "preview.png")
    bodies = to_solids(outline, regions, scale)
    minx, miny, maxx, maxy = affinity.scale(outline, scale, scale, origin=(0, 0)).bounds
    print(f"size {maxx - minx:.1f} x {maxy - miny:.1f} x {TOP} mm; volumes cm3:",
          {k: round(v.volume / 1000, 2) for k, v in bodies.items()})
