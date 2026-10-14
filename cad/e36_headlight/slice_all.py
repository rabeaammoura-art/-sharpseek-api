"""Slice every printed part with PrusaSlicer (approximate H2D/ASA-CF profile) and collect real slicer output.
For small parts each of 6 axis-aligned orientations is sliced and the fastest is kept.
Support share = (mass with supports) - (mass without supports), same orientation."""
import sys, re, json, subprocess, itertools, tempfile
from pathlib import Path
import numpy as np, trimesh
sys.path.insert(0, str(Path(__file__).parent))
OUT = Path(__file__).parent / "out"; GC = OUT / "gcode"; GC.mkdir(parents=True, exist_ok=True)
INI = Path(__file__).parent / "config" / "h2d_asacf_0.20.ini"
BED = (325.0, 320.0)


def run(stl, gcode, extra=()):
    cmd = ["prusa-slicer", "--export-gcode", "--load", str(INI), *extra, "--center", f"{BED[0]/2},{BED[1]/2}", "-o", str(gcode), str(stl)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if r.returncode != 0 or not gcode.exists():
        return None
    txt = gcode.read_text(errors="ignore")[-20000:]
    g = re.search(r"; total filament used \[g\] = ([\d.]+)", txt) or re.search(r"; filament used \[g\] = ([\d.]+)", txt)
    cm3 = re.search(r"; filament used \[cm3\] = ([\d.]+)", txt)
    t = re.search(r"; estimated printing time \(normal mode\) = (.+)", txt)
    cost = re.search(r"; total filament cost = ([\d.]+)", txt)
    secs = 0
    for v, u in re.findall(r"(\d+)([dhms])", t.group(1)):
        secs += int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
    return dict(g=float(g.group(1)), cm3=float(cm3.group(1)), time_s=secs, time=t.group(1).strip(), cost=float(cost.group(1)) if cost else None)


def orient(mesh, R):
    m = mesh.copy(); T = np.eye(4); T[:3, :3] = R; m.apply_transform(T); m.apply_translation(-m.bounds[0]); return m


ROTS = {"+Z up": np.eye(3), "-Z up": np.diag([1, -1, -1]),
        "+Y up": np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]), "-Y up": np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]),
        "+X up": np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]), "-X up": np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])}


def main():
    res = {}
    tmp = Path(tempfile.mkdtemp())
    # housing: natural orientation (bottom plate on the bed), rotated about Z to fit 325 x 320
    h = trimesh.load(OUT / "housing_L_mod.stl")
    a = np.radians(16.0); Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    hm = orient(h, Rz); p = tmp / "housing.stl"; hm.export(p)
    print("housing footprint after 16 deg Z rotation:", (hm.bounds[1] - hm.bounds[0]).round(1))
    s = run(p, GC / "housing_L_mod.gcode"); n = run(p, tmp / "h_nosup.gcode", ["--no-support-material"]) if s else None
    res["housing_L_mod"] = dict(orientation="bottom plate on bed, rotated 16 deg about Z", **(s or {"error": "slice failed"}),
                                support_g=round(s["g"] - n["g"], 1) if s and n else None)
    print("housing", res["housing_L_mod"])
    for name in ["projector_carrier", "pivot_cap", "wedge_A", "wedge_B", "inboard_bracket", "outboard_pillar", "devil_adapter", "devil_clamp"]:
        mesh = trimesh.load(OUT / "parts" / f"{name}_L.stl"); best = None
        for k, R in ROTS.items():
            m = orient(mesh, R); q = tmp / f"{name}_{k[0]}{k[1]}.stl"; m.export(q)
            r = run(q, tmp / "x.gcode")
            if r and (best is None or r["time_s"] < best[1]["time_s"]): best = (k, r, q)
        k, r, q = best
        run(q, GC / f"{name}_L.gcode"); n = run(q, tmp / "n.gcode", ["--no-support-material"])
        res[name] = dict(orientation=k, **r, support_g=round(r["g"] - n["g"], 1) if n else None)
        print(name, res[name])
    (OUT / "slicing.json").write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
