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
    part = {n: load(PARTS / f"{n}_L.stl") for n in
            ["projector_carrier", "pivot_cap", "wedge_A", "wedge_B", "inboard_bracket", "outboard_pillar",
             "devil_adapter", "devil_clamp", "PH_projector_ASSUMED", "PH_devil_eye_ASSUMED"]}
    a = G.aim_points(); f = G.projector_frame(); w = G.wedge_geom(); adj = G.adjusters()
    res = {"assumptions": "module envelopes are ASSUMED placeholders (params.py)", "checks": {}}
    C = res["checks"]
    TOL = 1.0   # mm3: below this an 'interference' is numerical contact

    # ---- 1. static interference (nominal aim) between every pair
    fixed = {"housing": H, **part}
    pairs = {}
    for (n1, m1), (n2, m2) in itertools.combinations(fixed.items(), 2):
        v = vol(m1 ^ m2)
        if v > TOL: pairs[f"{n1} x {n2}"] = round(v, 1)
    intended = {"devil_clamp x PH_devil_eye_ASSUMED": "0.2 mm clamp preload on the module flange (intended)"}
    C["static_interference_mm3"] = {k: (v, intended.get(k, "UNINTENDED")) for k, v in pairs.items()} or "none"

    # ---- 2. aiming sweep: moving set rotates about P (pitch about P-B, yaw about P-A)
    moving = part["projector_carrier"] + part["pivot_cap"] + part["PH_projector_ASSUMED"]
    # stat = H + part["inboard_bracket"] + part["outboard_pillar"] + part["wedge_A"] + part["wedge_B"]
    sweep = {}
    R_ = P.AIM_RANGE_DEG
    for pd, yd in itertools.product((-R_, 0, R_), repeat=2):
        Rm = rot(pd, yd)
        mv = xf(moving, Rm, a["P"])
        hits = {}
        for n, m in (("housing", H), ("inboard_bracket", part["inboard_bracket"]), ("outboard_pillar", part["outboard_pillar"])):
            v = vol(mv ^ m)
            if v > TOL: hits[n] = round(v, 1)
        # wedges follow the aim: wedge DOWN by d = follower (carrier) moves rearward (+Y) by d
        car = xf(part["projector_carrier"], Rm, a["P"])
        for n, pt in (("wedge_A", a["A"]), ("wedge_B", a["B"])):
            dy = float(((pt - a["P"]) @ Rm.T + a["P"] - pt)[1])
            v = vol(car ^ part[n].translate([0, 0, -dy]))
            if v > TOL: hits[n] = round(v, 1)
        sweep[f"pitch {pd:+.0f} / yaw {yd:+.0f}"] = hits or "clear"
    C["aim_sweep_interference_mm3"] = sweep

    # ---- 3. lens shroud vs aperture: min radial clearance of the shroud front rim over the sweep
    cx, cz = P.PROJ_C; r_s = P.PROJ_SHROUD_D / 2; r_a = P.PROJ_APERTURE_D / 2
    t = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    rim = np.stack([cx + r_s * np.cos(t), np.full_like(t, f["y_front"]), cz + r_s * np.sin(t)], 1)
    rim2 = rim.copy(); rim2[:, 1] = f["y_front"] + 8.0 + 0.0                    # collar rear end
    worst = 1e9
    for pd, yd in itertools.product(np.linspace(-R_, R_, 7), repeat=2):
        Rm = rot(pd, yd)
        for rr in (rim, rim2):
            q = (rr - a["P"]) @ Rm.T + a["P"]
            rad = np.hypot(q[:, 0] - cx, q[:, 2] - cz)
            worst = min(worst, r_a - rad.max())
    C["shroud_to_aperture_min_clearance_mm"] = round(worst, 2)

    # ---- 4. adjustment kinematics
    lever_A = a["A"][2] - a["P"][2]; lever_B = a["B"][0] - a["P"][0]
    trav_A = lever_A * math.tan(math.radians(R_)); trav_B = lever_B * math.tan(math.radians(R_))
    C["adjust"] = {
        "pitch_lever_mm": lever_A, "yaw_lever_mm": lever_B,
        "deg_per_turn_pitch(M5x0.8)": round(math.degrees(0.8 / lever_A), 3),
        "deg_per_turn_yaw(M5x0.8)": round(math.degrees(0.8 / lever_B), 3),
        "wedge_travel_needed_A_mm": round(trav_A, 2), "wedge_travel_needed_B_mm": round(trav_B, 2),
        "ramp_capacity_mm": w["ramp_half"],
        "ok": bool(trav_A <= w["ramp_half"] - 1 and trav_B <= w["ramp_half"] - 1),
        "coupling": "pitch axis = line P-B (horizontal), yaw axis = line P-A (vertical): first-order decoupled",
    }
    # wedge stays inside its channel over the travel
    br = part["inboard_bracket"]; pl = part["outboard_pillar"]
    tr = {}
    for n, host, need in (("wedge_A", br, trav_A), ("wedge_B", pl, trav_B)):
        bad = []
        for dz in (-need, need):
            v = vol(part[n].translate([0, 0, dz]) ^ host) + vol(part[n].translate([0, 0, dz]) ^ H)
            if v > TOL: bad.append((round(dz, 1), round(v, 1)))
        tr[n] = bad or "clear over full travel"
    C["wedge_travel_clearance"] = tr

    # ---- 5. top access: hex key (Ø10 sweep) straight down onto each adjuster head, nothing in the way
    acc = {}
    for k, (x, y) in adj.items():
        z_head = G.SEAT_Z
        tool = mf.Manifold.cylinder(400 - z_head - 6, 5.0, 5.0, 32).translate([x, y, z_head + 6])
        acc[k] = {"head_xyz": [round(x, 1), round(y, 1), z_head],
                  "tool_path_clear": vol(tool ^ H) < TOL,
                  "screw_length_min_mm": round(z_head - (a[k][2] + w["dz"] - w["below"]) + 2, 1)}
    # head seat: what is directly under the washer (ring r=4..6.5 mm around the screw), top-down
    seat_bodies = {"housing": H, "inboard_bracket": part["inboard_bracket"], "outboard_pillar": part["outboard_pillar"]}
    tms = {}
    for n, m in seat_bodies.items():
        o = m.to_mesh(); tms[n] = trimesh.Trimesh(np.asarray(o.vert_properties)[:, :3], np.asarray(o.tri_verts))
    for k, (x, y) in adj.items():
        hits = {}
        for ang in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            for rr in (4.0, 6.0):
                org = [[x + rr * np.cos(ang), y + rr * np.sin(ang), 400.0]]
                best = None
                for n, tm in tms.items():
                    loc, _, _ = tm.ray.intersects_location(org, [[0, 0, -1.0]], multiple_hits=False)
                    loc = np.asarray(loc).reshape(-1, 3)
                    if len(loc) and (best is None or loc[0, 2] > best[1]): best = (n, float(loc[0, 2]))
                key = f"{best[0]}@Z{best[1]:.1f}" if best else "NOTHING"
                hits[key] = hits.get(key, 0) + 1
        acc[k]["washer_seat_samples"] = hits
        acc[k]["seat_ok"] = all(not h.startswith("NOTHING") for h in hits) and len({h.split("@Z")[1] for h in hits}) <= 2
    C["top_access"] = acc

    # ---- 6. rear service: modules pulled straight back after unbolting
    rem = {}
    proj = part["PH_projector_ASSUMED"]; others = H + part["inboard_bracket"] + part["outboard_pillar"] + part["projector_carrier"] + part["pivot_cap"]
    hit = [d for d in range(4, 260, 4) if vol(proj.translate([0, d, 0]) ^ others) > TOL]
    rem["bi_led_projector (unbolt 3 screws, pull +Y)"] = "clear" if not hit else f"blocked at +{hit[0]} mm"
    dv = part["PH_devil_eye_ASSUMED"]; others2 = H + part["devil_adapter"]
    hit = [d for d in range(4, 260, 4) if vol(dv.translate([0, d, 0]) ^ others2) > TOL]
    rem["devil_eye (remove clamp ring, pull +Y)"] = "clear" if not hit else f"blocked at +{hit[0]} mm"
    C["rear_removal"] = rem

    # ---- 7. envelope check of the supplier-photo reading "124 mm tall"
    zf = np.array([P.BOTTOM_PLATE_TOP, P.TOP_PLATE_UNDERSIDE_FRONT])
    C["vertical_envelope_at_projector"] = {
        "floor_Z": P.BOTTOM_PLATE_TOP, "ceiling_Z_front": P.TOP_PLATE_UNDERSIDE_FRONT,
        "clear_height_mm": round(zf[1] - zf[0], 1),
        "max_module_height_with_±3deg_and_2mm_gaps_mm": round(zf[1] - zf[0] - 2 * 2 - 2 * 60 * math.tan(math.radians(R_)), 1),
        "if_module_is_124mm_tall": "DOES NOT FIT centred on Zc=%.1f" % cz,
    }
    (OUT / "validation.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
