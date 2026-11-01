"""print_test.py - generic pre-print simulation for ANY STL / 3MF (run after /3d-cost, before printing).

It does not slice. It re-creates the part layer by layer in Python and answers two questions:
  A) will the PRINT succeed?   mesh health, bed fit, floating islands / overhangs / bridges, thin features,
                                warping risk, first-layer stability
  B) will the PART hold?       cantilever stress on every cross-section (layer-bond direction) under a
                                handling load + own weight, tipping angle

Usage:
  python print_test.py part.stl other.3mf --filament PETG [--load 10] [--no-support] [--png report.png] [--json out.json]

Exit code: 0 = all OK/WARN, 2 = at least one FAIL.
All numbers are engineering estimates (screening), not a certified FEA. Limits are listed in the report.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import shapely
import trimesh
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

# ---------------------------------------------------------------- data
BED = (325.0, 320.0, 325.0)        # H2D effective single-nozzle volume (see PRINTING_NOTES.md)
TOWER_W = 14.0 + 5.0               # narrow prime tower + gap, reserved for multi-colour 3MF
NOZZLE = 0.4

# density g/cm3, tensile strength in XY (MPa, printed), warp factor
MATERIALS = {
    "PLA": dict(rho=1.24, xy=50.0, warp=0.5),
    "PETG": dict(rho=1.27, xy=45.0, warp=0.8),
    "ASA": dict(rho=1.07, xy=40.0, warp=1.5),
    "ABS": dict(rho=1.05, xy=40.0, warp=1.7),
    "PC": dict(rho=1.20, xy=60.0, warp=2.0),
    "TPU": dict(rho=1.21, xy=8.0, warp=0.2),
}
Z_KNOCKDOWN = 0.5                  # layer-bond strength is ~50 % of the in-plane strength
OK, WARN, FAIL = "OK", "WARN", "FAIL"
ICON = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}


class Report:
    def __init__(self, name):
        self.name, self.rows, self.facts = name, [], {}

    def add(self, status, check, detail, advice=""):
        self.rows.append(dict(status=status, check=check, detail=detail, advice=advice))

    @property
    def verdict(self):
        s = {r["status"] for r in self.rows}
        return FAIL if FAIL in s else WARN if WARN in s else OK


# ---------------------------------------------------------------- loading
def load_parts(path):
    """Return a list of (name, trimesh.Trimesh) bodies with transforms applied."""
    obj = trimesh.load(str(path))
    if isinstance(obj, trimesh.Scene):
        parts = [(f"{Path(path).stem}#{i + 1}", g) for i, g in enumerate(obj.dump(concatenate=False))]
    else:
        parts = [(Path(path).stem, obj)]
    out, seen = [], set()
    for n, g in parts:
        if not (isinstance(g, trimesh.Trimesh) and len(g.faces)):
            continue
        key = (len(g.faces), tuple(np.round(g.bounds.ravel(), 3)), round(float(g.area), 2))
        if key in seen:                              # the same mesh listed twice (colour slots / instances)
            continue
        seen.add(key)
        out.append((n, g))
    return out


def poly_list(g):
    if g is None or g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


# ---------------------------------------------------------------- slicing
def polygonize_parity(path):
    """Robust fallback: cells of the noded line arrangement that lie inside an odd number of loops."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    loops = [np.asarray(d) for d in path.discrete if len(d) >= 4]
    if not loops:
        return None
    rings = [Polygon(l).buffer(0) for l in loops]
    cells = list(polygonize(unary_union([LineString(l) for l in loops])))
    if not cells:
        return None
    pts = shapely.points(np.array([[c.representative_point().x, c.representative_point().y] for c in cells]))
    tree = shapely.STRtree([r for r in rings if not r.is_empty])
    _, ci = tree.query(pts, predicate="within")                 # (point, ring) pairs
    cnt = np.bincount(ci, minlength=len(cells)) if False else np.bincount(tree.query(pts, predicate="within")[0], minlength=len(cells))
    keep = [c for c, k in zip(cells, cnt) if k % 2 == 1]
    return unary_union(keep) if keep else None


def slice_layers(meshes, step):
    """Union cross-section polygon for each height. meshes: list of bodies (sliced separately, then unioned)."""
    z0 = min(m.bounds[0][2] for m in meshes)
    z1 = max(m.bounds[1][2] for m in meshes)
    zs = np.arange(z0 + step / 2, z1, step)
    if len(zs) == 0:
        zs = np.array([(z0 + z1) / 2])
    per_layer = [[] for _ in zs]
    for m in meshes:
        paths = m.section_multiplane(np.array([0, 0, 0.0]), np.array([0, 0, 1.0]), zs)
        for k, p in enumerate(paths):
            if p is None:
                continue
            try:
                per_layer[k] += [pg for pg in p.polygons_full if pg.is_valid and pg.area > 1e-6]
            except Exception:                          # non-manifold edges (touching colour shells): rebuild by parity
                g = polygonize_parity(p)
                if g is not None:
                    per_layer[k].append(g)
    return zs, [unary_union(l) if l else Polygon() for l in per_layer]


