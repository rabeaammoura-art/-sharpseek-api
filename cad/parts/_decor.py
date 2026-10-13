"""Decoration for the Mercedes tray, in the spirit of the carved wooden folding basket:

* three tomoe (comma / paisley) swirls engraved across the closed top: ring tops and frame top,
* an engraved border line around the flange and along the handle,
* triangular teeth around the handle ring, the fixed outer segment and the base edge.

Everything is a cutting tool (solid) built from 2D shapely geometry. The same tools are exported
as STEP for the Fusion 360 script, so both pipelines cut identical geometry. Nothing here touches
the lips, gaps, hinge pins, the leg feet or the base pockets.
"""
from functools import lru_cache

import numpy as np
from build123d import Compound, Face, Part, Wire, extrude
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

DEPTH = 0.4      # engraving depth: 2 layers at 0.2 mm
STROKE = 1.0     # engraved line width (>= 2.5 nozzle widths, reads clearly)
INNER = 4.0      # second outline inside each tomoe
TOOTH = 1.5      # radial depth of the edge teeth
TOOTH_PITCH = 6.0  # mm along the edge


def tomoe(R, head_deg, span=100.0, rh_frac=0.24):
    """Comma shape: head disk tangent to the circle of radius R at head_deg, tail running
    counter-clockwise along that circle and tapering to a point span degrees later."""
    rh = rh_frac * R
    u = lambda a: np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])  # noqa: E731
    head = Point(*((R - rh) * u(head_deg))).buffer(rh, 128)
    tip = head_deg + span
    e = 2 * rh / (1 - np.cos(np.radians(span)))
    crescent = Point(0, 0).buffer(R, 512).difference(Point(*(e * u(tip))).buffer(R - e, 512))
    wedge = Polygon([(0, 0)] + [tuple(2 * R * u(a)) for a in np.linspace(head_deg, tip, 60)])
    return unary_union([head, crescent.intersection(wedge)]).buffer(2.0).buffer(-2.0)  # smooth the joint


def _polys(g):
    return [] if g.is_empty else list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def outline(poly, width=STROKE):
    lines = [r.buffer(width / 2) for p in _polys(poly) for r in [p.exterior, *p.interiors]]
    return unary_union(lines)


def pattern_2d(p):
    """Carving: each tomoe recessed 0.4 mm with a raised line left inside it (relief look),
    plus an engraved circle around the swirl."""
    R = p.r_sector - 6.0
    shapes = [tomoe(R, h) for h in p.compartment_angles]
    recess = [s.difference(outline(s.buffer(-INNER), width=1.6)) for s in shapes]
    ring = Point(0, 0).buffer(R + 3.0, 512).exterior.buffer(STROKE / 2)
    return unary_union(recess + [ring])


def arc_band(r, a0, a1, width=STROKE):
    pts = [(r * np.cos(np.radians(a)), r * np.sin(np.radians(a))) for a in np.linspace(a0, a1, 400)]
    from shapely.geometry import LineString
    return LineString(pts).buffer(width / 2, cap_style="round")


def teeth(r, a0, a1, depth=TOOTH, pitch=TOOTH_PITCH):
    """Triangular notches cut into an outer edge of radius r between angles a0..a1."""
    n = max(1, int(np.radians(a1 - a0) * r / pitch))
    da = (a1 - a0) / n
    tris = []
    for i in range(n):
        a, b, m = np.radians(a0 + i * da), np.radians(a0 + (i + 1) * da), np.radians(a0 + (i + 0.5) * da)
        ro = r + 1.0
        tris.append(Polygon([(ro * np.cos(a), ro * np.sin(a)), (ro * np.cos(b), ro * np.sin(b)),
                             ((r - depth) * np.cos(m), (r - depth) * np.sin(m))]))
    # leave a flat land between notches: shrink each triangle slightly sideways
    return unary_union([t.buffer(-0.15) for t in tris])


