"""Wrench body (stage 1 of the workshop key holder): outline, orange band and ring teeth taken from the reference picture.
Run: python cad/wrench/wrench.py [--out cad/wrench/out]     (reads cad/wrench/wrench_trace.json made by trace_wrench.py)
Layers (Z up from the wall): L0 outer border 0..BORDER_T, L1 plate (inset) up to PLATE_T, orange band, screws.
The tooth ring is recessed: teeth cut in L0, a round opening in L1.  Length is one parameter (LENGTH_MM)."""
import argparse, json, math
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from build123d import Face, Wire, Solid, Vector, Compound, Pos, Cylinder, Box, Align, export_step, export_stl

HERE = Path(__file__).resolve().parent
PARAMS = dict(HOOK_T=10.0, HOOK_X0=603.0, HOOK_DX=216.25, HOOK_N=5, HOOK_PILOT_D=2.5, HOOK_HOLE_D=3.4, LENGTH_MM=610.0, BORDER_T=3.0, PLATE_T=7.0, BAND_H=1.4, INSET_MM=3.4, SCREW_R=6.4, SCREW_H=2.0)
tr = json.loads((HERE / "wrench_trace.json").read_text())
ox = [p[0] for p in tr["outline"]["outer"]]; oy = [p[1] for p in tr["outline"]["outer"]]
X0, X1 = min(ox), max(ox)
S = PARAMS["LENGTH_MM"] / (X1 - X0)                 # mm per picture pixel
CX, CY = (X0 + X1) / 2, (min(oy) + max(oy)) / 2
def m(p): return ((p[0] - CX) * S, -(p[1] - CY) * S)

def shp(r):
    return Polygon([m(p) for p in r["outer"]], [[m(p) for p in h] for h in r.get("holes", [])]).buffer(0)

def teeth(cx, cy, r_tip, r_root, n):
    pts = []
    for i in range(n):
        a0 = 2 * math.pi * i / n; da = 2 * math.pi / n
        for f, r in ((0.0, r_root), (0.12, r_tip), (0.50, r_tip), (0.62, r_root), (0.99, r_root)):
            a = a0 + f * da; pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(pts).buffer(0)

def face(poly):
    f = Face(Wire.make_polygon([(x, y, 0) for x, y in poly.exterior.coords[:-1]]),
             [Wire.make_polygon([(x, y, 0) for x, y in i.coords[:-1]]) for i in poly.interiors])
    return f

def solid(poly, z0, z1):
    parts = [poly] if poly.geom_type == "Polygon" else list(poly.geoms)
    out = []
    for p in parts:
        if p.area < 0.5: continue
        s = Solid.extrude(face(p), Vector(0, 0, z1 - z0)); out.append(Pos(0, 0, z0) * s)
    return out

K = tr["image_size"][0] / 2000.0                     # hook measurements below are in a 2000 px wide view
def md(x, y): return m((x * K, y * K))               # 2000-view coordinates -> mm
def hook_shape(cx):
    """Hook profile in the wall plane, measured on a 5x crop of the picture: slot-shaped plate with a rounded top,
    J curl at the bottom, ball on the tip.  cx = stem centre (2000-view x)."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    def P(x, y): return md(cx + x, y)
    stem = Polygon([P(-17.5, 348), P(17.5, 348), P(17.5, 450), P(-17.5, 450)])
    top = Point(P(0, 347.5)).buffer(17.5 * K * S, 32)
    ux0, uy0 = P(-22, 395); ux1, uy1 = P(38, 484)
    bottom = box(min(ux0, ux1), min(uy0, uy1), max(ux0, ux1), max(uy0, uy1)).buffer(-21 * K * S).buffer(21 * K * S, 48)
    arm = Polygon([P(8, 432), P(34, 432), P(34, 470), P(8, 470)])
    ball = Point(P(24.4, 425)).buffer(17 * K * S, 32)
    return unary_union([stem, top, bottom, arm, ball]).buffer(1.0).buffer(-1.0)

def hook_holes_xy(cx):
    return [md(cx, 352), md(cx, 384)]

def build():
    P = PARAMS
    ring = tr["ring"]; rc = m((ring["cx"], ring["cy"]))
    outline = shp(tr["outline"])
    hole_teeth = teeth(rc[0], rc[1], ring["r_tip"] * S, ring["r_root"] * S, ring["teeth"])
    opening = Point(rc).buffer(ring["r_open"] * S, 64)
    xs_h = [P["HOOK_X0"] + i * P["HOOK_DX"] for i in range(P["HOOK_N"])]
    hole_pts = [pt for cx in xs_h for pt in hook_holes_xy(cx)]
    holes = unary_union([Point(pt).buffer(P["HOOK_HOLE_D"] / 2, 24) for pt in hole_pts])
    L0 = outline.difference(hole_teeth).difference(holes)
    plate = outline.buffer(-P["INSET_MM"], join_style=1).difference(opening).difference(holes)
    band = unary_orange().intersection(plate.buffer(-0.2))
    black = solid(L0, 0, P["BORDER_T"]) + solid(plate, P["BORDER_T"], P["PLATE_T"])
    for sx, sy in tr["screws_px"]:
        x, y = m((sx, sy))
        h = Pos(x, y, P["PLATE_T"]) * Cylinder(P["SCREW_R"], P["SCREW_H"], align=(Align.CENTER, Align.CENTER, Align.MIN))
        for bx, by in ((9.6, 1.5), (1.5, 9.6)):
            h = h - Pos(x, y, P["PLATE_T"] + P["SCREW_H"] - 1.0) * Box(bx, by, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
        black.append(h)
    orange = solid(band, P["PLATE_T"], P["PLATE_T"] + P["BAND_H"])
    hooks = {}
    for i, cx in enumerate(xs_h):
        sh = hook_shape(cx)
        hs = solid(sh, P["PLATE_T"], P["PLATE_T"] + P["HOOK_T"])[0]
        for (hx, hy) in hook_holes_xy(cx):
            hs = hs - Pos(hx, hy, P["PLATE_T"]) * Cylinder(P["HOOK_PILOT_D"] / 2, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        hooks[f"hook_{i+1}"] = {"black": [hs]}
    res = {"wrench_body": {"black": black, "orange": orange}}
    res.update(hooks)
    return res, dict(L=outline.bounds, S=S)

def unary_orange():
    from shapely.ops import unary_union
    return unary_union([shp(o) for o in tr["orange"]])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE / "out")); a = ap.parse_args()
    out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    parts, info = build()
    print("bounds mm", [round(v, 1) for v in info["L"]], "scale mm/px %.4f" % info["S"])
    for name, cols in parts.items():
        for col, ss in cols.items():
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            print(name, col, len(ss), "solids valid=%s" % all(s.is_valid for s in c.solids()), "vol=%.0f" % sum(s.volume for s in c.solids()))
