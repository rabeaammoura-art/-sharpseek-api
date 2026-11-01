"""print_test.py - generic pre-print simulation for ANY STL / 3MF (run after /3d-cost, before printing).

It does not slice (that is /3d-cost: bed fit, supports, time, cost). It answers two questions in Python:

  1. Will the PRINT succeed?   mesh health, features too thin to print, warping / bed adhesion, stability
  2. Will the PRINTED PART work as designed?
        - every pair of bodies in the file (separate parts of an assembly, or the pin and the hole of a
          print-in-place joint) is measured; the gap is then re-computed as the printer will really make it
          (holes print smaller, walls wider, elephant foot, layer steps) as a best..worst range
        - verdict per pair: fits/moves | jams or FUSES | undecided (depends on the printer)
        - hinges (coaxial pin/hole) are turned through their range, sliding joints are slid, with the worst-case gap
        - cantilever strength of the part under a handling load

Usage:  python print_test.py file.stl|file.3mf ... [--filament PETG] [--profile cad/config/printer_profile.json]
Exit code 0 = no FAIL, 2 = at least one FAIL.  All numbers are engineering estimates: the printer profile holds
estimates from public reports until it is calibrated by measuring a printed test piece.
"""
import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import shapely
import trimesh
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

HERE = Path(__file__).parent
NOZZLE = 0.4
MATERIALS = {                       # density g/cm3, tensile strength in the layer plane (MPa), warp factor
    "PLA": dict(rho=1.24, xy=50.0, warp=0.5),
    "PETG": dict(rho=1.27, xy=45.0, warp=0.8),
    "ASA": dict(rho=1.07, xy=40.0, warp=1.5),
    "ABS": dict(rho=1.05, xy=40.0, warp=1.7),
    "PC": dict(rho=1.20, xy=60.0, warp=2.0),
    "TPU": dict(rho=1.21, xy=8.0, warp=0.2),
}
Z_KNOCKDOWN = 0.5                   # layer-bond strength is ~50 % of the in-plane strength
OK, WARN, FAIL = "OK", "WARN", "FAIL"
ICON = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}

DEFAULT_PROFILE = {
    "_note": "ESTIMATES from public forum reports, NOT measured on this printer. Replace after printing a test piece "
             "and measuring it with calipers; then set calibrated=true.",
    "calibrated": False,
    "outer_growth": [-0.05, 0.08],      # mm per side an OUTER wall moves into the gap, best .. worst
    "hole_growth": [-0.05, 0.15],       # mm per side the wall of a HOLE / socket moves into the gap, best .. worst
    "z_growth": [0.0, 0.15],            # mm a gap closes in the vertical direction (layer steps, bridge sag)
    "elephant_foot": 0.10,              # extra mm per side on the first `elephant_z` mm of the part (worst case)
    "elephant_z": 0.8,
    "free_gap": 0.15,                   # printed gap that still moves/fits in the WORST case
    "fuse_gap": 0.05,                   # if even the BEST case is at or below this, it fuses / jams
    "loose_gap": 1.5,                   # nominal gap above this: wobbly, not a precision fit
    "pair_distance": 3.0,               # bodies closer than this (mm) are treated as interacting
    "min_volume": 50.0,                 # ignore specks smaller than this (mm3): they are not mating parts
}


def load_profile(path):
    p = dict(DEFAULT_PROFILE)
    f = Path(path) if path else HERE / "config" / "printer_profile.json"
    if f.exists():
        p.update(json.loads(f.read_text(encoding="utf-8")))
    return p


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
def shell_volume(s):
    return abs(s.volume) if s.is_watertight else float(s.convex_hull.volume) * 0.5


