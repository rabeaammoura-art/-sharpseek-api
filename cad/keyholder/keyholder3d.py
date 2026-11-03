"""Car-upholstery key holder: 3D from the approved flat drawing (flat_preview.load_layers).

ONE printed piece, back on the bed (Z = 0 is the wall side), no supports, no loose parts.
Colours (3): black (structure), red (stitching, strip, wheel mark), white (lettering, chrome, strip stitching).
Usage: python keyholder3d.py <out_dir> [--trace trace.json] [--wheel wheel_in.json]
All heights are parameters below (mm).
"""
import argparse, math, sys, os
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely import affinity
from build123d import Solid, Face, Wire, Vector, Pos, Compound, export_stl, export_step, Cone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flat_preview as F

# ------------------------------------------------------------------ parameters (mm)
W_MM = 300.0                    # overall width (parametric: everything scales from the picture width)
H_BASE = 4.0                    # back plate thickness
H_PANEL = 5.5                   # dark panel behind the lettering
H_BAND = 5.0                    # arch band
H_WHEEL_RING = 8.0              # steering wheel rim
H_WHEEL_PAD = 9.0               # hub pad / spoke bodies
H_SEAT_FILL = 7.0
H_SEAT_SIDES = 12.0             # side bolsters
H_SEAT_CENTRE = 9.5             # plain upper centre panel
H_SEAT_DIAMOND = 10.0           # diamond panel
H_SEAT_TOP = 14.0               # cushion + headrest
H_STRIP = 9.0                   # red leather strip (top)
T_STITCH = 0.8                  # raised stitches (red / white)
T_TEXT = 3.5                    # lettering on the panel
T_SWOOSH = 1.6
T_MACHINE = 3.0
T_TRIM = 1.2                    # chrome trim of the wheel
HOOK_OUT = 28.0                 # hook stem length out of the plate surface
HOOK_W = 12.0                   # hook width (x)
HOOK_T = 9.0                    # stem thickness (y)
HOOK_LIP = 6.0                  # upturned lip
HOOK_BOSS_R = 11.0
HOOK_BOSS_H = 5.0
SCREW_THROUGH = 4.2
SCREW_HEAD = 8.5

Y_BOTTOM_PX = 728.0             # bottom edge of the plate in the picture
X_LEFT_PX = 74.0
S = W_MM / (1484.0 - 74.0)      # mm per picture px


def to_mm(g):
    """picture px (y down) -> mm (y up, plate bottom = 0, left = 0)."""
    g = affinity.translate(g, -X_LEFT_PX, -Y_BOTTOM_PX)
    g = affinity.scale(g, S, -S, origin=(0, 0))
    return g


def parts_of(g):
    if g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    if not hasattr(g, "geoms"):
        return []                      # lines / points from intersections
    return [p for gg in g.geoms for p in parts_of(gg)]


def face(poly):
    return Face(Wire.make_polygon([(x, y, 0) for x, y in poly.exterior.coords[:-1]]),
                [Wire.make_polygon([(x, y, 0) for x, y in i.coords[:-1]]) for i in poly.interiors])


def prism(g, z0, z1):
    out = []
    for p in parts_of(g):
        if p.area < 0.15 or z1 - z0 < 0.05:
            continue
        p = p.simplify(0.02)
        out.append(Pos(0, 0, z0) * Solid.extrude(face(p), Vector(0, 0, z1 - z0)))
    return out


ROUND = {"base": 0.8, "wheel_ring": 1.4, "wheel_pad": 1.2, "seat_left": 2.2, "seat_right": 2.2, "seat_centre": 1.2,
         "seat_cush": 2.2, "seat_head": 2.2, "strip": 1.5}      # quarter-round top-edge radius per piece (mm); 0 = sharp
SLAB = 0.4                                                          # slab thickness of the rounded edge (2 printed layers)
CELL_H = 1.2                                                        # diamond cells stand this much above the diamond panel
CELL_R = 0.9
GROOVE = 0.95                                                       # half width of the quilting groove (mm)