def as_polys(geom):
    """Shapely geometry -> [(outer [(x, y)...], [hole, ...])], simplified to 0.03 mm (far below
    print resolution) to keep the booleans fast. This is the exact data both pipelines extrude."""
    out = []
    for poly in _polys(geom.buffer(0).simplify(0.03, preserve_topology=True)):
        ring = lambda r: [(round(x, 4), round(y, 4)) for x, y in list(r.coords)[:-1]]  # noqa: E731
        out.append((ring(poly.exterior), [ring(h) for h in poly.interiors]))
    return out


@lru_cache(maxsize=None)
def specs(p):
    """Every decoration cut: (target, z0, z1, polygons). target: rings | frame | handle | base."""
    from _mercedes import sector_points
    clip = unary_union([Polygon(_sector_poly(sector_points, p, p.divider_half + p.lip, th))
                        for th in p.compartment_angles])
    pat = pattern_2d(p)
    g = p.leg_deg + p.leg_gap_deg
    rm = (p.handle_r0 + p.handle_r1) / 2
    zones = handle_zones(p)
    top = p.frame_h - DEPTH
    return (
        # pattern 0.4 mm into the ring tops, only inside the compartment openings
        ("rings", p.ring_h - DEPTH, p.ring_h + 1.0, as_polys(pat.intersection(clip))),
        # pattern continued over the frame top + flange border line
        ("frame", top, p.frame_h + 1.0, as_polys(unary_union(
            [pat, Point(0, 0).buffer((p.r_sector + p.r_flange) / 2, 512).exterior.buffer(STROKE / 2)]))),
        # teeth on the fixed outer segment
        ("frame", -1.0, p.frame_h + 1.0, as_polys(teeth(p.handle_r1, 180 + g + 4, 360 - g - 4))),
        # line along the handle, teeth on its outer edge (away from hinges and feet)
        ("handle", top, p.frame_h + 1.0, as_polys(unary_union([arc_band(rm, a0, a1) for a0, a1 in zones]))),
        ("handle", -1.0, p.frame_h + 1.0, as_polys(unary_union([teeth(p.handle_r1, a0, a1) for a0, a1 in zones]))),
        # teeth around the base edge
        ("base", -p.base_t - 1.0, 1.0, as_polys(teeth(p.base_d / 2, 0, 360, depth=2.0, pitch=8.0))),
    )


def to_part(polys, z0, z1) -> Part:
    solids = []
    for outer, holes in polys:
        ow = Wire.make_polygon([(x, y, z0) for x, y in outer], close=True)
        hw = [Wire.make_polygon([(x, y, z0) for x, y in h], close=True) for h in holes]
        solids += extrude(Face(ow, hw), z1 - z0, dir=(0, 0, 1)).solids()  # winding-independent
    return solids


@lru_cache(maxsize=None)
def tool(p, target) -> Part:
    return Compound([s for t, z0, z1, polys in specs(p) if t == target for s in to_part(polys, z0, z1)])


def rings_tool(p):
    return tool(p, "rings")


def frame_tool(p):
    return tool(p, "frame")


def handle_tool(p):
    return tool(p, "handle")


def base_tool(p):
    return tool(p, "base")


def export_json(p, path):
    """decor.json for the Fusion script: identical polygons, extruded the same way."""
    import json
    data = [{"target": t, "z0": z0, "z1": z1, "polys": [{"outer": o, "holes": h} for o, h in polys]}
            for t, z0, z1, polys in specs(p)]
    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))


def handle_zones(p):
    """Angle ranges of the handle that may be decorated: away from the hinges and the leg feet."""
    keep_end, keep_hinge = 10.0, 8.0
    return [(-p.leg_deg + keep_end, -keep_hinge), (keep_hinge, 180 - keep_hinge),
            (180 + keep_hinge, 180 + p.leg_deg - keep_end)]


def _sector_poly(sector_points, p, d, th, n=200):
    apex, a1, mid, a2 = sector_points(p, d, th)
    r = np.hypot(*mid)
    t0, t1 = np.degrees(np.arctan2(a1[1], a1[0])), np.degrees(np.arctan2(a2[1], a2[0]))
    if t1 < t0:
        t1 += 360
    return [apex] + [(r * np.cos(np.radians(t)), r * np.sin(np.radians(t))) for t in np.linspace(t0, t1, n)]