def load_bodies(path, min_volume):
    """Meshes of the file + all separate shells inside them (a 3MF's objects AND disconnected shells: print-in-place)."""
    obj = trimesh.load(str(path))
    geoms = obj.dump(concatenate=False) if isinstance(obj, trimesh.Scene) else [obj]
    raw = [g for g in geoms if isinstance(g, trimesh.Trimesh) and len(g.faces)]
    meshes, shells, seen = [], [], set()
    for g in raw:
        key = (len(g.faces), tuple(np.round(g.bounds.ravel(), 3)), round(float(g.area), 2))
        if key in seen:                                  # the same mesh listed twice (colour slots / instances)
            continue
        seen.add(key)
        meshes.append(g)
        for s in g.split(only_watertight=False):
            if len(s.faces) >= 4 and shell_volume(s) >= min_volume:
                s.metadata["obj"] = len(meshes) - 1      # shells of one object may merge; different objects stay separate parts
                shells.append(s)
    return meshes, shells


def poly_list(g):
    if g is None or g.is_empty:
        return []
    return list(g.geoms) if hasattr(g, "geoms") else [g]


# ---------------------------------------------------------------- slicing (print + strength checks)
def _parity_job(loops):
    """Cells of the noded line arrangement lying inside an odd number of loops -> WKB (robust on non-manifold edges)."""
    loops = [np.asarray(l) for l in loops if len(l) >= 4]
    if not loops:
        return None
    rings = [Polygon(l).buffer(0) for l in loops]
    cells = list(polygonize(unary_union([LineString(l) for l in loops])))
    if not cells:
        return None
    pts = shapely.points(np.array([[c.representative_point().x, c.representative_point().y] for c in cells]))
    tree = shapely.STRtree([r for r in rings if not r.is_empty])
    cnt = np.bincount(tree.query(pts, predicate="within")[0], minlength=len(cells))
    keep = [c for c, k in zip(cells, cnt) if k % 2 == 1]
    return shapely.to_wkb(unary_union(keep)) if keep else None


def slice_layers(meshes, step):
    z0 = min(m.bounds[0][2] for m in meshes)
    z1 = max(m.bounds[1][2] for m in meshes)
    zs = np.arange(z0 + step / 2, z1, step)
    if len(zs) == 0:
        zs = np.array([(z0 + z1) / 2])
    loops = [[] for _ in zs]
    for m in meshes:
        for k, p in enumerate(m.section_multiplane(np.array([0, 0, 0.0]), np.array([0, 0, 1.0]), zs)):
            if p is not None:
                loops[k] += [np.asarray(d) for d in p.discrete]
    if len(loops) > 6:
        with ProcessPoolExecutor(max_workers=min(4, len(loops))) as ex:
            res = list(ex.map(_parity_job, loops, chunksize=2))
    else:
        res = [_parity_job(j) for j in loops]
    return zs, [shapely.from_wkb(r) if r else Polygon() for r in res]


def moments(g):
    """Area, centroid, weak principal second moment (mm^4) and fibre direction of a polygon geometry."""
    A = Sx = Sy = Ixx = Iyy = Ixy = 0.0
    for pg in poly_list(g):
        for ring, sign in [(pg.exterior, 1.0)] + [(r, -1.0) for r in pg.interiors]:
            c = np.asarray(ring.coords)
            x, y, x1, y1 = c[:-1, 0], c[:-1, 1], c[1:, 0], c[1:, 1]
            cr = x * y1 - x1 * y
            a = cr.sum() / 2
            if a < 0:
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
    u = vec[:, 0]
    return A, (cx, cy), max(float(ev[0]), 1e-6), np.array([-u[1], u[0]])


