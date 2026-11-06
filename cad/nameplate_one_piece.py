#!/usr/bin/env python3
"""One-piece automotive nameplate (wrench + crossed pistons + script name), parametric.

    .venv-cad/bin/python cad/nameplate_one_piece.py --name Rabea --width 300 --out cad/out/nameplate

Layers (printed front face up, back on the bed):
    z 0 .. BODY            frame (wrench + pistons) united with the name
    z BODY .. TOP-DEPTH    name only
    z TOP-DEPTH .. TOP     name with the LED channel cut from the FRONT (TOP = BODY + PROTRUSION)
A wire hole (d=3) goes from the back to the channel floor.
Every layer is a clean 2D polygon extruded with manifold3d, so the STL is watertight by construction.
The frame outline is private/third-party: cad/config/automotive_frame.wkt (git-ignored, copy by hand).
"""
import argparse, os, sys
import numpy as np
from shapely import wkt
from shapely.affinity import scale as shp_scale, translate
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import shapely, trimesh, manifold3d as mf
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME_BASE_W = 297.12          # width of the stored frame (nominal 300)
NAME_ZONE = dict(cx=148.0, cy=128.0, w=175.0, h=75.0)   # where the name sits, at 300 mm width


def text_polygon(name, font):
    tp = TextPath((0, 0), name, size=100, prop=FontProperties(fname=font))
    rings = [np.asarray(r) for r in tp.to_polygons(closed_only=True) if len(r) >= 3]
    # script fonts have overlapping contours: use winding direction (outer = same direction as the biggest ring),
    # union the outers, subtract the holes (even-odd would punch holes where strokes overlap)
    def signed(r):
        return 0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1])
    big = max(rings, key=lambda r: abs(signed(r)))
    sgn = np.sign(signed(big))
    outers = [Polygon(r).buffer(0) for r in rings if np.sign(signed(r)) == sgn]
    holes = [Polygon(r).buffer(0) for r in rings if np.sign(signed(r)) != sgn]
    return unary_union(outers).difference(unary_union(holes)).buffer(0)


def clean(g, close=0.1, eps=0.03):
    # close: fill slivers/gaps narrower than 2*close (they become pinch points); open: remove hair-thin necks
    g = g.buffer(close, join_style=2).buffer(-close, join_style=2)
    g = g.buffer(-eps, join_style=2).buffer(eps, join_style=2).buffer(0)
    # drop micro-segments (< 0.02 mm): they collapse in float32 STL and turn into pinch edges
    return g.simplify(0.02, preserve_topology=True).buffer(0)


def extrude(g, z0, z1):
    out = None
    for p in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        if p.is_empty or p.area < 0.05:
            continue
        rings = [np.array(p.exterior.coords)[:-1].tolist()] + [np.array(i.coords)[:-1].tolist() for i in p.interiors]
        e = mf.Manifold.extrude(mf.CrossSection(rings, mf.FillRule.EvenOdd), z1 - z0).translate([0, 0, z0])
        out = e if out is None else out + e
    return out


