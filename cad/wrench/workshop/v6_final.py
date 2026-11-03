"""Version 6 (owner-approved picture): found-wrench body (300 mm, jaw mirrored, handle 20 mm, ring head +15 %), ONE continuous orange line
(lower jaw prong -> around the jaw slot -> U-turn at the upper prong -> handle top edge -> 240 deg around the ring head; on the ring wall there is
no plate level so the line runs on the border level, 1.4 mm wide), clean workshop 1.25x with the disc at 75 % and the word the owner chose,
fish-profile J hooks (scale 1.0, 45 deg tip slope).  Third-party inputs stay OUT of the repo (local files passed as arguments).
Run: python cad/wrench/workshop/v6_final.py --outline O.json --profile P.json --car-trace C.json --text Aldawayme --out DIR"""
import argparse, json, math, subprocess, sys
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, Point, box, LineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from build123d import Compound, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import wrench as W
import workshop_v4 as WS4
import v5_new_body as V5

P = dict(LENGTH=300.0, BORDER_T=2.0, PLATE_T=5.0, INSET=1.7, BAND_H=1.0, HANDLE=20.0, RING=1.15, OVERLAP=0.4, WRAP=240.0,
         HOOK_XS=(-80.0, -40.0, 0.0, 40.0, 80.0))

def smooth(t):
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

def body_shapes(outline_json):
    o = json.loads(Path(outline_json).read_text()); g = Polygon(o["outer"], o["holes"]).buffer(0)
    s = P["LENGTH"] / (g.bounds[2] - g.bounds[0]); g = affinity.scale(g, s, s, origin=(0, 0))
    h = g.intersection(box(-60, -50, 60, 50)); yc = (h.bounds[1] + h.bounds[3]) / 2
    g = affinity.scale(g, 1, -1, origin=(0, yc)); h = g.intersection(box(-60, -50, 60, 50))      # short jaw prong at the bottom
    top, bot = h.bounds[3], h.bounds[1]; y_hb = W.m((0, 296 * W.K))[1]; dy = y_hb + P["OVERLAP"] - top
    g = affinity.translate(g, 0, dy); top += dy; bot += dy
    hole0 = Polygon(g.interiors[0]); xr, yr = hole0.centroid.x, hole0.centroid.y
    F = P["RING"]
    def ring_scale(q):
        rho = math.hypot(q[0] - xr, q[1] - yr); f = 1 + (F - 1) * (1 - smooth((rho - 19) / 13))
        return (xr + (q[0] - xr) * f, yr + (q[1] - yr) * f)
    extra = P["HANDLE"] - (top - bot); newbot = bot - extra; yc0 = (top + bot) / 2
    def wx(x):                                           # widen the handle downward, eased to 0 over the necks (no notch)
        if x < -90: return smooth((x + 118) / 28)
        if x > 106: return smooth((124 - x) / 18)
        return 1.0
    ext = [ring_scale(q) for q in g.exterior.segmentize(0.4).coords]
    ext = [(x, y - extra * wx(x) if y < yc0 else y) for x, y in ext]
    hole_pts = [ring_scale(q) for q in g.interiors[0].segmentize(0.3).coords]
    ext2 = Polygon(ext).buffer(0.0)
    body = orient(Polygon(ext2.exterior, [hole_pts])); plate = orient(body.buffer(-P["INSET"], join_style=1))
    plate = plate.difference(Point(xr, yr).buffer(18.05 * (F / 1.15) + 2.0, 64))     # the ring wall is only 3-5 mm: no plate level around the ring head (it would only leave scalloped slivers)
    return dict(body=body, plate=plate, ext2=ext2, xr=xr, yr=yr, yc0=yc0, top=top, newbot=newbot)