# ---------------------------------------------------------------- 1. will the print succeed
def check_health(rep, meshes, shells):
    bad = []
    for i, m in enumerate(meshes):
        issues = []
        if not m.is_watertight:
            issues.append("not watertight")
        if not m.is_winding_consistent:
            issues.append("inconsistent winding")
        deg = int((m.area_faces < 1e-9).sum())
        if deg:
            issues.append(f"{deg} degenerate faces")
        if m.is_watertight and m.volume <= 0:
            issues.append("inverted normals")
        if issues:
            bad.append(f"mesh {i + 1}: {', '.join(issues)}")
    tri = sum(len(m.faces) for m in meshes)
    if not bad:
        rep.add(OK, "Mesh health", f"{len(meshes)} mesh(es), {len(shells)} shell(s), {tri:,} triangles, all closed")
    else:
        rep.add(WARN, "Mesh health", "; ".join(bad[:4]),
                "Open meshes can slice wrong: re-export or repair (multi-colour 3MF layers are often like this and usually fine).")


def check_thin(rep, zs, layers, sample=40):
    idx = np.unique(np.linspace(0, len(layers) - 1, min(sample, len(layers))).astype(int))
    tot = lost1 = lost2 = 0.0
    worst_z, worst = None, 0.0
    for i in idx:
        g = layers[i]
        if g.is_empty:
            continue
        a = g.area
        o1 = g.buffer(-NOZZLE / 2, resolution=3).buffer(NOZZLE / 2, resolution=3).area
        o2 = g.buffer(-NOZZLE, resolution=3).buffer(NOZZLE, resolution=3).area
        tot += a
        lost1 += max(a - o1, 0)
        lost2 += max(a - o2, 0)
        if a and (a - o1) / a > worst:
            worst, worst_z = (a - o1) / a, zs[i]
    if tot == 0:
        rep.add(WARN, "Thin features", "no cross-section found")
        return
    f1, f2 = 100 * lost1 / tot, 100 * lost2 / tot
    st = FAIL if f1 > 5 else WARN if f1 > 0.5 else OK
    d = f"{f1:.2f} % of the area is thinner than {NOZZLE} mm (will not print), {f2:.1f} % thinner than {2 * NOZZLE} mm (single wall, weak)"
    if worst_z is not None and worst > 0.005:
        d += f"; worst near z={worst_z:.1f} mm"
    rep.add(st, "Thin features", d, "Thicken walls/details to >= 0.8 mm (2 perimeters)." if st != OK else "")


def check_warp(rep, layers, mat, mi):
    first = next((g for g in layers[:3] if not g.is_empty), Polygon())
    if first.is_empty:
        return
    minx, miny, maxx, maxy = first.bounds
    L = max(maxx - minx, maxy - miny)
    score = L * mi["warp"]
    st = FAIL if score >= 450 else WARN if score >= 150 else OK
    rep.add(st, f"Warping / bed adhesion ({mat})",
            f"first layer {L:.0f} mm long, contact {first.area / 100:.1f} cm² (risk score {score:.0f}; <150 ok, >=450 high)",
            "Brim, textured PEI + glue, bed 100 °C, closed chamber, no draft; or PLA/PETG." if st != OK else "")
    if first.area < 50:
        rep.add(WARN, "Bed contact area", f"only {first.area:.0f} mm² touches the bed", "Add a brim or a flat base.")


def check_stability(rep, whole, layers):
    first = next((g for g in layers[:3] if not g.is_empty), None)
    if first is None:
        return
    hull = first.convex_hull
    com = whole.center_mass if whole.is_watertight else whole.centroid
    h, H = float(com[2] - whole.bounds[0][2]), float(whole.extents[2])
    pt = Point(com[0], com[1])
    short = 2 * float(shapely.maximum_inscribed_circle(hull, 0.1).length) if hull.area > 0 else 0
    aspect = H / max(short, 1e-6)
    if not hull.contains(pt):
        rep.add(FAIL, "Stability while printing", f"centre of mass is outside the first-layer footprint (height {H:.0f} mm)",
                "It will fall over / peel off the bed: re-orient, wide brim, or add a base.")
        return
    tip = math.degrees(math.atan2(hull.exterior.distance(pt), max(h, 1e-6)))
    st = FAIL if aspect > 10 else WARN if (aspect > 5 or tip < 8) else OK
    rep.add(st, "Stability (as oriented)", f"tips at {tip:.0f}° tilt, height/footprint ratio {aspect:.1f} (wobbles when > 5)",
            "Tall and thin: wide brim, lower speed/acceleration, or lay it down." if st != OK else "")


