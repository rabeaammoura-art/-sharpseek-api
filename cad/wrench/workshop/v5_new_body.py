"""Version 5: NEW body (outline taken from the found 30 cm combination wrench, owner has the designer's OK to adapt) + clean workshop (v4)
+ J hooks with the side profile of the fish-skeleton hook at scale 1.0.  Plain wrench: no text, no screws.
The two third-party inputs stay OUT of the repo (local files passed as arguments):
  --outline   wrench_outline_mm.json  (silhouette of the wrench in mm: {"outer": [[x,z]...], "holes": [...]}, jaw on the left, z up)
  --profile   hook_profile_yz.json    (side outline of the hook, y/z)
Run: python cad/wrench/workshop/v5_new_body.py --outline O.json --profile P.json --car-trace C.json --out DIR"""
import argparse, json, sys
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from build123d import Compound, Face, Wire, Solid, Vector, Pos, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import wrench as W
import workshop_v4 as WS4

PARAMS = dict(LENGTH_MM=300.0, BORDER_T=2.0, PLATE_T=5.0, INSET=1.7, BAND_H=1.0, BAND_OFF=3.2, BAND_W=1.5,
              HOOK_SCALE=1.0, HOOK_CHAMFER=True, FLIP=True, HOOK_XS=(-80.0, -40.0, 0.0, 40.0, 80.0), OVERLAP=0.4)

def body(outline_json):
    P = PARAMS; o = json.loads(Path(outline_json).read_text())
    g = Polygon(o["outer"], o["holes"]).buffer(0)
    s = P["LENGTH_MM"] / (g.bounds[2] - g.bounds[0])
    g = affinity.scale(g, s, s, origin=(0, 0))
    handle = g.intersection(box(-60, -50, 60, 50))                # straight part of the bar
    if P["FLIP"]:                                                 # owner: the SHORT jaw prong must be at the bottom -> mirror about the handle's centre line (handle stays put)
        yc = (handle.bounds[1] + handle.bounds[3]) / 2
        g = affinity.scale(g, 1, -1, origin=(0, yc)); handle = g.intersection(box(-60, -50, 60, 50))
    top, bot = handle.bounds[3], handle.bounds[1]
    y_hb = W.m((0, 296 * W.K))[1]                                 # house bottom line (mm) in the workshop's coordinate system
    dy = y_hb + P["OVERLAP"] - top
    g = affinity.translate(g, 0, dy); bot += dy; top += dy
    plate = g.buffer(-P["INSET"], join_style=1)
    band = g.buffer(-P["BAND_OFF"], join_style=1).difference(g.buffer(-(P["BAND_OFF"] + P["BAND_W"]), join_style=1)).intersection(plate.buffer(-0.2))
    b = W.solid(g, 0, P["BORDER_T"]) + W.solid(plate, P["BORDER_T"], P["PLATE_T"])
    o_ = W.solid(band, P["PLATE_T"], P["PLATE_T"] + P["BAND_H"])
    return {"black": b, "orange": o_}, dict(bounds=g.bounds, top=top, bot=bot, scale=s)

def hooks(profile_json, y_attach):
    P = PARAMS; sc = P["HOOK_SCALE"]
    prof = json.loads(Path(profile_json).read_text()); poly0 = Polygon(prof["yz"]).buffer(0).intersection(box(-60, -20, -8.0, 20))
    if P["HOOK_CHAMFER"]:        # 45 deg slope under the tip (profile y/z): without it the tip is an 11 mm horizontal cantilever when printed with the plate on the bed
        poly0 = unary_union([poly0, Polygon([(-25.5, 8.4), (-38.5, -4.6), (-38.5, 4.0), (-31.0, 10.0)])])
    width = 6.0 * sc; zt = P["PLATE_T"]; out = []
    for xc in P["HOOK_XS"]:
        pts = [(y_attach + (y + 8.0) * sc, (z + 14.7) * sc) for y, z in poly0.exterior.coords]
        poly = unary_union([Polygon(pts).buffer(0), box(y_attach - 0.01, 0, y_attach + 6.0, min(zt, 6.2 * sc))]).intersection(box(-500, 0, 500, 500))     # stem runs 6 mm up into the bar
        face = Face(Wire.make_polygon([(0, y, z) for y, z in poly.exterior.coords[:-1]]))
        out.append(Pos(xc - width / 2, 0, 0) * Solid.extrude(face, Vector(width, 0, 0)))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--outline", required=True); ap.add_argument("--profile", required=True)
    ap.add_argument("--car-trace"); ap.add_argument("--out", required=True); ap.add_argument("--stretch", type=float, default=1.25)
    ap.add_argument("--hook-scale", type=float, default=1.0); ap.add_argument("--no-chamfer", action="store_true"); ap.add_argument("--no-flip", action="store_true")
    a = ap.parse_args(); PARAMS["HOOK_SCALE"] = a.hook_scale; PARAMS["HOOK_CHAMFER"] = not a.no_chamfer; PARAMS["FLIP"] = not a.no_flip
    out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    b, info = body(a.outline)
    parts = {"body": b}; parts.update(WS4.build(a.stretch, a.car_trace)[0])
    parts["hooks"] = {"black": hooks(a.profile, info["bot"])}
    print("body bounds mm", [round(v, 1) for v in info["bounds"]], "scale", round(info["scale"], 3), "handle top/bottom", round(info["top"], 1), round(info["bot"], 1))
    for name, cols in parts.items():
        for col, ss in cols.items():
            if not ss: continue
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            print(name, col, len(ss), "valid=%s" % all(s.is_valid for s in c.solids()))