def orange_line(sh):
    ext2, xr, yr, yc0, RING = sh["ext2"], sh["xr"], sh["yr"], sh["yc0"], P["RING"]
    cw = list(orient(Polygon(ext2.exterior), sign=-1).exterior.coords)[:-1]                       # clockwise: interior on the right
    i0 = min(range(len(cw)), key=lambda i: (cw[i][0] if cw[i][1] > yc0 else 1e9))                 # upper prong tip
    n = len(cw); jl = min((i for i in range(n) if cw[i][1] < yc0), key=lambda i: cw[i][0])        # lower prong tip
    seq = cw[i0:] + cw[:i0]
    itop = min((i for i, q in enumerate(seq) if q[0] > xr), default=0)
    ang = lambda q: math.atan2(q[1] - yr, q[0] - xr); cum = 0.0; stop = len(seq)
    for i in range(itop + 1, len(seq)):
        d = (ang(seq[i]) - ang(seq[i - 1]) + math.pi) % (2 * math.pi) - math.pi; cum += d
        if cum <= -math.radians(P["WRAP"]) or (cum <= -math.radians(150) and math.hypot(seq[i][0] - xr, seq[i][1] - yr) > 17.5 * RING): stop = i; break
    pts = seq[:stop + 1]; cl = [0.0]
    for i in range(1, len(pts)): cl.append(cl[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    rho = [math.hypot(q[0] - xr, q[1] - yr) for q in pts]
    s_ring = next((cl[i] for i, r in enumerate(rho) if r <= 17.5 * RING), cl[-1]); TW = 22.0
    DH, WH, DR, WR = 4.2, 2.0, 1.35, 1.4
    tip = cw[i0]; CUT = 14.0; C1 = []
    for i, q in enumerate(pts):
        j0, j1 = max(i - 1, 0), min(i + 1, len(pts) - 1); dx, dy = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]; L = math.hypot(dx, dy) or 1.0
        t = smooth((cl[i] - (s_ring - TW)) / TW); d = DH + (DR - DH) * t; w = WH + (WR - WH) * t
        C1.append((q[0] + dy / L * d, q[1] - dx / L * d, w))
    C1 = [c for c in C1 if math.hypot(c[0] - tip[0], c[1] - tip[1]) >= CUT or c is C1[-1]]
    idx = []; i = i0
    while True:
        idx.append(i)
        if i == jl: break
        i = (i - 1) % n
        if len(idx) > n: break
    sl = [cw[k] for k in idx]; C2 = []
    for k, q in enumerate(sl):
        j0, j1 = max(k - 1, 0), min(k + 1, len(sl) - 1); dx, dy = sl[j1][0] - sl[j0][0], sl[j1][1] - sl[j0][1]; L = math.hypot(dx, dy) or 1.0
        C2.append((q[0] - dy / L * 2.9, q[1] + dx / L * 2.9, 1.5))
    C2 = [c for c in C2 if math.hypot(c[0] - tip[0], c[1] - tip[1]) >= CUT and math.hypot(c[0] - cw[jl][0], c[1] - cw[jl][1]) >= 7.0]
    A = C2[0] if math.hypot(C2[0][0] - tip[0], C2[0][1] - tip[1]) < math.hypot(C2[-1][0] - tip[0], C2[-1][1] - tip[1]) else C2[-1]
    if A is not C2[0]: C2 = C2[::-1]
    B = C1[0]; mid = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2); vx, vy = tip[0] - mid[0], tip[1] - mid[1]; vl = math.hypot(vx, vy) or 1.0
    ctrl = (mid[0] + vx / vl * 5.0, mid[1] + vy / vl * 5.0)
    bez = [((1 - t) ** 2 * A[0] + 2 * (1 - t) * t * ctrl[0] + t * t * B[0], (1 - t) ** 2 * A[1] + 2 * (1 - t) * t * ctrl[1] + t * t * B[1], 1.8) for t in np.linspace(0, 1, 25)]
    chain = C2[::-1] + bez + C1                                                                    # lower prong -> slot -> U-turn -> top edge -> ring
    parts = []
    for k, (x, y, w) in enumerate(chain):
        parts.append(Point(x, y).buffer(w / 2, 8))
        if k: parts.append(LineString([chain[k - 1][:2], (x, y)]).buffer(max(min(w, chain[k - 1][2]) / 2 - 0.05, 0.1), cap_style=1))
    return unary_union(parts).simplify(0.05)

def body_solids(sh, band):
    body, plate = sh["body"], sh["plate"]
    on_plate = band.intersection(plate.buffer(-0.1)); on_border = band.intersection(body.buffer(-0.2)).difference(plate.buffer(-0.1))
    black = W.solid(body, 0, P["BORDER_T"]) + W.solid(plate, P["BORDER_T"], P["PLATE_T"])
    orange = W.solid(on_plate, P["PLATE_T"], P["PLATE_T"] + P["BAND_H"]) + W.solid(on_border, P["BORDER_T"], P["BORDER_T"] + P["BAND_H"])
    return black, orange

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--outline", required=True); ap.add_argument("--profile", required=True)
    ap.add_argument("--car-trace"); ap.add_argument("--text", default="Aldawayme"); ap.add_argument("--out", required=True)
    ap.add_argument("--stretch", type=float, default=1.25); ap.add_argument("--ws-scale", type=float, default=1.25); ap.add_argument("--disc", type=float, default=0.75)
    a = ap.parse_args(); out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    sh = body_shapes(a.outline); band = orange_line(sh); b_black, b_orange = body_solids(sh, band)
    V5.PARAMS["HOOK_SCALE"] = 1.0; V5.PARAMS["HOOK_CHAMFER"] = True; V5.PARAMS["HOOK_XS"] = P["HOOK_XS"]
    parts = {"body": {"black": b_black, "orange": b_orange}}
    parts.update(WS4.build(a.stretch, a.car_trace, a.ws_scale, a.disc, a.text)[0])
    parts["hooks"] = {"black": V5.hooks(a.profile, sh["newbot"])}
    print("body bounds", [round(v, 1) for v in sh["body"].bounds], "handle top/bottom", round(sh["top"], 1), round(sh["newbot"], 1))
    for name, cols in parts.items():
        for col, ss in cols.items():
            if not ss: continue
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            print(name, col, len(ss), "valid=%s" % all(s.is_valid for s in c.solids()))
