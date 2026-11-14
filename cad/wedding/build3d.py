"""Wedding heart plaque in 3D (backlit, glow_cap method) + heart box + removable printed kickstand.

Usage:  python cad/wedding/build3d.py <flat_picture.png> <out_dir> [--size 280] [--name1 .. --name2 .. --date ..]

Plaque (4 slots): base (opaque, 2.4 mm, openings under the cream field), cream (translucent, 1.2 mm, the glowing field),
gold (opaque, 1.8 mm: frame, hearts, lines, rings), navy (opaque, 1.8 mm: couple, veil, names, date, calendar).
Box: follows the heart (tip cut flat so the heart can stand), 14 mm deep, back panel 1 mm (LED strip on it), 12 plate tabs,
two nut posts (the plaque has two planted hex nuts in the frame, screws from the back), USB-C slot in the flat bottom wall,
dovetail pocket for the printed kickstand (cad/kickstand.py, hinge height computed to fit inside the heart).
All parts are checked watertight; nothing here is print-tested.
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import flat_v3  # noqa: E402
import kickstand as ks  # noqa: E402
import newborn_plaque as n  # noqa: E402
from threemf import build_project_settings, write_bambu_3mf  # noqa: E402

BASE_H, CAP, RAISE = 2.4, 1.2, 1.8
FLAT_W = 38.0           # width of the flat foot where the tip is cut


def polys(g):
    return [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if not p.is_empty and p.geom_type == "Polygon"]


def minpoly(g, a):
    return n.only_polygons(unary_union([p for p in polys(g) if p.area >= a]))


def width_at(poly, y):
    row = poly.intersection(LineString([(-1e3, y), (1e3, y)]))
    return row.bounds[2] - row.bounds[0]


def flat_y(outer):
    """y where the heart is FLAT_W wide (cut here so it can stand)."""
    lo, hi = outer.bounds[1], outer.bounds[1] + 60
    for _ in range(40):
        mid = (lo + hi) / 2
        if width_at(outer, mid) < FLAT_W:
            lo = mid
        else:
            hi = mid
    return hi


def fix_points_heart(outer, inner, y=48.0):
    """Two nut spots in the frame, left and right, where the frame is vertical (widest part of the heart)."""
    pts = []
    for sx in (-1, 1):
        row_o = outer.intersection(LineString([(0, y), (sx * 1e3, y)]))
        row_i = inner.intersection(LineString([(0, y), (sx * 1e3, y)]))
        xo, xi = abs(row_o.bounds[0] if sx < 0 else row_o.bounds[2]), abs(row_i.bounds[0] if sx < 0 else row_i.bounds[2])
        pts.append((sx * (xo + xi) / 2, y, xo - xi))
    return pts


def build_plaque(L, y_cut):
    half = box(-1e3, y_cut, 1e3, 1e3)
    outer = L["outer"].intersection(half)
    inner = L["inner"].intersection(box(-1e3, y_cut + 9.0, 1e3, 1e3))          # keep a 9 mm frame along the flat foot too
    gold = n.only_polygons(unary_union([L["gold"].intersection(half), outer.difference(inner)]))
    navy = n.only_polygons(L["navy"].intersection(half))
    field = n.only_polygons(inner.difference(unary_union([gold, navy])))
    field = minpoly(field, 2.0)
    ovl = n.CAP_OVERLAP
    holes = []
    for p in polys(field.buffer(-ovl, join_style=1)):
        if p.area > 0.3:
            holes.append(n.add_ribs(p, 1.0))
    fp = fix_points_heart(outer, inner)
    pockets = unary_union([n.hexagon(x, y, n.NUTS["M3"]["af"] + 0.3) for x, y, _ in fp])
    base = n.only_polygons(outer.difference(unary_union(holes)).difference(pockets))
    base = n.only_polygons(base.buffer(0.2, join_style=1).buffer(-0.2, join_style=1).simplify(0.02))   # closing: removes vertex-touching edges
    base = minpoly(base, 1.5)
    base = unary_union([Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area > 0.5]) for p in polys(base)])
    layers = {"base": [(base, 0, BASE_H)], "cream": [(field, BASE_H, BASE_H + CAP)],
              "gold": [(gold, BASE_H, BASE_H + RAISE)], "navy": [(navy, BASE_H, BASE_H + RAISE)]}
    return layers, outer, fp, base, holes


def make_heart_box(outer, fp, size=280):
    depth, back, plate_t, wall = 14.0, 1.0, 2.4, n.BOX_WALL
    ledge_top = depth - plate_t
    cav = outer.buffer(0.2, join_style=1)
    boxo = cav.buffer(wall, join_style=1)
    ring = boxo.difference(cav)
    bx0, by0, bx1, by1 = boxo.bounds
    cx0, cy0, cx1, cy1 = cav.bounds
    slot = box(-5, by0 - 1, 5, cy0 + 1)                                     # USB-C slot through the flat bottom wall
    # plate tabs: 12 along the cavity boundary, 2.5 mm in, 30 mm long
    band = cav.difference(cav.buffer(-2.5, join_style=1)).buffer(0.3, join_style=1).intersection(boxo)   # overlaps the wall: no touching edges
    per = cav.exterior
    tabs = unary_union([band.intersection(Point(per.interpolate(d).coords[0]).buffer(15)) for d in np.linspace(0, per.length, 13)[:-1]])
    nut = n.NUTS["M3"]
    posts = unary_union([Point(x, y).buffer(nut["post"] / 2, 24) for x, y, _ in fp]).intersection(cav)
    holes = unary_union([Point(x, y).buffer(nut["hole"] / 2, 24) for x, y, _ in fp])
    # kickstand hinge height: as high as the pocket (pad) still sits inside the heart, max 0.82 of the box height
    y_bot, H = by0, by1 - by0
    best = None
    for fr in np.arange(0.82, 0.45, -0.01):
        ks.OVERRIDE = {"y_axis": y_bot + fr * H, "y_bot": y_bot}
        kp = ks.pocket_shapes(size)
        if kp["pad"].difference(cav.buffer(-1.0)).is_empty:
            best = fr
            break
    assert best is not None, "kickstand pocket does not fit"
    kp = ks.pocket_shapes(size)
    z0, z1 = 4.0, 8.5
    cuts = sorted({0, back, z0, z1, ledge_top - 2.0, ledge_top, depth} | set(kp["z"]))
    meshes = []
    for a, b in zip(cuts, cuts[1:]):
        mid = (a + b) / 2
        g = boxo if mid < back else (ring.difference(slot) if z0 < mid < z1 else ring)
        if ledge_top - 2.0 < mid < ledge_top:
            g = g.union(tabs)
        if back <= mid < ledge_top:
            g = g.union(posts)
        if mid < ledge_top:
            g = g.difference(holes)
        if back <= mid < kp["z"][2]:
            g = g.union(kp["pad"].intersection(boxo))
        if mid < kp["z"][0]:
            g = g.difference(kp["slot"])
        elif mid < kp["z"][1]:
            g = g.difference(kp["chamber"])
        g = g.buffer(0.15, join_style=1).buffer(-0.15, join_style=1)      # closing: no vertex-touching edges
        meshes += n.extrude(n.only_polygons(g), a, b)
    mesh = n.merge_solids(meshes)
    return mesh, {"outer": (bx1 - bx0, by1 - by0), "depth": depth, "hinge_frac": best, "y_axis": y_bot + best * H, "y_bot": y_bot,
                  "foot": width_at(cav, cy0 + 3.0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("out")
    ap.add_argument("--size", type=float, default=280)
    ap.add_argument("--name1", default="أحمد")
    ap.add_argument("--name2", default="سارة")
    ap.add_argument("--date", default="15/06/2026")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    L = flat_v3.build(a.ref, a.size, 9.0, a.name1, a.name2, a.date)
    y_cut = flat_y(L["outer"])
    layers, outer_c, fp, base, holes = build_plaque(L, y_cut)
    print(f"plaque {outer_c.bounds[2] - outer_c.bounds[0]:.1f} x {outer_c.bounds[3] - outer_c.bounds[1]:.1f} mm, flat foot at y={y_cut:.1f}, "
          f"nut spots {[(round(x, 1), round(y, 1), round(w, 1)) for x, y, w in fp]} (x, y, frame width)")
    parts = []
    for slot, role in enumerate(("base", "cream", "gold", "navy"), start=1):
        m = n.to_mesh(layers[role])
        m.export(out / f"wedding_{role}.stl")
        parts.append((role, m, slot))
        print(role, len(m.faces), "faces, vol", round(m.volume), "watertight", m.is_watertight, "bounds", m.bounds.round(1).tolist())
    bl = polys(base)
    print("base pieces", len(bl), "smallest", sorted(round(p.area, 1) for p in bl)[:6])
    petg = (HERE.parent / "config" / "bambu_project_4fil_petg.config").read_bytes()
    cols = ["#F5F5F5", "#FFF1C9", "#D9A21B", "#161D3C"]
    px = 144.0
    tower = (round(px + 140 + 3, 1), 120, 14)
    write_bambu_3mf(out / "wedding_plaque_280.3mf", parts, center=(px, 160.0), name="wedding_plaque_280",
                    project_settings=build_project_settings(petg, cols, tower))

    box_mesh, info = make_heart_box(outer_c, fp, a.size)
    box_mesh.export(out / "wedding_box.stl")
    print(f"box {info['outer'][0]:.1f} x {info['outer'][1]:.1f} x {info['depth']:.0f} mm, watertight {box_mesh.is_watertight}, "
          f"hinge at {info['hinge_frac']:.2f} of box height, flat foot {info['foot']:.1f} mm")
    mod, minfo = ks.make_module(a.size)
    leg, linfo = ks.make_leg(a.size)
    pin = ks.make_pin()
    for nm, m in (("module", mod), ("leg", leg), ("pin", pin)):
        m.export(out / f"wedding_kick_{nm}.stl")
        print(nm, "watertight", m.is_watertight, "bounds", m.bounds.round(1).tolist())
    # interference: module / leg / pin against the box, locked and opened
    for nm, m in (("module", ks.module_in_box(mod, a.size)), ("pin", ks.pin_in_box(pin, a.size))):
        iv = trimesh.boolean.intersection([box_mesh, m], engine="manifold")
        print(f"interference box vs {nm}: {iv.volume if len(iv.faces) else 0:.3f} mm3")
    for th in (0, 23.5):
        iv = trimesh.boolean.intersection([box_mesh, ks.leg_in_box(leg, a.size, th)], engine="manifold")
        print(f"interference box vs leg at {th} deg: {iv.volume if len(iv.faces) else 0:.3f} mm3")
    # one plate for the box + leg + module + pin (single colour)
    bc, lm, mm_, pm = box_mesh.copy(), leg.copy(), mod.copy(), pin.copy()
    BX0, BY0, GAP = 3.0, 1.5, 3.0
    bc.apply_translation([BX0 - bc.bounds[0][0], BY0 - bc.bounds[0][1], 0])
    lm.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, (0, 0, 1)))
    lm.apply_translation([BX0 - lm.bounds[0][0], bc.bounds[1][1] + GAP - lm.bounds[0][1], 0])
    mm_.apply_translation([lm.bounds[1][0] + GAP - mm_.bounds[0][0], bc.bounds[1][1] + GAP - mm_.bounds[0][1], 0])
    pm.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 0, 1)))
    pm.apply_translation([bc.bounds[1][0] + GAP - pm.bounds[0][0], BY0 - pm.bounds[0][1] + 20, 0])
    allp = [("box", bc, 1), ("leg", lm, 1), ("module", mm_, 1), ("pin", pm, 1)]
    allb = trimesh.util.concatenate([p_[1] for p_ in allp]).bounds
    ccx, ccy = (allb[0][0] + allb[1][0]) / 2, (allb[0][1] + allb[1][1]) / 2
    for _, m_, _ in allp:
        m_.apply_translation([-ccx, -ccy, 0])
    ps = build_project_settings(petg, cols, None)
    write_bambu_3mf(out / "wedding_box_all.3mf", allp, center=(ccx, ccy), name="wedding_box_all", project_settings=ps)
    print(f"ONE box plate: x {allb[0][0]:.1f}..{allb[1][0]:.1f}, y {allb[0][1]:.1f}..{allb[1][1]:.1f} (H2D: x 0-~305, y 0-320)")
    np.save(out / "fix_points.npy", np.array(fp))


if __name__ == "__main__":
    main()
