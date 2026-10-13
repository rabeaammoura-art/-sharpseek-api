"""Verify the Mercedes tray from the generated files and the exact B-rep.

Checks: STL manifold/watertight per body, bed fit, print-in-place clearance (all body
pairs, STL meshes), extension travel without collisions, lip stop engagement, handle
sweep, opening kinematics on the base, over-centre stop. Writes out/mercedes_verification.md. Exit code 1 if any check fails.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from build123d import Location, export_stl

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parts"))
from _mercedes import P, assembly, frame, frame_lift, handle, sector_face, solve_pocket, tray_bodies  # noqa: E402

OUT = ROOT / "out"
BED = (300.0, 320.0, 325.0)
TOL = 0.01  # STL chord tolerance is 0.005 mm; faceting may close a gap by up to ~0.01 mm
results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def mesh_of(shape, tmp):
    f = Path(tmp) / "m.stl"
    export_stl(shape, str(f), tolerance=0.005, angular_tolerance=0.05)
    return trimesh.load(f, force="mesh")


def min_dist(meshes: dict):
    cm = trimesh.collision.CollisionManager()
    for n, m in meshes.items():
        cm.add_object(n, m)
    d, names = cm.min_distance_internal(return_names=True)
    return d, names


def gcode_check(path=OUT / "mercedes_tray.gcode", centre=(162.5, 160.0), w=0.42):
    """Gaps between neighbouring bodies as actually sliced: external perimeters crossing a line
    0.37 mm off the bisector of compartment 270 (it runs along -Y from the tray centre)."""
    if not path.exists():
        check("G-code gaps", False, f"{path.name} missing - run make mercedes first")
        return
    import re
    cx, cy = centre[0] + 0.37, centre[1]
    layers, z, x, y, typ = {}, 0.0, 0.0, 0.0, ""
    for line in open(path):
        if line.startswith(";Z:"):
            z = round(float(line[3:]), 2)
        elif line.startswith(";TYPE:"):
            typ = line[6:].strip()
        elif line.startswith("G1"):
            m = dict(re.findall(r"([XYE])([-\d.]+)", line))
            nx, ny = float(m.get("X", x)), float(m.get("Y", y))
            if "E" in m and float(m["E"]) > 0 and typ == "External perimeter":
                layers.setdefault(z, []).append((x, y, nx, ny))
            x, y = nx, ny
    y_floor = -(P.r_sector - P.ring_inset(P.n_rings))
    for zl, what in ((0.2, "first layer (elephant-foot comp. 0.15)"), (0.4, "bottom lips"),
                     (P.ring_h - 0.2, "top lips")):
        h = sorted(y1 + (cx - x1) / (x2 - x1) * (y2 - y1) - cy
                   for x1, y1, x2, y2 in layers[zl] if (x1 - cx) * (x2 - cx) < 0)
        h = [v for v in h if -P.r_sector < v < y_floor + 0.5]  # frame edge .. floor ring
        # h[0] = frame opening, then (outer, inner) boundary pairs of rings 1..N-1
        gaps = [h[i + 1] - h[i] - w for i in range(0, len(h) - 1, 2)]
        check(f"G-code {what}, z={zl}: body-to-body gaps after slicing", min(gaps) >= P.clear - 0.05,
              f"{len(gaps)} gaps, min {min(gaps):.2f} / max {max(gaps):.2f} mm")


def overlap(a, b):
    return (a & b).volume


def main():
    # 1. STL files as delivered -----------------------------------------
    tray = trimesh.load(OUT / "mercedes_tray.stl", force="mesh")
    bse = trimesh.load(OUT / "mercedes_base.stl", force="mesh")
    n_expected = 2 + 3 * P.n_rings  # frame + handle + rings
    for label, m, n_exp in (("tray (one print, in place)", tray, n_expected), ("base", bse, 1)):
        parts = m.split(only_watertight=False)
        bad = [i for i, b in enumerate(parts) if not (b.is_watertight and b.is_winding_consistent and b.volume > 0)]
        check(f"STL {label}: separate bodies", len(parts) == n_exp, f"{len(parts)} bodies (expected {n_exp})")
        check(f"STL {label}: every body watertight, consistent winding, positive volume",
              not bad, f"{len(parts) - len(bad)}/{len(parts)} OK")
        ext = m.bounds[1] - m.bounds[0]
        fits = all(e <= b for e, b in zip(sorted(ext[:2]), sorted(BED[:2]))) and ext[2] <= BED[2]
        check(f"STL {label}: fits H2D safe area {BED[0]:.0f}x{BED[1]:.0f}x{BED[2]:.0f}", fits,
              f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, min z = {m.bounds[0][2]:.3f}")
        if label.startswith("tray"):
            d, names = min_dist({f"b{i}": b for i, b in enumerate(parts)})
            check("STL tray: min gap between any two bodies (print-in-place)", d >= P.clear - TOL,
                  f"{d:.3f} mm (design {P.clear} mm; STL faceting allowance {TOL} mm)")

    with tempfile.TemporaryDirectory() as tmp:
        # 2. exact B-rep clearances, collapsed ---------------------------
        b0 = tray_bodies(P, 0.0)
        th = int(P.compartment_angles[0])
        pairs = [("frame", f"c{th}_r01")] + [(f"c{th}_r{k:02d}", f"c{th}_r{k + 1:02d}") for k in range(1, P.n_rings)]
        gaps = [b0[a].distance_to(b0[b]) for a, b in pairs]
        check("B-rep collapsed: gap frame/ring/ring... (one compartment, all are identical by rotation)",
              min(gaps) >= P.clear - 1e-6, f"min {min(gaps):.4f}, max {max(gaps):.4f} mm")
        fr = frame(P)
        d = handle(P, 0).distance_to(fr)
        check("B-rep collapsed: handle ring + pins vs frame", d >= P.clear - 1e-6,
              f"{d:.4f} mm (pin in hole {P.pin_clear}, ring gap {P.handle_gap})")

        # 3. ring travel: all-pairs mesh distance at intermediate states
        meshes0 = {n: mesh_of(s, tmp) for n, s in b0.items()}
        n = P.n_rings
        for e in (0.25, 0.5, 0.75, 0.98):
            dz = P.travel * e
            moved = {}
            for name, m in meshes0.items():
                k = 0 if name == "frame" else int(name.split("_r")[1])
                moved[name] = m.copy().apply_translation((0, 0, (n - k) * dz if k else n * dz))
            d, names = min_dist(moved)
            check(f"Rings {int(e * 100)}% extended: no collision", d > 0, f"min gap {d:.3f} mm ({names[0]} / {names[1]})")
        b1 = tray_bodies(P, 1.0)
        touch = [b1[a].distance_to(b1[b]) for a, b in pairs]
        inter = [overlap(b1[a], b1[b]) for a, b in pairs]
        check("Rings fully extended: every lip pair in contact (stop engaged)", max(touch) < 1e-3,
              f"max distance {max(touch):.5f} mm")
        perim = sector_face(P, P.ring_inset(P.n_rings) - P.lip, th, 0).outer_wire().length
        eq = max(inter) / (perim * (P.lip - P.clear) * 2 ** 0.5)
        check("Rings fully extended: no interpenetration", eq < 1e-3,
              f"max boolean overlap {max(inter):.4f} mm^3 = {eq * 1000:.2f} um equivalent thickness (numerical contact noise)")
        over = tray_bodies(P, 1.0 + 0.2 / P.travel)
        ov = [overlap(over[a], over[b]) for a, b in pairs]
        check("Rings cannot separate: 0.2 mm extra pull collides at every lip", min(ov) > 0,
              f"min overlap {min(ov):.2f} mm^3 per lip pair")

        # 4. handle rotation relative to the frame (hinge sweep) ----------
        worst = (1e9, None)
        for a in np.arange(0, P.stop_deg + 0.1, 2.5):
            worst = min(worst, (handle(P, float(a)).distance_to(fr), float(a)))
        check(f"Hinge sweep 0..{P.stop_deg:.0f} deg: handle never touches the frame", worst[0] >= 0.3,
              f"min gap {worst[0]:.3f} mm at {worst[1]:.1f} deg")

        # 5. physical opening on the base ---------------------------------
        lifts = {a: frame_lift(P, a) for a in np.arange(0, P.stop_deg + 0.01, 0.5)}
        a_max = max(lifts, key=lifts.get)
        check("Lifting: the handle's legs raise the frame", lifts[P.stop_deg] > 0,
              f"lift {lifts[45.0]:.1f} mm at 45 deg, {lifts[90.0]:.1f} mm at 90 deg, "
              f"{lifts[P.stop_deg]:.2f} mm at the stop ({P.stop_deg:.0f} deg); rings need {P.lift:.2f}")
        check("Open on the base: rings fully extended, floors resting on the base",
              abs(lifts[P.stop_deg] - P.lift) < 0.2,
              f"last lip gap {P.lift - lifts[P.stop_deg]:.2f} mm (floors carry the food straight to the base)")
        a_pk = max((a for a in lifts if a >= 70), key=lifts.get)
        check("Over-centre lock: past the peak the frame sinks toward the stop, so the weight holds the handle against it",
              a_pk < P.stop_deg - 2 and lifts[P.stop_deg - 2] > lifts[P.stop_deg],
              f"peak {lifts[a_pk]:.2f} mm at {a_pk:.1f} deg -> {lifts[P.stop_deg]:.2f} mm at the stop; "
              f"to close, the handle must raise the loaded frame {lifts[a_pk] - lifts[P.stop_deg]:.2f} mm first (weight alone cannot)")
        px, py = solve_pocket(P)
        check("Pocket in the model matches the foot's swept footprint (80 deg..stop)",
              max(abs(px[0] - P.pocket_x[0]), abs(px[1] - P.pocket_x[1]), abs(py[0] - P.pocket_y[0]), abs(py[1] - P.pocket_y[1])) < 0.02,
              f"solved {px} {py}, model {P.pocket_x} {P.pocket_y}")
        poses = [0, 20, 45, 70, 76, 78, 80, 85, 90, 95, P.stop_deg]
        worst_h, worst_b = 1e9, 0.0
        for a in poses:
            asm = assembly(P, float(a))
            ms = {k: mesh_of(v, tmp) for k, v in asm.items() if k.startswith("c") or k == "handle"}
            cm = trimesh.collision.CollisionManager()
            for k, m in ms.items():
                if k != "handle":
                    cm.add_object(k, m)
            worst_h = min(worst_h, cm.min_distance_single(ms["handle"]))
            pen = max(overlap(asm["base"], asm[k]) for k in ("frame", "handle", f"c{th}_r{P.n_rings:02d}"))
            worst_b = max(worst_b, pen)
        check("Opening poses 0..stop: handle/legs never touch any ring", worst_h > 0, f"min gap {worst_h:.2f} mm")
        check("Opening poses 0..stop: nothing sinks into the base (feet and floors only touch it)",
              worst_b < 0.05, f"max overlap {worst_b:.4f} mm^3 (contact noise)")
        asm = assembly(P, P.stop_deg)
        a2 = P.stop_deg + 2.0
        h2 = handle(P, a2).moved(Location((0, 0, frame_lift(P, P.stop_deg))))
        check(f"Stop: turning 2 deg past {P.stop_deg:.0f} drives the leg into the pocket wall",
              overlap(h2, asm["base"]) > 1.0, f"overlap {overlap(h2, asm['base']):.1f} mm^3 -> rotation blocked")
        check("Heights", True, f"collapsed {P.frame_h:.0f} mm (+{P.base_t:.0f} mm base); open: frame top "
              f"{lifts[P.stop_deg] + P.frame_h:.1f} mm above the base, compartments {P.lift:.1f} mm deep; "
              f"handle top {lifts[P.stop_deg] + P.hinge_z + P.handle_r1:.0f} mm")

    gcode_check()
    lines = ["# Mercedes tray — verification report", "",
             "Generated by `cad/verify_mercedes.py` from `out/mercedes_tray.stl`, "
             "`out/mercedes_tray_handle.stl` and the exact B-rep.", "",
             "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {n} | {'PASS' if ok else 'FAIL'} | {d} |" for n, ok, d in results]
    (OUT / "mercedes_verification.md").write_text("\n".join(lines) + "\n")
    return all(ok for _, ok, _ in results)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