def check_strength(rep, zs, layers, step, mat, mi, load, fill, whole):
    allow = mi["xy"] * Z_KNOCKDOWN
    weight = lambda vol: vol * mi["rho"] * 1e-3 * fill * 1e-3 * 9.81
    areas = np.array([g.area for g in layers])
    above = np.cumsum((areas * step)[::-1])[::-1]
    ztop = float(whole.bounds[1][2])
    worst = (float("inf"), None, 0, 0)
    for i in np.unique(np.linspace(0, len(layers) - 1, min(60, len(layers))).astype(int)):
        g = layers[i]
        if g.is_empty:
            continue
        A, c, Imin, nrm = moments(g)
        if A < 1e-6:
            continue
        pts = np.vstack([np.asarray(p.exterior.coords) for p in poly_list(g)])
        cmax = float(np.abs((pts[:, 0] - c[0]) * nrm[0] + (pts[:, 1] - c[1]) * nrm[1]).max())
        sigma = load * max(ztop - zs[i], 0.0) * cmax / Imin + weight(above[i]) / A
        sf = allow / sigma if sigma > 1e-9 else float("inf")
        if sf < worst[0]:
            worst = (sf, zs[i], sigma, A)
    sf, z, sigma, A = worst
    if z is None:
        return
    st = FAIL if sf < 1.5 else WARN if sf < 3 else OK
    sfs = "no significant stress" if math.isinf(sf) else f"safety factor {sf:.1f}"
    rep.add(st, f"Strength: {load:g} N sideways at the top",
            f"{sfs}; weakest section at z={z:.1f} mm (area {A:.0f} mm², {sigma:.2f} MPa vs {allow:.0f} MPa across layers in {mat})",
            "Thicken that section, add fillets, or print it flat (layers along the load)." if st != OK else "")


# ---------------------------------------------------------------- 2. will the printed part work as designed
class Body:
    def __init__(self, mesh, idx):
        self.mesh, self.idx = mesh, idx
        self.vol = shell_volume(mesh)
        e = mesh.extents
        self.name = f"part{idx + 1} ({e[0]:.0f}x{e[1]:.0f}x{e[2]:.0f} mm)"
        self._pts = None

    def samples(self, n=6000):
        if self._pts is None:
            pts, fi = trimesh.sample.sample_surface_even(self.mesh, n)
            self._pts = np.vstack([self.mesh.vertices[:n], pts])
            self._nrm = np.vstack([self.mesh.vertex_normals[:n], self.mesh.face_normals[fi]])
        return self._pts

    def normals(self):
        self.samples()
        return self._nrm


def dists(points, mesh):
    q, d, _ = trimesh.proximity.closest_point(mesh, points)
    return d, q


def signed_dists(points, mesh):
    """Distance to the surface, negative when the point is inside (sign from the nearest triangle's normal)."""
    q, d, tri = trimesh.proximity.closest_point(mesh, points)
    inside = ((points - q) * mesh.face_normals[tri]).sum(1) < 0
    return np.where(inside & (d > 1e-9), -d, d)


def pair_points(a, b, lim):
    """All sampled surface points of a/b that lie within `lim` of the other body: (distance, point, nearest point on the other)."""
    d1, q1 = dists(a.samples(), b.mesh)
    d2, q2 = dists(b.samples(), a.mesh)
    p = np.vstack([a.samples(), b.samples()])
    q = np.vstack([q1, q2])
    nrm = np.vstack([a.normals(), b.normals()])
    d = np.r_[d1, d2]
    gap_dir = (q - p) / np.maximum(d, 1e-9)[:, None]
    facing = ((nrm * gap_dir).sum(1) > 0.5) | (d < 0.02)           # only surfaces that FACE the other body form a gap
    k = (d <= lim) & facing
    return d[k], p[k], q[k]