def moments(g):
    """Area, centroid and principal second moments (mm^4) of a polygon geometry (holes subtracted)."""
    A = Sx = Sy = Ixx = Iyy = Ixy = 0.0
    for pg in poly_list(g):
        for ring, sign in [(pg.exterior, 1.0)] + [(r, -1.0) for r in pg.interiors]:
            c = np.asarray(ring.coords)
            x, y = c[:-1, 0], c[:-1, 1]
            x1, y1 = c[1:, 0], c[1:, 1]
            cr = x * y1 - x1 * y
            a = cr.sum() / 2
            if a < 0:                      # normalise orientation so |sign| controls add / subtract
                cr, a = -cr, -a
            A += sign * a
            Sx += sign * ((x + x1) * cr).sum() / 6
            Sy += sign * ((y + y1) * cr).sum() / 6
            Ixx += sign * ((y * y + y * y1 + y1 * y1) * cr).sum() / 12
            Iyy += sign * ((x * x + x * x1 + x1 * x1) * cr).sum() / 12
            Ixy += sign * ((x * y1 + 2 * x * y + 2 * x1 * y1 + x1 * y) * cr).sum() / 24
    if A <= 1e-9:
        return 0.0, (0.0, 0.0), 0.0, np.array([1.0, 0.0])
    cx, cy = Sx / A, Sy / A
    Ixx_c, Iyy_c, Ixy_c = Ixx - A * cy * cy, Iyy - A * cx * cx, Ixy - A * cx * cy
    ev, vec = np.linalg.eigh(np.array([[Ixx_c, -Ixy_c], [-Ixy_c, Iyy_c]]))
    # bending about the weak principal axis (eigenvector 0); fibres lie along its perpendicular
    u = vec[:, 0]
    return A, (cx, cy), max(float(ev[0]), 1e-6), np.array([-u[1], u[0]])


# ---------------------------------------------------------------- checks
def check_health(rep, bodies):
    bad, notes = [], []
    for n, m in bodies:
        m = m.copy()
        issues = []
        if not m.is_watertight:
            issues.append("not watertight")
        if not m.is_winding_consistent:
            issues.append("inconsistent winding")
        deg = int((m.area_faces < 1e-9).sum())
        if deg:
            issues.append(f"{deg} degenerate faces")
        if m.is_watertight and m.volume <= 0:
            issues.append("negative volume (inverted normals)")
        if issues:
            bad.append(f"{n}: {', '.join(issues)}")
    tri = sum(len(m.faces) for _, m in bodies)
    if not bad:
        rep.add(OK, "Mesh health", f"{len(bodies)} body(ies), {tri:,} triangles, all closed")
    else:
        rep.add(WARN, "Mesh health", "; ".join(bad[:4]) + (" ..." if len(bad) > 4 else ""),
                "Slicers usually repair small defects, but open meshes (multi-colour layers excepted) can slice wrong: re-export or repair.")


def check_fit(rep, whole, multi, tower):
    ext = whole.extents
    tw = TOWER_W if (multi and tower is None) else (tower or 0.0)
    fits = (ext[2] <= BED[2]) and ((ext[0] + tw <= BED[0] and ext[1] <= BED[1]) or (ext[1] + tw <= BED[0] and ext[0] <= BED[1]))
    d = f"{ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm" + (f" + {tw:.0f} mm prime tower" if tw else "") + f" vs bed {BED[0]:.0f} x {BED[1]:.0f} x {BED[2]:.0f}"
    if fits:
        free = min(BED[0] - ext[0] - tw, BED[1] - ext[1])
        rep.add(OK if free > 4 else WARN, "Fits the bed", d + (f" (only {free:.1f} mm spare)" if free <= 4 else ""),
                "" if free > 4 else "Almost no margin: brim/skirt or the real tower position may not fit.")
    else:
        rep.add(FAIL, "Fits the bed", d, "Does not fit: scale down, split the part, or drop the prime tower (single colour).")


