"""Workshop in 3D from the clean vector drawing (vector_workshop.py).  Z from the wall: black base (house + disc plate) 0..plate+FACE,
white/orange details +RELIEF on top.  Features thinner than MIN_FEATURE_MM are dropped/thickened (printing limit).
Run: python cad/wrench/workshop/workshop_v4.py --out DIR [--stretch 1.25] [--car-trace car_trace.json]"""
import argparse, sys
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.ops import transform, unary_union
from build123d import Compound, export_step, export_stl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import wrench as W
import vector_workshop as VW

PARAMS = dict(FACE=1.3, RELIEF=0.8, MIN_FEATURE_MM=0.7)

def to_mm(g):
    def f(x, y, z=None):
        x = np.asarray(x) * W.K; y = np.asarray(y) * W.K            # view units -> original picture px
        return (x - W.CX) * W.S, -(y - W.CY) * W.S                  # -> mm (same mapping as the wrench body)
    return transform(f, g)

def clean(g, m):
    return g if g.is_empty else g.buffer(-m / 2).buffer(m / 2)

def build(stretch=1.25, car_trace=None, ws_scale=1.0, disc_scale=1.0, text="WORKSHOP"):
    P = PARAMS; g = VW.build(stretch, car_trace, disc_scale, text)
    y_hb = W.m((0, 296 * W.K))[1]                                   # house bottom line (mm): the uniform scale keeps it where it is
    sc = (lambda x: affinity.scale(x, ws_scale, ws_scale, origin=(0, y_hb))) if ws_scale != 1.0 else (lambda x: x)
    panel, white, orange = sc(to_mm(g["panel"])), sc(to_mm(g["white"])), sc(to_mm(g["orange"]))
    white, orange = clean(white, P["MIN_FEATURE_MM"]), clean(orange, P["MIN_FEATURE_MM"])
    z0 = W.PARAMS["PLATE_T"]; face = z0 + P["FACE"]; top = face + P["RELIEF"]
    house = sc(to_mm(g["house"])); disc = sc(to_mm(g["disc_base"]))
    black = W.solid(house, 0, face) + W.solid(disc.difference(house), W.PARAMS["BORDER_T"], face)      # disc plate rests on the border layer (z 2), not in the air
    return {"workshop": {"black": black, "white": W.solid(white, face, top), "orange": W.solid(orange, face, top)}}, dict(
        bounds=unary_union([house, disc]).bounds)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--stretch", type=float, default=1.25)
    ap.add_argument("--car-trace"); ap.add_argument("--no-hooks", action="store_true"); ap.add_argument("--ws-scale", type=float, default=1.0)
    a = ap.parse_args(); out = Path(a.out); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "step").mkdir(exist_ok=True)
    if a.no_hooks: W.PARAMS["HOOK_N"] = 0
    parts, _ = W.build(); ws, info = build(a.stretch, a.car_trace, a.ws_scale); parts.update(ws)
    print("workshop bounds mm", [round(v, 1) for v in info["bounds"]])
    for name, cols in parts.items():
        for col, ss in cols.items():
            if not ss: continue
            c = Compound(children=ss); c.label = f"{name}_{col}"
            export_step(c, str(out / "step" / f"{name}__{col}.step")); export_stl(c, str(out / "stl" / f"{name}__{col}.stl"), tolerance=0.02, angular_tolerance=0.1)
            if name == "workshop": print(name, col, len(ss), "solids valid=%s" % all(s.is_valid for s in c.solids()))