def group_touching(shells, tol=0.01):
    """Shells that touch / overlap are ONE part (colour layers, letters on a plate): merge them."""
    n = len(shells)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    cache = {}

    def smp(i):
        if i not in cache:
            cache[i] = trimesh.sample.sample_surface_even(shells[i], 1500)[0]
        return cache[i]

    for i in range(n):
        for j in range(i + 1, n):
            a, b = shells[i], shells[j]
            if find(i) == find(j):
                continue
            if np.any(a.bounds[1] + tol < b.bounds[0]) or np.any(b.bounds[1] + tol < a.bounds[0]):
                continue
            if dists(smp(i), b)[0].min() <= tol or dists(smp(j), a)[0].min() <= tol:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(shells[i])
    return [trimesh.util.concatenate(g) if len(g) > 1 else g[0] for g in groups.values()]


def printed_range(d, p, q, prof):
    """Per sample: (best, worst) printed gap from the designed gap d and its direction / height. Vectorised."""
    v = q - p
    n = np.linalg.norm(v, axis=1)
    vertical = (n > 1e-9) & (np.abs(v[:, 2]) / np.maximum(n, 1e-9) > 0.7)       # layer steps / bridge sag
    best = np.where(vertical, d - prof["z_growth"][0], d - (prof["outer_growth"][0] + prof["hole_growth"][0]))
    worst = np.where(vertical, d - prof["z_growth"][1], d - (prof["outer_growth"][1] + prof["hole_growth"][1]))
    ef = (~vertical) & (np.minimum(p[:, 2], q[:, 2]) < prof["elephant_z"])
    worst = worst - np.where(ef, 2 * prof["elephant_foot"], 0.0)
    return best, worst, vertical


def fit_verdict(nominal, best, worst, prof):
    if best <= prof["fuse_gap"]:
        return FAIL, "JAMS / FUSES even in the best case"
    if worst <= -2 * prof["free_gap"]:
        return WARN, "very likely JAMS / FUSES (only the best case clears)"
    if worst >= prof["free_gap"]:
        if nominal > prof["loose_gap"]:
            return WARN, "loose / wobbly (not a precision fit)"
        return OK, "fits / moves freely in every case"
    return WARN, "undecided: depends on the real printer (measure it)"


def circle3(p1, p2, p3):
    ax, ay = p1; bx, by = p2; cx, cy = p3
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return np.array([ux, uy]), math.hypot(ax - ux, ay - uy)


def detect_axis(pts, iters=300):
    """(point, unit axis, radius) if many near-surface points lie on one cylinder around the x, y or z axis (RANSAC:
    tolerant to a head / flange / unrelated points)."""
    rng = np.random.default_rng(0)
    best = None
    for u in (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])):
        a = np.cross(u, [0, 0, 1.0] if abs(u[2]) < 0.9 else [1.0, 0, 0])
        a /= np.linalg.norm(a)
        b = np.cross(u, a)
        p2 = np.c_[pts @ a, pts @ b]
        for _ in range(iters):
            c3 = circle3(*p2[rng.choice(len(p2), 3, replace=False)])
            if c3 is None or not (0.4 < c3[1] < 60):
                continue
            c, r = c3
            inl = np.abs(np.hypot(*(p2 - c).T) - r) < 0.08
            n = int(inl.sum())
            if n < max(25, 0.25 * len(p2)):
                continue
            ang = np.sort(np.arctan2(p2[inl, 1] - c[1], p2[inl, 0] - c[0]))
            covered = 2 * math.pi - np.diff(np.r_[ang, ang[0] + 2 * math.pi]).max()
            if covered > 1.5 * math.pi and (best is None or n > best[0]):
                best = (n, c[0] * a + c[1] * b + u * float(pts[inl].mean(0) @ u), u, r)
    return None if best is None else best[1:]