def check_layers(rep, zs, layers, step, angle, support, bridge_warn, bridge_fail, min_area):
    tol = step * math.tan(math.radians(angle))
    islands, regions = [], []
    unsupported_vol = 0.0
    prev = None
    for i, (z, g) in enumerate(zip(zs, layers)):
        if prev is not None and not g.is_empty:
            reach = prev.buffer(tol, resolution=4) if not prev.is_empty else Polygon()
            for pg in poly_list(g):
                if not pg.intersects(reach):
                    if pg.area >= min_area:
                        islands.append((z, pg.area, float(pg.centroid.x), float(pg.centroid.y)))
            un = g.difference(reach)
            for u in poly_list(un):
                if u.area >= min_area:
                    span = 2 * float(shapely.maximum_inscribed_circle(u, 0.1).length) if u.area > 0 else 0.0
                    regions.append((z, u.area, span, float(u.centroid.x), float(u.centroid.y)))
                    unsupported_vol += u.area * step
        prev = g
    max_span = max((r[2] for r in regions), default=0.0)
    n_isl = len({(round(i[2], 0), round(i[3], 0)) for i in islands})
    rep.facts.update(unsupported_cm3=unsupported_vol / 1000, max_span=max_span, islands=n_isl)

    if not regions and not islands:
        rep.add(OK, "Overhangs / bridges / islands", f"nothing exceeds {angle:.0f}° overhang: printable without supports")
        return regions, islands
    detail = (f"{len(regions)} overhang region(s), widest unsupported span {max_span:.1f} mm, "
              f"{n_isl} floating island(s), ~{unsupported_vol / 1000:.1f} cm³ of overhang area")
    if not support:
        st = FAIL if (max_span > bridge_fail or n_isl) else WARN if max_span > bridge_warn else OK
        rep.add(st, "Overhangs / bridges / islands (no supports)", detail,
                "Re-orient the part, add chamfers (<45°) or enable supports." if st != OK else "")
    else:
        st = WARN if (max_span > bridge_fail or n_isl or unsupported_vol / 1000 > 5) else OK
        rep.add(st, "Overhangs / bridges / islands (supports on)", detail,
                "Supports will carry it; expect rough underside and extra time. Reorienting may remove most of them." if st == WARN
                else "Small overhangs, supports (or bridging) will handle it.")
    return regions, islands


def check_thin(rep, zs, layers, sample=60):
    idx = np.unique(np.linspace(0, len(layers) - 1, min(sample, len(layers))).astype(int))
    tot = lost_fine = lost_single = 0.0
    worst_z, worst = None, 0.0
    for i in idx:
        g = layers[i]
        if g.is_empty:
            continue
        a = g.area
        o1 = g.buffer(-NOZZLE / 2, resolution=3).buffer(NOZZLE / 2, resolution=3).area
        o2 = g.buffer(-NOZZLE, resolution=3).buffer(NOZZLE, resolution=3).area
        tot += a
        lost_fine += max(a - o1, 0)
        lost_single += max(a - o2, 0)
        if a and (a - o1) / a > worst:
            worst, worst_z = (a - o1) / a, zs[i]
    if tot == 0:
        rep.add(WARN, "Thin features", "no cross-section found (empty model?)")
        return
    f1, f2 = 100 * lost_fine / tot, 100 * lost_single / tot
    rep.facts.update(thin_lt_nozzle_pct=f1, thin_single_wall_pct=f2)
    st = FAIL if f1 > 5 else WARN if f1 > 0.5 else OK
    d = f"{f1:.2f} % of the area is thinner than {NOZZLE} mm (will not print), {f2:.1f} % thinner than {2 * NOZZLE} mm (single wall, weak)"
    if worst_z is not None and worst > 0.005:
        d += f"; worst near z={worst_z:.1f} mm"
    rep.add(st, "Thin features", d, "Thicken walls/details to >= 0.8 mm (2 perimeters), or check the text/pins at that height." if st != OK else "")


def check_warp(rep, layers, mat, m_info):
    first = next((g for g in layers[:3] if not g.is_empty), Polygon())
    minx, miny, maxx, maxy = first.bounds if not first.is_empty else (0, 0, 0, 0)
    L = max(maxx - minx, maxy - miny)
    score = L * m_info["warp"]
    contact = first.area
    rep.facts.update(contact_cm2=contact / 100, footprint_len=L)
    st = FAIL if score >= 450 else WARN if score >= 150 else OK
    rep.add(st, f"Warping / bed adhesion ({mat})",
            f"first layer {L:.0f} mm long, contact {contact / 100:.1f} cm² (risk score {score:.0f}; <150 ok, >=450 high)",
            "Use brim (or mouse ears), textured PEI + glue, bed 100 °C, closed chamber, no draft; consider PLA/PETG instead." if st != OK else "")
    if contact < 50:
        rep.add(WARN, "Bed contact area", f"only {contact:.0f} mm² touches the bed", "Tiny first layer can detach: add a brim or a flat base.")


