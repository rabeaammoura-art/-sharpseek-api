"""Verify the Mercedes tray from the generated files and the exact B-rep.

Checks: STL manifold/watertight per body, bed fit, print-in-place clearance (all body
pairs, STL meshes), extension travel without collisions, lip stop engagement, handle
sweep. Writes out/mercedes_verification.md. Exit code 1 if any check fails.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from build123d import Location, export_stl

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "parts"))
from _mercedes import P, handle, sector_face, tray_bodies  # noqa: E402

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


def main():
    # 1. STL files as delivered -----------------------------------------
    tray = trimesh.load(OUT / "mercedes_tray.stl", force="mesh")
    hnd = trimesh.load(OUT / "mercedes_tray_handle.stl", force="mesh")
    n_expected = 1 + 3 * P.n_rings
    for label, m, n_exp in (("tray", tray, n_expected), ("handle", hnd, 1)):
        parts = m.split(only_watertight=False)
        bad = [i for i, b in enumerate(parts) if not (b.is_watertight and b.is_winding_consistent and b.volume > 0)]
        check(f"STL {label}: separate bodies", len(parts) == n_exp, f"{len(parts)} bodies (expected {n_exp})")
        check(f"STL {label}: every body watertight, consistent winding, positive volume",
              not bad, f"{len(parts) - len(bad)}/{len(parts)} OK")
        ext = m.bounds[1] - m.bounds[0]
        fits = all(e <= b for e, b in zip(sorted(ext[:2]), sorted(BED[:2]))) and ext[2] <= BED[2]
        check(f"STL {label}: fits H2D safe area {BED[0]:.0f}x{BED[1]:.0f}x{BED[2]:.0f}", fits,
              f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, min z = {m.bounds[0][2]:.3f}")
        if label == "tray":
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

        # 3. extension travel: all-pairs mesh distance at intermediate states
        meshes0 = {n: mesh_of(s, tmp) for n, s in b0.items()}
        n = P.n_rings
        for e in (0.25, 0.5, 0.75, 0.98):
            dz = P.travel * e
            moved = {}
            for name, m in meshes0.items():
                k = 0 if name == "frame" else int(name.split("_r")[1])
                moved[name] = m.copy().apply_translation((0, 0, (n - k) * dz if k else n * dz))
            d, names = min_dist(moved)
            check(f"Travel {int(e * 100)}% extended: no collision", d > 0, f"min gap {d:.3f} mm ({names[0]} / {names[1]})")

        # 4. full extension: lips touch (stop engaged), no penetration ----
        b1 = tray_bodies(P, 1.0)
        touch = [b1[a].distance_to(b1[b]) for a, b in pairs]
        inter = [(b1[a] & b1[b]).volume for a, b in pairs]
        check("Fully extended: every lip pair in contact (stop engaged)", max(touch) < 1e-3,
              f"max distance {max(touch):.5f} mm")
        # Coincident 45° contact faces leave boolean noise; express it as a thickness over the
        # smallest contact face (innermost lip: perimeter x sloped overlap width).
        perim = sector_face(P, P.ring_inset(P.n_rings) - P.lip, th, 0).outer_wire().length
        eq = max(inter) / (perim * (P.lip - P.clear) * 2 ** 0.5)
        check("Fully extended: no interpenetration", eq < 1e-3,
              f"max boolean overlap {max(inter):.4f} mm^3 = {eq * 1000:.2f} um equivalent thickness (numerical contact noise)")
        # over-pull by 0.2 mm per step: must collide -> rings cannot separate
        over = tray_bodies(P, 1.0 + 0.2 / P.travel)
        ov = [(over[a] & over[b]).volume for a, b in pairs]
        check("Over-extension blocked by lips (0.2 mm extra pull -> collision)", min(ov) > 0,
              f"min overlap {min(ov):.2f} mm^3 per lip pair")
        depth = n * P.travel
        check("Extended depth / collapsed height", True,
              f"frame lifts {depth:.1f} mm; extended height {P.frame_h + depth:.1f} mm; "
              f"collapsed height {max(P.post_top, P.hinge_z + P.handle_t / 2):.1f} mm (posts / folded handle)")

        # 5. handle sweep vs frame (collapsed and extended) -------------
        fr0 = b0["frame"]
        worst = (1e9, None)
        for a in range(0, 181, 5):
            d = handle(P, a).distance_to(fr0)
            worst = min(worst, (d, a))
        check("Handle sweep 0..180 deg vs frame: no collision", worst[0] >= P.pin_clear - 1e-6,
              f"min gap {worst[0]:.3f} mm at {worst[1]} deg (pin clearance {P.pin_clear})")
        hm = mesh_of(handle(P, 0), tmp)
        cm = trimesh.collision.CollisionManager()
        for k, v in meshes0.items():
            if k != "frame":
                cm.add_object(k, v)
        d = cm.min_distance_single(hm)
        check("Handle folded vs rings", d > 0, f"min gap {d:.3f} mm")

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
