"""Version 2 of the wrench key holder: the 300 mm wrench (cad/wrench/wrench.py, imported UNCHANGED) + the workshop traced from the picture.
Run: python cad/wrench/workshop/workshop.py [--out DIR] [--stretch 1.5]
Colours (owner decision): black, white (also the grey), orange (also the red).  Z is measured from the wall.
house base (black) Z 0..PLATE_T+FACE (overhangs the wrench above the bar), white/orange details +RELIEF on top of it.
WS_STRETCH stretches the house vertically about its bottom line (the disc stays round) so the details are big enough to print."""
import argparse, json, sys
from pathlib import Path
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from build123d import Compound, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import wrench as W

PARAMS = dict(FACE=1.3, RELIEF=0.8, WS_STRETCH=1.5, MIN_FEATURE_MM=0.7)
ws = json.loads((HERE / "workshop_trace.json").read_text())
YREF = 296 * ws["K"]                                   # house bottom line (orig px): the stretch keeps it fixed

def to_poly(r, stretch):
    f = (lambda p: W.m((p[0], YREF - (YREF - p[1]) * stretch)))
    return Polygon([f(p) for p in r["outer"]], [[f(p) for p in h] for h in r["holes"]]).buffer(0)

def union_of(rs, stretch): return unary_union([to_poly(r, stretch) for r in rs]) if rs else Polygon()

def clean(poly, min_mm):
    return poly.buffer(-min_mm / 2).buffer(min_mm / 2) if not poly.is_empty else poly       # drop features thinner than min_mm

def disc_white(c, R, n_holes=16):
    """Brake rotor (annulus with drilled holes), hub ring with 5 bolt holes, centre bore. c = centre mm, R = disc radius mm."""
    import math
    cx, cy = c
    rotor = Point(c).buffer(R * 0.93, 64).difference(Point(c).buffer(R * 0.50, 64))
    holes = [Point((cx + R * 0.72 * math.cos(2 * math.pi * i / n_holes), cy + R * 0.72 * math.sin(2 * math.pi * i / n_holes))).buffer(R * 0.058, 12)
             for i in range(n_holes)]
    hub = Point(c).buffer(R * 0.40, 48).difference(Point(c).buffer(R * 0.13, 32))
    bolts = [Point((cx + R * 0.27 * math.cos(2 * math.pi * i / 5 + 0.3), cy + R * 0.27 * math.sin(2 * math.pi * i / 5 + 0.3))).buffer(R * 0.055, 12)
             for i in range(5)]
    return rotor.difference(unary_union(holes)).union(hub.difference(unary_union(bolts)))

def caliper_shape(c, R):
    """Red caliper: crescent over the right side of the rotor (measured on the picture: outer edge = disc edge, about 40 % of R wide)."""
    from shapely.geometry import box
    cx, cy = c
    ring = Point(c).buffer(R * 1.0, 64).difference(Point(c).buffer(R * 0.60, 64))
    sector = box(cx + R * 0.22, cy - R * 0.80, cx + R * 1.2, cy + R * 0.92)       # y up: bottom edge lower than the top edge in the picture
    return ring.intersection(sector).buffer(-R * 0.04).buffer(R * 0.04)

def build(stretch=None):
    P = PARAMS; st = stretch or P["WS_STRETCH"]; z0 = W.PARAMS["PLATE_T"]; face = z0 + P["FACE"]; top = face + P["RELIEF"]
    house = union_of(ws["house"], st)
    dc = Point(W.m(tuple(ws["disc"]["c"]))).buffer(ws["disc"]["r"] * W.S, 64)
    base_zone = unary_union([house, dc])
    cal = caliper_shape(dc.centroid.coords[0], ws["disc"]["r"] * W.S)                          # caliper sits over the rotor
    white = unary_union([union_of(ws["house_white"], st), disc_white(dc.centroid.coords[0], ws["disc"]["r"] * W.S)]).intersection(base_zone).difference(cal)
    orange = unary_union([union_of(ws["house_orange"], st), cal]).intersection(unary_union([base_zone, dc.buffer(1.0)])).difference(white)
    white, orange = clean(white, P["MIN_FEATURE_MM"]), clean(orange, P["MIN_FEATURE_MM"])
    black = W.solid(house, 0, face) + W.solid(dc.difference(house), z0, face)
    return {"workshop": {"black": black, "white": W.solid(white, face, top), "orange": W.solid(orange, face, top)}}, dict(
        house=house.bounds, areas=dict(white=white.area, orange=orange.area))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE / "out")); ap.add_argument("--stretch", type=float, default=PARAMS["WS_STRETCH"])
    a = ap.parse_args(); out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    parts, info = W.build()                            # the 300 mm wrench, untouched
    ws_parts, winfo = build(a.stretch); parts.update(ws_parts)
    print("house bounds mm", [round(v, 1) for v in winfo["house"]], "stretch", a.stretch)
    for name, cols in parts.items():
        for col, ss in cols.items():
            if not ss: continue
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            if name == "workshop": print(name, col, len(ss), "solids valid=%s" % all(s.is_valid for s in c.solids()))