def check_stability(rep, whole, layers, step):
    first = next((g for g in layers[:3] if not g.is_empty), None)
    if first is None:
        return
    hull = first.convex_hull
    com = whole.center_mass if whole.is_watertight else whole.centroid
    h = float(com[2] - whole.bounds[0][2])
    H = float(whole.extents[2])
    pt = Point(com[0], com[1])
    short = 2 * float(shapely.maximum_inscribed_circle(hull, 0.1).length) if hull.area > 0 else 0
    aspect = H / max(short, 1e-6)
    if not hull.contains(pt):
        rep.add(FAIL, "Stability while printing", f"centre of mass is outside the first-layer footprint (height {H:.0f} mm)",
                "It will fall over / peel off the bed: re-orient, add a wide brim or a support base.")
        return
    d = hull.exterior.distance(pt)
    tip = math.degrees(math.atan2(d, max(h, 1e-6)))
    rep.facts.update(tip_angle=tip, aspect=aspect)
    st = FAIL if aspect > 10 else WARN if (aspect > 5 or tip < 8) else OK
    rep.add(st, "Stability (as oriented)", f"tips at {tip:.0f}° tilt, height/footprint ratio {aspect:.1f} (wobbles when > 5)",
            "Tall and thin: wide brim, lower speed/acceleration, or lay the part down." if st != OK else "")


def check_strength(rep, zs, layers, step, mat, m_info, load, fill, whole):
    allow = m_info["xy"] * Z_KNOCKDOWN                # MPa across layers
    rho = m_info["rho"] * 1e-3                         # g/mm3 -> use in N below
    weight_n = lambda vol_mm3: vol_mm3 * rho * fill * 1e-3 * 9.81     # N
    areas = np.array([g.area for g in layers])
    above = np.cumsum((areas * step)[::-1])[::-1]       # mm3 of material from slice upward
    ztop = float(whole.bounds[1][2])
    idx = np.unique(np.linspace(0, len(layers) - 1, min(80, len(layers))).astype(int))
    worst = (float("inf"), None, 0, 0)
    for i in idx:
        g = layers[i]
        if g.is_empty:
            continue
        A, c, Imin, nrm = moments(g)
        if A < 1e-6:
            continue
        # fibre distance: farthest boundary point from the centroid, measured across the weak bending axis
        pts = np.vstack([np.asarray(p.exterior.coords) for p in poly_list(g)])
        cmax = float(np.abs((pts[:, 0] - c[0]) * nrm[0] + (pts[:, 1] - c[1]) * nrm[1]).max())
        arm = max(ztop - zs[i], 0.0)
        M = load * arm                                  # N.mm
        sigma = M * cmax / Imin + weight_n(above[i]) / A
        sf = allow / sigma if sigma > 1e-9 else float("inf")
        if sf < worst[0]:
            worst = (sf, zs[i], sigma, A)
    sf, z, sigma, A = worst
    if z is None:
        return
    rep.facts.update(safety_factor=None if math.isinf(sf) else sf, weak_z=z)
    st = FAIL if sf < 1.5 else WARN if sf < 3 else OK
    sfs = "no significant stress" if math.isinf(sf) else f"safety factor {sf:.1f}"
    rep.add(st, f"Strength: {load:g} N sideways at the top",
            f"{sfs}; weakest section at z={z:.1f} mm (area {A:.0f} mm², {sigma:.2f} MPa vs {allow:.0f} MPa across layers in {mat})",
            "Thicken that section, add fillets/gussets, print it flat (layers along the load), or use a tougher material." if st != OK else "")


