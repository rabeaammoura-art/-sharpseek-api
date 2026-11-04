"""Version 7: the v6 design at 3.3x (about 1 m) WITHOUT hooks, split into 4 interlocking columns (dovetail puzzle tabs, 0.3 mm clearance), plain, with
the owner's word.  Only XY is scaled: thickness is chosen for the big size (border 3, plate to 9, house base to 11, relief +2.5, orange line +1.8 mm).
Tabs are dovetail prisms extruded along Z (no overhang when printed plate-down) and are pressed in from the front. Wall: 2 countersunk screw holes per column.
Third-party inputs stay out of the repo: --outline / --car-trace local files.
Run: python cad/wrench/workshop/v7_big.py --outline O.json --car-trace C.json --text Aldawayme --out DIR [--scale 3.3]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
from build123d import Compound, Solid, Pos, Box, Align, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import wrench as W
import workshop_v4 as WS4
import vector_workshop as VW
import v6_final as V6

Z = dict(BORDER=3.0, PLATE=9.0, FACE=2.0, RELIEF=2.5, BAND=1.8)
TAB = dict(NECK=9.0, HEAD=15.0, LEN=11.0, CLEAR=0.3)
SCREW = dict(D=5.4, HEAD=11.0, DEPTH=4.5)


def polys(a, F):
    """All 2D shapes in mm at the big scale (XY scaled by F about the origin)."""
    V6.P["SCREW_XS"] = ()                                           # no small-size screw holes: the big version has its own
    sh = V6.body_shapes(a.outline); band = V6.orange_line(sh)
    sc = lambda g: affinity.scale(g, F, F, origin=(0, 0))
    out = dict(body=sc(sh["body"]), plate=sc(sh["plate"]), band=sc(band), handle_top=sh["top"] * F, handle_bot=sh["newbot"] * F)
    g = VW.build(1.25, a.car_trace, 0.75, a.text)
    y_hb = W.m((0, 296 * W.K))[1]
    s2 = lambda x: affinity.scale(WS4.to_mm(x), 1.25, 1.25, origin=(0, y_hb))
    white, orange = WS4.clean(s2(g["white"]), 0.7), WS4.clean(s2(g["orange"]), 0.7)
    house, disc = s2(g["house"]), s2(g["disc_base"])
    out.update(white=sc(white), orange_ws=sc(orange), house=sc(house), disc=sc(disc))
    return out


def solids(p):
    z = Z; face = z["PLATE"] + z["FACE"]; top = face + z["RELIEF"]
    body, plate, band = p["body"], p["plate"], p["band"]
    on_plate = band.intersection(plate.buffer(-0.3)); on_border = band.intersection(body.buffer(-0.5)).difference(plate.buffer(-0.3))
    black = (W.solid(body, 0, z["BORDER"]) + W.solid(plate, z["BORDER"], z["PLATE"]) + W.solid(p["house"], 0, face)
             + W.solid(p["disc"].difference(p["house"]), z["BORDER"], face))
    white = W.solid(p["white"], face, top)
    orange = W.solid(on_plate, z["PLATE"], z["PLATE"] + z["BAND"]) + W.solid(on_border, z["BORDER"], z["BORDER"] + z["BAND"]) + W.solid(p["orange_ws"], face, top)
    return dict(black=black, white=white, orange=orange)


def _sol(r):
    return [] if r is None else list(r.solids())


def inter(a, b):
    try: return _sol(a & b)
    except Exception: return []


def sub(a, b):
    try: return _sol(a - b)
    except Exception: return [a]


def box3(x0, x1, y0=-2000.0, y1=2000.0, z0=-5.0, z1=60.0):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def prism(poly, z0=-1.0, z1=40.0):
    return W.solid(poly, z0, z1)[0]


def tab_poly(c, y, clear=0.0):
    n, h, L = TAB["NECK"] / 2 + clear, TAB["HEAD"] / 2 + clear, TAB["LEN"]
    return Polygon([(c - 3, y - n), (c, y - n), (c + L + clear, y - h), (c + L + clear, y + h), (c, y + n), (c - 3, y + n)])


def seam_ys(p, c, relief):
    """y positions of the dovetail tabs on the seam x = c: inside the real black material and with NO raised relief (white/orange/line) above the
    tab or its socket (a relief over the socket hole would hang in the air when printed plate-down)."""
    mat = unary_union([p["body"], p["house"]])
    seg = LineString([(c, -2000), (c, 2000)]).intersection(mat)
    segs = [seg] if seg.geom_type == "LineString" else list(seg.geoms)
    seg = max(segs, key=lambda s: s.length); y0, y1 = seg.bounds[1], seg.bounds[3]
    cand = []
    for y in np.arange(y0 + TAB["HEAD"], y1 - TAB["HEAD"], 4.0):
        zone = tab_poly(c, float(y), TAB["CLEAR"] + 2.0).buffer(1.0)
        if zone.within(mat.buffer(-0.5)) and not zone.intersects(relief): cand.append(float(y))
    if len(cand) < 2: raise SystemExit(f"seam x={c:.0f}: no free place for tabs (candidates {len(cand)})")
    hc = (p["handle_top"] + p["handle_bot"]) / 2
    first = min(cand, key=lambda y: abs(y - hc)); last = max(cand)
    pick = [first] + ([min(cand, key=lambda y: abs(y - (first + last) / 2))] if last - first > 80 else []) + ([last] if last - first > 40 else [])
    return sorted(set(pick)), (y0, y1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--outline", required=True); ap.add_argument("--car-trace"); ap.add_argument("--text", default="Aldawayme")
    ap.add_argument("--out", required=True); ap.add_argument("--scale", type=float, default=3.3)
    a = ap.parse_args(); out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    F = a.scale; p = polys(a, F); sol = solids(p)
    xmin, xmax = unary_union([p["body"], p["house"]]).bounds[0], unary_union([p["body"], p["house"]]).bounds[2]
    n = 4; cuts = [xmin + (xmax - xmin) * i / n for i in range(1, n)]
    edges = [xmin - 1] + cuts + [xmax + 1]
    print("size mm", round(xmax - xmin, 1), "cuts", [round(c, 1) for c in cuts])
    relief = unary_union([p["white"], p["orange_ws"], p["band"]]).buffer(0.5)
    tabs = {}
    for c in cuts:
        ys, rng = seam_ys(p, c, relief); tabs[c] = ys; print("seam", round(c, 1), "tabs at y", [round(y) for y in ys])
    pieces = {}
    for k in range(n):
        x0, x1 = edges[k], edges[k + 1]; win = box3(x0, x1); cols = {}
        for col, ss in sol.items():
            res = []
            for s in ss: res.extend(inter(s, win))
            cols[col] = res
        # tab on the right seam (piece k), socket on the left seam (piece k) -> black only
        if k < n - 1:
            c = cuts[k]
            for y in tabs[c]:
                t = prism(tab_poly(c, y)); cols["black"] += [r_ for s in sol["black"] for r_ in inter(t, s)]
        if k > 0:
            c = cuts[k - 1]
            for y in tabs[c]:
                sock = prism(tab_poly(c, y, TAB["CLEAR"])); cols["black"] = [r_ for s in cols["black"] for r_ in sub(s, sock)]
        # wall screws: 2 per column on the handle's centre line (countersunk, 45 deg)
        hy = (p["handle_top"] + p["handle_bot"]) / 2
        for sx in (x0 + 0.2 * (x1 - x0), x0 + 0.8 * (x1 - x0)):
            if k == 0: sx = max(sx, -(abs(xmin)) + 200)            # keep clear of the jaw
            if k == n - 1: sx = min(sx, xmax - 200)                 # keep clear of the ring head
            r0 = SCREW["D"] / 2 - 0.2; z0c = Z["PLATE"] - SCREW["DEPTH"] - 0.2; hc = Z["PLATE"] + 0.2 - z0c
            hole = Pos(sx, hy, -1) * Solid.make_cylinder(SCREW["D"] / 2, 40); cone = Pos(sx, hy, z0c) * Solid.make_cone(r0, r0 + hc, hc)
            cols["black"] = [r_ for s in cols["black"] for q in sub(s, hole) for r_ in sub(q, cone)]
        bl = cols["black"]
        if len(bl) > 1: cols["black"] = list(bl[0].fuse(*bl[1:]).clean().solids())          # one clean shell (overlapping shells share edges: non-manifold STL)
        pieces[f"column_{k + 1}"] = cols
    for name, cols in pieces.items():
        allv = [s for ss in cols.values() for s in ss]; bb = Compound(children=allv).bounding_box()
        print(name, "x", round(bb.min.X, 1), round(bb.max.X, 1), "w", round(bb.size.X, 1), "h", round(bb.size.Y, 1), "t", round(bb.size.Z, 1), {c: len(v) for c, v in cols.items()})
        for col, ss in cols.items():
            if not ss: continue
            c_ = Compound(children=ss); c_.label = f"{name}_{col}"
            export_step(c_, str(out / "step" / f"{name}__{col}.step")); export_stl(c_, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.03, angular_tolerance=0.1)


if __name__ == "__main__":
    main()