def build(a):
    s = a.width / 300.0
    frame = wkt.loads(open(os.path.join(HERE, "config", a.frame)).read())
    # name polygon, fitted into the name zone
    L = text_polygon(a.name, a.font)
    minx, miny, maxx, maxy = L.bounds
    k = min(NAME_ZONE["w"] * s / (maxx - minx), NAME_ZONE["h"] * s / (maxy - miny))
    L = shp_scale(L, k, k, origin=(minx, miny))
    minx, miny, maxx, maxy = L.bounds
    L = translate(L, NAME_ZONE["cx"] * s - (minx + maxx) / 2 + (a.dx * s), NAME_ZONE["cy"] * s - (miny + maxy) / 2)
    frame = shp_scale(frame, s, s, origin=(0, 0))
    # stroke width estimate (area / perimeter * 2) and the LED channel = centre band of the letters
    w = 2 * L.area / L.length
    inset = max((w - a.led_w) / 2, 0)
    G = L.buffer(-inset, join_style=1) if inset > 0 else L
    G = G.buffer(0)
    note = []
    if w < a.led_w + 2.4:
        note.append(f"WARNING: letter strokes are about {w:.1f} mm; the {a.led_w} mm channel leaves walls under 1.2 mm. Use a shorter name or a smaller channel.")
    # wire hole: leftmost point of the channel
    gp = max(G.geoms, key=lambda p: p.area) if isinstance(G, MultiPolygon) else G
    gl = min(G.geoms, key=lambda p: p.bounds[0]) if isinstance(G, MultiPolygon) else G
    c = gl.representative_point()
    hole = Point(c.x, c.y).buffer(1.5, 24)
    top = a.body + a.protrusion
    zg = top - a.led_d
    # all layers derive from the SAME cleaned shapes, so their walls coincide exactly (no slivers between layers)
    L = clean(L)
    Ra = clean(unary_union([frame, L]))
    Lb = L.intersection(Ra)
    G = G.intersection(Lb)
    snap = lambda g: shapely.set_precision(g.buffer(0), 0.005)
    layers = [
        (0, a.body, snap(Ra.difference(hole))),
        (a.body, zg, snap(Lb.difference(hole))),
        (zg, top, snap(Lb.difference(G))),
    ]
    return layers, note, dict(stroke=w, k=k, name_w=maxx - minx, name_h=maxy - miny)


def to_mesh(layers, fixes):
    res = None
    for z0, z1, g in layers:
        for (x, y, a, b) in fixes:
            if a < z1 - 1e-6 and b > z0 + 1e-6:
                g = g.union(Point(x, y).buffer(0.2))
        g = shapely.set_precision(g.buffer(0), 0.005)
        e = extrude(g, z0, z1)
        res = e if res is None else res + e
    m = res.to_mesh()
    r = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=True)
    r.merge_vertices()
    return r


def pinches(r):
    u, c = np.unique(r.edges_sorted, axis=0, return_counts=True)
    return u[c > 2], int((c == 1).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--width", type=float, default=300.0, help="overall width mm (<= 290 for coloured H2D jobs)")
    ap.add_argument("--led-w", type=float, default=3.0, help="LED strip channel width (3, 4 or 5)")
    ap.add_argument("--led-d", type=float, default=5.0, help="channel depth")
    ap.add_argument("--body", type=float, default=10.0)
    ap.add_argument("--protrusion", type=float, default=6.0)
    ap.add_argument("--dx", type=float, default=0.0, help="shift the name sideways (mm at 300 width)")
    ap.add_argument("--frame", default="automotive_frame.wkt", help="frame outline in cad/config: automotive_frame.wkt (one piece, keeps a banner outline of the old name) or automotive_frame_cut.wkt (clean, but the rods/wrench are cut, several loose bodies)")
    ap.add_argument("--font", default=os.path.join(HERE, "fonts", "Pacifico-Regular.ttf"))
    ap.add_argument("--out", required=True, help="output path without extension")
    a = ap.parse_args()
    if not a.name.isascii():
        sys.exit("English (Latin) names only for now: Pacifico has no Arabic glyphs.")
    layers, notes, info = build(a)
    fixes = []
    for _ in range(8):
        r = to_mesh(layers, fixes)
        e, op = pinches(r)
        if len(e) == 0 and op == 0:
            break
        for ed in e:
            v = r.vertices[ed]
            fixes.append((v[:, 0].mean(), v[:, 1].mean(), v[:, 2].min(), v[:, 2].max()))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    r.export(a.out + ".stl")
    print(f"{a.out}.stl  watertight={r.is_watertight} winding={r.is_winding_consistent} volume={r.volume:.0f} mm3 "
          f"bbox={np.round(r.extents, 1).tolist()} zmin={r.bounds[0][2]:.1f} pinch-fixes={len(fixes)}")
    print(f"name {info['name_w']:.0f} x {info['name_h']:.0f} mm, stroke ~{info['stroke']:.1f} mm")
    for n in notes:
        print(n)
    if r.extents[0] > 290:
        print("NOTE: wider than 290 mm: a multi-colour job will not fit the H2D with the prime tower.")


if __name__ == "__main__":
    main()