# ---------------------------------------------------------------- preview
def render_png(path, whole, angle):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    m = whole
    n = m.face_normals
    over = (n[:, 2] < -math.cos(math.radians(90 - angle)) * 0 - math.sin(math.radians(angle))) & \
           (m.triangles_center[:, 2] > m.bounds[0][2] + 0.3)
    idx = np.arange(len(m.faces))
    if len(idx) > 30000:
        idx = np.random.default_rng(0).choice(idx, 30000, replace=False)
    tri = m.triangles[idx]
    col = np.where(over[idx, None], np.array([[0.85, 0.15, 0.15, 1.0]]), np.array([[0.55, 0.65, 0.8, 1.0]]))
    fig = plt.figure(figsize=(11, 5))
    for k, (el, az) in enumerate([(25, -60), (-35, 30)]):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(tri, facecolors=col, edgecolors="none"))
        b = m.bounds
        c, r = b.mean(0), (b[1] - b[0]).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(el, az); ax.set_axis_off()
        ax.set_title("top view" if k == 0 else "underside (red = overhang needing support)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- main
def analyse(path, a):
    t0 = time.time()
    rep = Report(Path(path).name)
    bodies = load_parts(path)
    if not bodies:
        rep.add(FAIL, "Load", "no mesh found in file")
        return rep, None
    mat = a.filament.upper()
    m_info = MATERIALS[mat]
    whole = trimesh.util.concatenate([m for _, m in bodies])
    dz = -whole.bounds[0][2]                                        # drop onto the bed
    placed = [(n, m.copy()) for n, m in bodies]
    for _, m in placed:
        m.apply_translation([0, 0, dz])
    whole = whole.copy()
    whole.apply_translation([0, 0, dz])
    step = a.step or float(np.clip(whole.extents[2] / 250, 0.2, 0.6))
    rep.facts.update(layer_step=step, size=[round(float(x), 1) for x in whole.extents])
    check_health(rep, bodies)
    check_fit(rep, whole, len(bodies) > 1, a.tower)
    zs, layers = slice_layers([b for _, b in placed], step)
    check_layers(rep, zs, layers, step, a.angle, not a.no_support, a.bridge_warn, a.bridge_fail, a.min_area)
    check_thin(rep, zs, layers)
    check_warp(rep, layers, mat, m_info)
    check_stability(rep, whole, layers, step)
    check_strength(rep, zs, layers, step, mat, m_info, a.load, a.fill, whole)
    rep.facts["seconds"] = round(time.time() - t0, 1)
    return rep, whole


def print_report(rep, a):
    print(f"\n=== {rep.name}  ->  {ICON[rep.verdict]} {rep.verdict}   ({rep.facts.get('size')} mm, {a.filament.upper()}, {rep.facts.get('seconds', 0)} s)")
    for r in rep.rows:
        print(f" {ICON[r['status']]} {r['check']}: {r['detail']}")
        if r["advice"]:
            print(f"      -> {r['advice']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--filament", default="PLA", help="PLA | PETG | ASA | ABS | PC | TPU")
    ap.add_argument("--load", type=float, default=10.0, help="sideways handling force at the top of the part, N (default 10)")
    ap.add_argument("--fill", type=float, default=0.4, help="effective solid fraction for weight (walls+infill), default 0.4")
    ap.add_argument("--no-support", action="store_true", help="the part will be printed without supports")
    ap.add_argument("--angle", type=float, default=45.0, help="max overhang angle from vertical, degrees (default 45)")
    ap.add_argument("--bridge-warn", type=float, default=15.0)
    ap.add_argument("--bridge-fail", type=float, default=40.0)
    ap.add_argument("--min-area", type=float, default=1.0, help="ignore overhang patches smaller than this, mm2")
    ap.add_argument("--tower", type=float, default=None, help="prime tower width to reserve on the bed (mm); default auto for multi-body 3MF")
    ap.add_argument("--step", type=float, default=None, help="slice step, mm (default auto 0.2-0.6)")
    ap.add_argument("--png", help="write an overhang preview PNG (single file: that path; many files: suffixed)")
    ap.add_argument("--json", help="write the results as JSON")
    a = ap.parse_args()
    if a.filament.upper() not in MATERIALS:
        sys.exit(f"unknown filament {a.filament}; choose from {', '.join(MATERIALS)}")
    results, worst = [], OK
    for f in a.files:
        rep, whole = analyse(f, a)
        print_report(rep, a)
        results.append(rep)
        if a.png and whole is not None:
            out = a.png if len(a.files) == 1 else str(Path(a.png).with_name(f"{Path(a.png).stem}_{Path(f).stem}.png"))
            render_png(out, whole, a.angle)
            print(f"   preview: {out}")
        if rep.verdict == FAIL:
            worst = FAIL
        elif rep.verdict == WARN and worst == OK:
            worst = WARN
    if len(results) > 1:
        print("\nSummary:")
        for r in results:
            print(f" {ICON[r.verdict]} {r.name}")
    print("\nNot covered: fits/clearances between separate parts, dynamic/impact loads, creep and heat, slicer-specific behaviour.")
    if a.json:
        Path(a.json).write_text(json.dumps([dict(file=r.name, verdict=r.verdict, facts=r.facts, checks=r.rows) for r in results],
                                           indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    sys.exit(2 if worst == FAIL else 0)


if __name__ == "__main__":
    main()
