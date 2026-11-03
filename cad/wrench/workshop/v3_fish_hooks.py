"""Version 3: wrench + workshop (v2) with J hooks whose side profile is taken from a fish-skeleton hook the owner has permission to adapt.
The hook profile (2D side outline, y/z) is NOT stored in the repo (third-party design): extract it from the owner's 3MF into a local json
and pass it with --profile.  The hooks are part of the print (plate on the bed, J curl standing up, no supports, no screws).
Run: python cad/wrench/workshop/v3_fish_hooks.py --profile hook_profile_yz.json --out DIR [--stretch 1.5] [--hook-scale 0.8]"""
import argparse, json, sys
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from build123d import Compound, Face, Wire, Solid, Vector, Pos, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import wrench as W
import workshop as WS

def hook_solids(profile_json, scale):
    prof = json.loads(Path(profile_json).read_text()); P = Polygon(prof["yz"]).buffer(0)
    P = P.intersection(box(-60, -20, -8.0, 20))                    # hook below the fish spine (y <= -8): stem + J
    width = 6.0 * scale
    y_attach = W.md(0, W.tr["bar_bottom_px"] / W.K)[1]             # bar bottom edge (mm)
    zt = W.PARAMS["PLATE_T"]
    hooks = []
    for i in range(5):
        xc = W.md(W.PARAMS["HOOK_X0"] + i * W.PARAMS["HOOK_DX"], 0)[0]
        pts = [(y_attach + (y + 8.0) * scale, (z + 14.7) * scale) for y, z in P.exterior.coords]      # (Y, Z): wall at Z=0
        poly = Polygon(pts).buffer(0)
        poly = unary_union([poly, box(y_attach - 0.01, 0, y_attach + 6.0, min(zt, 6.2 * scale))])   # stem runs 6 mm up into the bar
        face = Face(Wire.make_polygon([(0, y, z) for y, z in poly.exterior.coords[:-1]]))
        hooks.append(Pos(xc - width / 2, 0, 0) * Solid.extrude(face, Vector(width, 0, 0)))
    return hooks

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--stretch", type=float, default=1.5); ap.add_argument("--hook-scale", type=float, default=0.8)
    a = ap.parse_args(); out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    W.PARAMS["HOOK_N"] = 0                                         # no traced hooks and no hook screw holes in the body
    parts, info = W.build(); parts.update(WS.build(a.stretch)[0])
    parts["hooks"] = {"black": hook_solids(a.profile, a.hook_scale)}
    for name, cols in parts.items():
        for col, ss in cols.items():
            if not ss: continue
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            print(name, col, len(ss), "valid=%s" % all(s.is_valid for s in c.solids()))
