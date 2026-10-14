"""Engineering checks on the assembled LEFT headlight (right is an exact mirror).
Writes out/validation.json and prints a summary. Every check is geometric (manifold3d booleans)."""
import sys, json, itertools, math
from pathlib import Path
import numpy as np, trimesh, manifold3d as mf
sys.path.insert(0, str(Path(__file__).parent))
import params as P, geom as G

OUT = G.OUT; PARTS = OUT / "parts"


def load(path):
    t = trimesh.load(path)
    m = mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    assert m.status() == mf.Error.NoError, (path, m.status())
    return m


def xf(m, R, about, shift=(0, 0, 0)):
    """Rotate m by 3x3 R about point 'about', then translate."""
    a = np.asarray(about, float)
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = a - R @ a + np.asarray(shift)
    return m.transform(T[:3, :].T.tolist() if False else [list(T[0, :]), list(T[1, :]), list(T[2, :])])


def rot(pitch_deg, yaw_deg):
    p, y = math.radians(pitch_deg), math.radians(yaw_deg)
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    return Rz @ Rx


def vol(m):
    return 0.0 if m.is_empty() else m.volume()


def main():
    H = load(OUT / "housing_L_mod.stl")
    part = {n: load(PARTS / f"{n}_L.stl") for n in ["projector_carrier", "devil_clamp", "PH_projector_ASSUMED", "PH_devil_eye_ASSUMED"]}
    a = G.aim_points(); f = G.projector_frame(); posts = G.aim_posts(); sp = P.AIM_SPRING
    res = {"design": "v2 simplified: housing + carrier + devil clamp per lamp; 3 spring screws from the rear",
           "assumptions": "module envelopes are ASSUMED placeholders (params.py)", "checks": {}}
    C = res["checks"]; TOL = 1.0
    fixed = {"housing": H, **part}
    intended = {"devil_clamp x PH_devil_eye_ASSUMED": "0.2 mm clamp preload on the module flange (intended)"}
    pairs = {}
    for (n1, m1), (n2, m2) in itertools.combinations(fixed.items(), 2):
        v = vol(m1 ^ m2)
        if v > TOL: pairs[f"{n1} x {n2}"] = (round(v, 1), intended.get(f"{n1} x {n2}", "UNINTENDED"))
    C["static_interference_mm3"] = pairs or "none"
    moving = part["projector_carrier"] + part["PH_projector_ASSUMED"]
    R_ = P.AIM_RANGE_DEG; sweep = {}
    for pd, yd in itertools.product(np.linspace(-R_, R_, 5), repeat=2):
        v = vol(xf(moving, rot(pd, yd), a["P"]) ^ H)
        sweep[f"pitch {pd:+.1f} / yaw {yd:+.1f}"] = round(v, 1) if v > TOL else "clear"
    C["aim_sweep_vs_housing_mm3"] = sweep
    cx, cz = P.PROJ_C; r_s = P.PROJ_SHROUD_D / 2; r_a = P.PROJ_APERTURE_D / 2
    t = np.linspace(0, 2 * np.pi, 180, endpoint=False); worst = 1e9
    for yy in (f["y_front"], f["y_front"] + 8.0):
        rim = np.stack([cx + r_s * np.cos(t), np.full_like(t, yy), cz + r_s * np.sin(t)], 1)
        for pd, yd in itertools.product(np.linspace(-R_, R_, 7), repeat=2):
            q = (rim - a["P"]) @ rot(pd, yd).T + a["P"]
            worst = min(worst, r_a - np.hypot(q[:, 0] - cx, q[:, 2] - cz).max())
    C["shroud_to_aperture_min_clearance_mm"] = round(worst, 2)
    lev_A = a["A"][2] - a["P"][2]; lev_B = a["B"][0] - a["P"][0]
    tA = lev_A * math.tan(math.radians(R_)); tB = lev_B * math.tan(math.radians(R_))
    C["adjust"] = {"pitch_screw": "A", "yaw_screw": "B", "reference": "P",
                   "deg_per_turn_pitch(M5x0.8)": round(math.degrees(0.8 / lev_A), 3),
                   "deg_per_turn_yaw(M5x0.8)": round(math.degrees(0.8 / lev_B), 3),
                   "spring_length_range_A_mm": [round(sp["l_installed"] - tA, 1), round(sp["l_installed"] + tA, 1)],
                   "spring_length_range_B_mm": [round(sp["l_installed"] - tB, 1), round(sp["l_installed"] + tB, 1)],
                   "spring_free_length_mm": sp["l_free"],
                   "ok": bool(sp["l_installed"] + tB < sp["l_free"] - 2 and sp["l_installed"] - tB > 6.0)}
    acc = {}
    for k, (x, y_end, z) in posts.items():
        tool = cyl(x, z, 5.0, f["y_mount"] + 6.0, 120.0)
        acc[k] = {"head_xyz": [round(x, 1), round(f["y_mount"], 1), round(z, 1)],
                  "rear_tool_path_vs_housing_mm3": round(vol(tool ^ H), 1),
                  "rear_tool_path_vs_projector_mm3": round(vol(tool ^ part["PH_projector_ASSUMED"]), 1)}
    C["rear_screwdriver_access"] = acc
    rem = {}
    others = H + part["projector_carrier"]
    hit = [d for d in range(4, 260, 4) if vol(part["PH_projector_ASSUMED"].translate([0, d, 0]) ^ others) > TOL]
    rem["bi_led_projector (unbolt 3 screws, pull +Y)"] = "clear" if not hit else f"blocked at +{hit[0]} mm"
    hit = [d for d in range(4, 260, 4) if vol(part["PH_devil_eye_ASSUMED"].translate([0, d, 0]) ^ H) > TOL]
    rem["devil_eye (remove clamp ring, pull +Y)"] = "clear" if not hit else f"blocked at +{hit[0]} mm"
    C["rear_removal"] = rem
    (OUT / "validation.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))


def cyl(x, z, r, y0, y1):
    return mf.Manifold.cylinder(y1 - y0, r, r, 32).rotate([-90, 0, 0]).translate([x, y0, z])


if __name__ == "__main__":
    main()