def shaped(g, z0, z1, R):
    """Prism z0..z1 whose top edge is a quarter round of radius R (stacked slabs, each inset by the circle profile)."""
    R = min(R, z1 - z0)
    if R < 0.3:
        return prism(g, z0, z1)
    out = prism(g, z0, z1 - R)
    n = max(int(math.ceil(R / SLAB)), 1)
    for k in range(n):
        za, zb = (z1 - R) + k * R / n, (z1 - R) + (k + 1) * R / n
        t = ((za + zb) / 2) - (z1 - R)
        d = R - math.sqrt(max(R * R - t * t, 0.0))
        gg = g.buffer(-d)
        out += prism(gg, za, zb)
    return out


def build(trace, wheel):
    L = F.load_layers(trace, wheel)
    M = {k: (to_mm(v) if hasattr(v, "geom_type") else v) for k, v in L.items()}
    base = M["base"]

    # --- structure in painter's order (later covers earlier): (name, polygon, top height)
    seat_fill = M["seat_fill"].intersection(base)
    structure = [
        ("base", base, H_BASE),
        ("band", M["band"].intersection(base), H_BAND),
        ("panel", M["panel"].intersection(base), H_PANEL),
        ("wheel_ring", M["wheel_ring"].intersection(base), H_WHEEL_RING),
        ("wheel_pad", M["wheel_pad"], H_WHEEL_PAD),
        ("seat_fill", seat_fill, H_SEAT_FILL),
        ("seat_left", M["seat_left"].intersection(base), H_SEAT_SIDES),
        ("seat_right", M["seat_right"].intersection(base), H_SEAT_SIDES),
        ("seat_centre", M["seat_centre"].intersection(base), H_SEAT_CENTRE),
        ("seat_diamond", M["seat_diamond"].intersection(base), H_SEAT_DIAMOND),
        ("seat_cush", M["seat_cush"].intersection(base), H_SEAT_TOP),
        ("seat_head", M["seat_head"].intersection(base), H_SEAT_TOP),
        ("strip", M["strip"].intersection(base), H_STRIP),      # red strip: black only up to H_BASE below it
    ]
    # level regions: region_k = poly_k minus everything painted later
    regions, covered = [], Polygon()
    for name, poly, h in reversed(structure):
        r = poly.difference(covered) if not covered.is_empty else poly
        regions.append((name, r, h))
        covered = covered.union(poly)
    regions = [(n, r.buffer(0), h) for n, r, h in regions if not r.is_empty]

    black, red, white = [], [], []
    for name, r, h in regions:
        rb = r.buffer(0.02)            # tiny overlap with the neighbour region: no pinch points / non-manifold edges after the fuse
        if name == "strip":
            black += prism(rb, 0, H_BASE)
            red += shaped(r, H_BASE, H_STRIP, ROUND["strip"])
        else:
            black += shaped(rb, 0, h, ROUND.get(name, 0.0))

    def level_regions():
        return [(n, r, (H_STRIP if n == "strip" else h)) for n, r, h in regions]

    def decor(poly, t, bucket):
        for name, r, h in level_regions():
            rr = ROUND.get(name, 0.0)
            piece = poly.intersection(r.buffer(-rr) if rr > 0 else r)          # decoration only on the flat top, not on the rounded edge
            if not piece.is_empty:
                bucket += prism(piece, h, h + t)

    # quilted diamond cells: real relief between the stitched grooves
    dia = [r for n, r, h in regions if n == "seat_diamond"]
    if dia and "seat_lattice_lines" in M:
        lines = M["seat_lattice_lines"].buffer(GROOVE)
        cells = dia[0].buffer(-0.8).difference(lines)
        for c in parts_of(cells):
            if c.area > 3.0:
                black += shaped(c.buffer(0.02), H_SEAT_DIAMOND, H_SEAT_DIAMOND + CELL_H, CELL_R)

    # the seat is in front of the wheel: wheel decoration must not run over it
    seat_cover = unary_union([M[k] for k in ("seat_fill", "seat_left", "seat_right", "seat_centre", "seat_diamond", "seat_cush", "seat_head")])
    M["wheel_stitch"] = M["wheel_stitch"].difference(seat_cover)
    M["wheel_mark"] = M["wheel_mark"].difference(seat_cover)
    M["wheel_hub"] = M["wheel_hub"].difference(seat_cover)
    # red decor
    for key in ("wheel_mark", "wheel_stitch", "seat_stitch", "seat_seam_stitch", "seat_lattice"):
        decor(M[key].intersection(base), T_STITCH, red)
    # white decor
    decor(M["text"], T_TEXT, white)
    decor(M["swoosh"], T_SWOOSH, white)
    decor(M["machine"], T_MACHINE, white)
    decor(M["wheel_hub"].intersection(base), T_TRIM, white)
    decor(M["strip_stitch"].intersection(M["strip"]), T_STITCH, white)

    # --- seam groove: cut a narrow channel in the seat (black stays, only a groove 0.6 deep) -> skipped (not needed for the print)

    # --- hooks (black): boss + stem (J profile in the y-z plane, 45 deg lip underside)
    hooks = []
    xs = [(x - X_LEFT_PX) * S for x in F.build()["hooks_x"]]
    yc = (Y_BOTTOM_PX - 668.0) * S
    z0 = H_BASE
    for cx in xs:
        prof = [(yc - HOOK_T / 2, z0 - 0.5), (yc + HOOK_T / 2, z0 - 0.5), (yc + HOOK_T / 2, z0 + HOOK_OUT - HOOK_LIP - 0.01),
                (yc + HOOK_T / 2 + HOOK_LIP * 0.75, z0 + HOOK_OUT - 1.5), (yc + HOOK_T / 2 + HOOK_LIP * 0.75, z0 + HOOK_OUT),
                (yc - HOOK_T / 2, z0 + HOOK_OUT)]
        f = Face(Wire.make_polygon([Vector(cx - HOOK_W / 2, y, z) for y, z in prof]))
        hooks.append(Solid.extrude(f, Vector(HOOK_W, 0, 0)))
        hooks += prism(Point(cx, yc).buffer(HOOK_BOSS_R, 48), z0 - 0.5, z0 + HOOK_BOSS_H)
    black += hooks

    # --- wall screw holes (countersunk), cut from the black
    screws = [((x - X_LEFT_PX) * S, (Y_BOTTOM_PX - y) * S) for x, y in F.build()["screws"]]
    return black, red, white, screws, L