def rot_about(pts, point, axis, deg):
    R = trimesh.transformations.rotation_matrix(math.radians(deg), axis, point)
    return (np.c_[pts, np.ones(len(pts))] @ R.T)[:, :3]


def sweep(mover, fixed, move, closing, values):
    """Largest contiguous range in each direction from 0 that stays free. `closing` = per-sample mm the printing
    closes the gap at that point (None = designed geometry)."""
    allp = mover.samples()
    stride = max(1, len(allp) // 500)                               # ~500 points are enough to catch contact
    pts = allp[::stride]
    cl = 0.0 if closing is None else closing[::stride]
    out = []
    for sgn in (-1, 1):
        free = 0
        for v in values:
            if (signed_dists(move(pts, sgn * v), fixed.mesh) - cl).min() <= 0.0:
                break
            free = v
        out.append(free)
    return out


def check_fit(rep, shells, prof):
    if not shells:
        return
    parts = []
    for oi in sorted({s_.metadata.get("obj", 0) for s_ in shells}):
        parts += group_touching([s_ for s_ in shells if s_.metadata.get("obj", 0) == oi])
    bodies = [Body(m, i) for i, m in enumerate(sorted(parts, key=lambda m: -shell_volume(m)))][:14]
    rep.facts["parts"] = len(bodies)
    if len(bodies) < 2:
        rep.add(OK, "Fit / clearance", "this file is one single part: nothing to fit against (pass an assembly, "
                                       "with the mating parts in their assembled positions, to check fits)")
        return
    lim = prof["pair_distance"]
    rows, n_pairs = [], 0
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            a, b = bodies[i], bodies[j]
            if np.any(a.mesh.bounds[1] + lim < b.mesh.bounds[0]) or np.any(b.mesh.bounds[1] + lim < a.mesh.bounds[0]):
                continue
            d, p, q = pair_points(a, b, lim)
            contact = int((d < 0.02).sum())
            keep = d >= 0.02                                            # touching surfaces are by design, not a gap
            d, p, q = d[keep], p[keep], q[keep]
            if len(d) == 0:
                if contact:
                    rows.append((OK, f"Contact {a.name} ↔ {b.name}", f"touch each other by design ({contact} sample points), no gap to check", ""))
                continue
            n_pairs += 1
            best, worst, vert = printed_range(d, p, q, prof)
            nominal = float(d.min())
            t_ = int(worst.argmin())                                 # the point that is tightest AFTER printing
            bmin, wmin = float(best.min()), float(worst.min())
            st, msg = fit_verdict(nominal, bmin, wmin, prof)
            need = float((d - worst).max()) + prof["free_gap"]       # design gap that survives the worst case
            adv = "" if st == OK else (f"Design gap >= {need:.2f} mm here (now {nominal:.2f}) to be safe in the worst case, "
                                       f"or measure the printer and calibrate the profile.")
            rows.append((st, f"Fit {a.name} ↔ {b.name}",
                         f"designed gap {nominal:.2f} mm → printed {bmin:.2f} (best) .. {wmin:.2f} (worst) mm, tightest at "
                         f"({p[t_][0]:.0f}, {p[t_][1]:.0f}, {p[t_][2]:.1f}) ({'vertical' if vert[t_] else 'horizontal'} gap)"
                         + (f"; {contact} contact points ignored" if contact else "") + f"; {msg}", adv))
            if st == FAIL or nominal < 0.02 or min(a.vol, b.vol) < 200:      # motion only for real parts, not specks
                continue
            inner, outer = (b, a) if a.vol >= b.vol else (a, b)
            dd, _ = dists(inner.samples(), outer.mesh)
            near = inner.samples()[dd < nominal + 2.0]
            dI, qI = dists(inner.samples(), outer.mesh)
            _, wI, _ = printed_range(dI, inner.samples(), qI, prof)
            touching = dI < 0.02                                     # faces that touch by design may keep touching, not penetrate
            closing = np.where(touching, -0.03, np.maximum(dI - wI, 0.0))     # per-point worst-case closing, by direction / height
            closing0 = np.where(touching, -0.03, 0.0)                # designed geometry
            if len(near) < 30:
                continue
            ax = detect_axis(near[:: max(1, len(near) // 1500)])
            if ax is not None:
                pt, u, r = ax
                mv = lambda pts, deg: rot_about(pts, pt, u, deg)
                lo0, hi0 = sweep(inner, outer, mv, closing0, range(10, 181, 10))
                lo, hi = sweep(inner, outer, mv, closing, range(10, 181, 10))
                s2 = OK if (lo0 - lo <= 12 and hi0 - hi <= 12) else WARN
                rows.append((s2, f"Hinge {a.name} ↔ {b.name}",
                             f"pin/hole axis found (r≈{r:.1f} mm, axis {np.round(u, 2).tolist()}); designed free turn "
                             f"-{lo0}°..+{hi0}°{' (full turn)' if min(lo0, hi0) >= 180 else ''}; as printed (worst case) -{lo}°..+{hi}°",
                             "" if s2 == OK else "The printed hinge loses range or catches: widen the clearance around the pin."))
                continue
            axes = [np.array(v, float) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
            c = near.mean(0)
            ev, evec = np.linalg.eigh(np.cov((near - c).T))
            if ev[2] > 8 * max(ev[1], 1e-9):
                axes.append(evec[:, 2])
            coarse = np.array([0.5, 1.0, 1.5, 2.0, 3.0])          # small steps: walls are ~1.4 mm, a big step would jump over them
            trav = []
            for dvec in axes:
                lo_, hi_ = sweep(inner, outer, lambda pts, t, dv=dvec: pts + dv * t, closing0, coarse)
                trav.append(lo_ + hi_)
            order = np.argsort(trav)[::-1]
            # a sliding joint = free along one axis while blocked along another (otherwise the parts are simply loose)
            if trav[order[0]] >= 2.5 and min(trav[:3]) < 1.0:
                dvec = axes[order[0]]
                mv = lambda pts, t, dv=dvec: pts + dv * t
                fine = np.arange(0.7, 28.1, 0.7)
                lo0, hi0 = sweep(inner, outer, mv, closing0, fine)
                lo, hi = sweep(inner, outer, mv, closing, fine)
                s2 = OK if (lo0 - lo <= 2 and hi0 - hi <= 2) else WARN
                rows.append((s2, f"Slide {a.name} ↔ {b.name}",
                             f"sliding joint along {np.round(dvec, 2).tolist()}; designed free travel -{lo0:.0f}..+{hi0:.0f} mm "
                             f"(checked up to 28 mm); as printed (worst case) -{lo:.0f}..+{hi:.0f} mm",
                             "" if s2 == OK else "The printed rail/slot binds before the full travel: add clearance."))
    if n_pairs == 0:
        rep.add(OK, "Fit / clearance", f"{len(bodies)} separate parts, none closer than {lim:g} mm: no interacting pairs")
    for r in rows[:30]:
        rep.add(*r)
    if len(rows) > 30:
        rep.add(WARN, "Fit / clearance", f"{len(rows) - 30} more pair rows not shown")


# ---------------------------------------------------------------- preview
def render_png(path, whole):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    m = whole
    over = (m.face_normals[:, 2] < -0.7071) & (m.triangles_center[:, 2] > m.bounds[0][2] + 0.3)
    idx = np.arange(len(m.faces))
    if len(idx) > 30000:
        idx = np.random.default_rng(0).choice(idx, 30000, replace=False)
    col = np.where(over[idx, None], np.array([[0.85, 0.15, 0.15, 1.0]]), np.array([[0.55, 0.65, 0.8, 1.0]]))
    fig = plt.figure(figsize=(11, 5))
    for k, (el, az) in enumerate([(25, -60), (-35, 30)]):
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        ax.add_collection3d(Poly3DCollection(m.triangles[idx], facecolors=col, edgecolors="none"))
        b = m.bounds
        c, r = b.mean(0), (b[1] - b[0]).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.view_init(el, az); ax.set_axis_off()
        ax.set_title("top" if k == 0 else "underside (red = overhang)", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


# ---------------------------------------------------------------- main
def analyse(path, a, prof):
    t0 = time.time()
    rep = Report(Path(path).name)
    meshes, shells = load_bodies(path, prof["min_volume"])
    if not meshes:
        rep.add(FAIL, "Load", "no mesh found in file")
        return rep, None
    mat = a.filament.upper()
    mi = MATERIALS[mat]
    dz = -min(m.bounds[0][2] for m in meshes)                # drop onto the bed
    for m in meshes + shells:
        m.apply_translation([0, 0, dz])
    whole = trimesh.util.concatenate(meshes)
    step = a.step or float(np.clip(whole.extents[2] / 120, 0.2, 0.6))
    rep.facts.update(size=[round(float(x), 1) for x in whole.extents], profile_calibrated=prof["calibrated"])
    check_health(rep, meshes, shells)
    if not a.assembly:                                      # an assembly is NOT a print orientation: no print checks on it
        zs, layers = slice_layers(meshes, step)
        check_thin(rep, zs, layers)
        check_warp(rep, layers, mat, mi)
        check_stability(rep, whole, layers)
        check_strength(rep, zs, layers, step, mat, mi, a.load, a.fill, whole)
    if not a.no_fit:
        check_fit(rep, shells, prof)
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
    ap.add_argument("--profile", help="printer error profile JSON (default cad/config/printer_profile.json, else built-in estimates)")
    ap.add_argument("--load", type=float, default=10.0, help="sideways handling force at the top of the part, N (default 10)")
    ap.add_argument("--fill", type=float, default=0.4, help="effective solid fraction for weight, default 0.4")
    ap.add_argument("--step", type=float, default=None, help="slice step, mm (default auto)")
    ap.add_argument("--assembly", action="store_true", help="the file holds several parts in their ASSEMBLED positions: "
                                                           "only check fits / clearances / joints (not printability)")
    ap.add_argument("--no-fit", action="store_true", help="skip the fit / clearance / joint simulation")
    ap.add_argument("--png", help="write an overhang preview PNG")
    ap.add_argument("--json", help="write the results as JSON")
    a = ap.parse_args()
    if a.filament.upper() not in MATERIALS:
        sys.exit(f"unknown filament {a.filament}; choose from {', '.join(MATERIALS)}")
    prof = load_profile(a.profile)
    if not prof["calibrated"]:
        print("NOTE: printer profile is NOT calibrated (estimates from public reports): fit results are ranges, not promises.")
    results, worst = [], OK
    for f in a.files:
        rep, whole = analyse(f, a, prof)
        print_report(rep, a)
        results.append(rep)
        if a.png and whole is not None:
            out = a.png if len(a.files) == 1 else str(Path(a.png).with_name(f"{Path(a.png).stem}_{Path(f).stem}.png"))
            render_png(out, whole)
            print(f"   preview: {out}")
        if rep.verdict == FAIL:
            worst = FAIL
        elif rep.verdict == WARN and worst == OK:
            worst = WARN
    if len(results) > 1:
        print("\nSummary:")
        for r in results:
            print(f" {ICON[r.verdict]} {r.name}")
    print("\nNot covered: bed fit / supports / time / cost (use /3d-cost), impact and heat, "
          "parts given as separate files without assembled positions.")
    if a.json:
        Path(a.json).write_text(json.dumps([dict(file=r.name, verdict=r.verdict, facts=r.facts, checks=r.rows) for r in results],
                                           indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    sys.exit(2 if worst == FAIL else 0)


if __name__ == "__main__":
    main()
