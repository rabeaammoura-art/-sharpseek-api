"""Photoreal renders (Blender/Cycles) of the ACTUAL CAD geometry in out/. Usage: render_all.py <bpy-python> [view ...]
Module bodies are the ASSUMED placeholder envelopes; the red iris is a procedural stand-in for the Devil Eye's
own display content. The original turn-signal BRACKET is shown for context (unchanged part); no indicator lamp
is modelled because no CAD exists for it."""
import sys, json, subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import params as P, geom as G
from build123d import import_step, export_stl

OUT = G.OUT; PT = OUT / "parts"; REF = OUT / "ref"; RND = OUT / "renders"; RND.mkdir(parents=True, exist_ok=True); REF.mkdir(exist_ok=True)
BPY = sys.argv[1]
for s in "LR":
    t = REF / f"turnsignal_bracket_{s}.stl"
    if not t.exists():
        export_stl(import_step(str(G.ROOT / "input" / f"turnsignal_bracket_{s}_orig.step")), str(t), tolerance=0.05, angular_tolerance=0.1)

mx = lambda x: -x + P.RH_SHIFT_X          # left X -> right X


def lamp(side, on=False, hw=True, explode=0.0, inner=True):
    f = G.projector_frame(); d = G.devil_frame()
    sfx = side
    o = [dict(path=str(OUT / f"housing_{side}_mod.stl"), mat="asacf", smooth_angle=14),
         dict(path=str(REF / f"turnsignal_bracket_{side}.stl"), mat="plastic", color=[0.12, 0.12, 0.13])]
    def e(dy, dz=0.0):
        return [0.0, dy * explode, dz * explode] if explode else None
    parts = [("devil_adapter", "plastic", [0.05, 0.05, 0.055], e(60)), ("devil_clamp", "plastic", [0.05, 0.05, 0.055], e(100)),
             ("PH_devil_eye_ASSUMED", "black", None, e(150)),
             ("projector_carrier", "plastic", [0.05, 0.05, 0.055], e(70)), ("pivot_cap", "plastic", [0.05, 0.05, 0.055], e(90)),
             ("PH_projector_ASSUMED", "black", None, e(160)), ("PH_projector_lens", "lens" if not on else "emit_white", None, e(160)),
             ("inboard_bracket", "plastic", [0.05, 0.05, 0.055], e(30, -40)), ("outboard_pillar", "plastic", [0.05, 0.05, 0.055], e(30, -40)),
             ("wedge_A", "alu", None, e(30, 60)), ("wedge_B", "alu", None, e(30, 60))]
    for n, m, c, off in parts:
        ob = dict(path=str(PT / f"{n}_{sfx}.stl"), mat=m)
        if c: ob["color"] = c
        if m == "emit_white": ob["strength"] = 25.0
        if off: ob["offset"] = off
        o.append(ob)
    if hw and side == "L":
        for p in sorted(PT.glob("HW_*_L.stl")):
            ob = dict(path=str(p), mat="chrome")
            if explode: ob["offset"] = [0, 30 * explode, 60 * explode] if "screw" in p.name else [0, 70 * explode, 0]
            o.append(ob)
    cx, cz = P.DEVIL_C; x = cx if side == "L" else mx(cx)
    o.append(dict(disc=dict(center=[x, d["y_front"] - 0.3 + (150 * explode if explode else 0), cz], radius=P.DEVIL_LENS_D / 2 - 3),
                  mat=("eye" if on else "black"), strength=14.0))
    return o


def cam(loc, tgt, lens=55, ortho=None):
    c = dict(loc=loc, target=tgt, lens=lens)
    if ortho: c["ortho"] = ortho
    return c


L_C = [-5, -60, 200]; PAIR_C = [-195, -60, 200]
VIEWS = {
    "01_front_pair_off": (lamp("L") + lamp("R"), cam([-195, -1400, 260], PAIR_C, ortho=780), dict(world=0.45)),
    "02_front_pair_on": (lamp("L", on=True) + lamp("R", on=True), cam([-195, -1400, 260], PAIR_C, ortho=780), dict(world=0.02, light=0.04, bg=[0.02, 0.02, 0.03])),
    "03_three_quarter": (lamp("L"), cam([330, -620, 420], L_C, lens=55), {}),
    "04_rear_service": (lamp("L"), cam([-260, 560, 430], [-40, -40, 190], lens=50), {}),
    "05_top_aiming": (lamp("L"), cam([-5, -40, 1200], [-5, -40, 200], ortho=400), {}),
    "06_exploded": (lamp("L", explode=1.0), cam([-650, 420, 520], [-40, 40, 200], lens=45), dict(floor=False)),
    "07_devil_eye_closeup": (lamp("L", on=True), cam([170, -380, 230], [87, -60, 186], lens=85), dict(world=0.05, light=0.15)),
    "08_left_right_34": (lamp("L") + lamp("R"), cam([200, -900, 520], PAIR_C, lens=40), {}),
}


def main(names):
    tmp = RND / "_scenes"; tmp.mkdir(exist_ok=True)
    for name in names or VIEWS:
        objs, c, extra = VIEWS[name]
        sc = dict(out=str(RND / f"{name}.png"), res=[1600, 1000], samples=48, objects=objs, camera=c, **extra)
        j = tmp / f"{name}.json"; j.write_text(json.dumps(sc))
        r = subprocess.run([BPY, str(G.ROOT / "tools" / "render.py"), str(j)], capture_output=True, text=True)
        print(name, "ok" if r.returncode == 0 else r.stderr[-800:])


if __name__ == "__main__":
    main(sys.argv[2:])