def fuse(solids):
    solids = [s for s in solids if s is not None]
    return solids[0].fuse(*solids[1:]).clean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--trace"); ap.add_argument("--wheel")
    a = ap.parse_args()
    out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True)
    black, red, white, screws, L = build(a.trace, a.wheel)
    res = {}
    for name, sol in (("black", black), ("red", red), ("white", white)):
        comp = Compound(sol)
        if name == "black":
            comp = fuse(sol)                       # ONE fused black solid (plate + seat + hooks)
            cuts = []
            for (sx, sy) in screws:
                cuts.append(Pos(sx, sy, -0.1) * Solid.make_cylinder(SCREW_THROUGH / 2, 40))
                cuts.append(Pos(sx, sy, H_BASE - (SCREW_HEAD - SCREW_THROUGH) / 2) * Solid.make_cone(SCREW_THROUGH / 2, SCREW_HEAD / 2, (SCREW_HEAD - SCREW_THROUGH) / 2 + 0.01))
            comp = comp - Compound(cuts)
        res[name] = comp
        export_stl(comp, str(out / "stl" / f"keyholder__{name}.stl"))
        bb = comp.bounding_box()
        print(name, len(sol), "solids", [round(v, 1) for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)])
    export_step(Compound(list(res.values())), str(out / "keyholder.step"))


if __name__ == "__main__":
    main()
