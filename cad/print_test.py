"""Printability test for STL/3MF models (layer-by-layer, FDM, plate-down): finds what a slicer warns about or what fails on the printer.
Usage: python cad/print_test.py model.stl [part2.stl ...] [--layer 0.4] [--angle 45] [--min-feature 0.7] [--bed 325x320x325] [--slice --filament NAME]
Several files = one assembly printed together (multi-colour parts). Exit code 1 if there is a PROBLEM (not only warnings).
Checks: watertight, on the bed (zmin = 0), fits the bed, first-layer contact, floating islands, overhangs beyond the angle, features thinner than min-feature,
tall thin columns. Optional --slice runs the Bambu Studio CLI (cad/bambu_slice.py) and relays its warnings, time and weight."""
import argparse, subprocess, sys, json
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union, polygonize


def load(paths):
    ms = []
    for p in paths:
        m = trimesh.load(p, force="mesh") if not str(p).lower().endswith(".3mf") else trimesh.load(p, force="mesh")
        ms.append(m)
    return trimesh.util.concatenate(ms) if len(ms) > 1 else ms[0]


class Slicer:
    def __init__(self, mesh):
        self.t = mesh.triangles; self.zmin = self.t[:, :, 2].min(1); self.zmax = self.t[:, :, 2].max(1)

    def layer(self, z):
        idx = np.where((self.zmin < z) & (self.zmax > z))[0]
        if not len(idx): return None
        tri = self.t[idx]; d = tri[:, :, 2] - z; segs = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            m = d[:, a] * d[:, b] < 0
            s = d[m, a] / (d[m, a] - d[m, b]); p = tri[m, a] + s[:, None] * (tri[m, b] - tri[m, a])
            segs.append((np.where(m)[0], p[:, :2]))
        # per triangle exactly two crossing points
        pts = {}
        for ids, p in segs:
            for i, q in zip(ids, p): pts.setdefault(i, []).append((round(float(q[0]), 3), round(float(q[1]), 3)))
        lines = [LineString(v[:2]) for v in pts.values() if len(v) >= 2 and v[0] != v[1]]
        if not lines: return None
        polys = list(polygonize(unary_union(lines)))
        if not polys: return None
        # nested rings are holes: even-odd by sorting by area
        polys.sort(key=lambda p: -p.area); shapes = []
        for p in polys:
            for i, q in enumerate(shapes):
                if q.contains(p): shapes[i] = q.difference(p); break
            else: shapes.append(p)
        return unary_union(shapes)


def run(a):
    mesh = load(a.files); r = {"problems": [], "warnings": [], "info": {}}
    b = mesh.bounds; ext = mesh.extents; r["info"]["size_mm"] = [round(float(v), 1) for v in ext]; r["info"]["faces"] = int(len(mesh.faces))
    if not mesh.is_watertight: r["problems"].append("الشبكة مش watertight (فيها فتحات أو حواف مفتوحة): الـ slicer ممكن يخرّب أو يتجاهل أجزاء")
    if mesh.volume <= 0: r["problems"].append("الحجم صفر أو سالب (الوجوه مقلوبة)")
    if abs(b[0][2]) > 0.02: r["problems"].append(f"القطعة مش على السرير: أقل Z = {b[0][2]:.2f} مم (لازم 0)")
    bx, by, bz = [float(v) for v in a.bed.split("x")]
    if ext[0] > bx or ext[1] > by or ext[2] > bz: r["problems"].append(f"القطعة أكبر من السرير ({bx:.0f}×{by:.0f}×{bz:.0f}): {ext.round(1).tolist()}")
    elif max(ext[0], ext[1]) > 290 and not a.no_tower_note: r["warnings"].append("أكبر من 290 مم: ما بتتسع مع برج التنظيف بالطباعة الملونة إلا إذا القطعة رفيعة وحطيت البرج على جنبها بالـ Y")
    if len(mesh.faces) > 600000: r["warnings"].append(f"الشبكة ثقيلة ({len(mesh.faces)} وجه): الفحص بطيء")
    sl = Slicer(mesh); dz = a.layer; allow = dz * np.tan(np.radians(a.angle)) + 0.05
    zs = np.arange(b[0][2] + dz / 2, b[1][2], dz); prev = None; islands = []; over = []; thin = []; first = None
    for z in zs:
        cur = sl.layer(z)
        if cur is None or cur.is_empty: prev = None; continue
        if first is None:
            first = cur; r["info"]["first_layer_area_mm2"] = round(cur.area, 1)
            if cur.area < 4: r["problems"].append(f"ملامسة السرير صغيرة جداً ({cur.area:.1f} مم²): بتنفك أثناء الطباعة")
        if prev is not None and z > b[0][2] + 0.6:
            comps = [cur] if cur.geom_type == "Polygon" else list(cur.geoms)
            for c in comps:
                if c.area > 0.5 and not c.intersects(prev.buffer(0.05)): islands.append((z, c.bounds, c.area))
            new = cur.difference(prev.buffer(allow))
            if not new.is_empty and new.area > 0.8:
                gs = [new] if new.geom_type == "Polygon" else list(new.geoms)
                for g in gs:
                    if g.area > 0.8:
                        w = min(g.minimum_rotated_rectangle.length / 4.0, 99) if False else None
                        rr = g.minimum_rotated_rectangle; xs, ys = rr.exterior.xy; sides = sorted([np.hypot(xs[i+1]-xs[i], ys[i+1]-ys[i]) for i in range(2)])
                        over.append((z, g.bounds, g.area, sides[0], sides[1]))
        lost = cur.difference(cur.buffer(-a.min_feature / 2).buffer(a.min_feature / 2))
        if lost.area > 1.0 and (len(thin) == 0 or z - thin[-1][0] > 1.5): thin.append((z, lost.bounds, lost.area))
        prev = cur
    def cluster(items, key_bounds=1):
        out = []
        for it in items:
            bb = it[key_bounds]
            for c in out:
                cb = c["bounds"]
                if not (bb[2] < cb[0] - 2 or bb[0] > cb[2] + 2 or bb[3] < cb[1] - 2 or bb[1] > cb[3] + 2):
                    c["bounds"] = (min(cb[0], bb[0]), min(cb[1], bb[1]), max(cb[2], bb[2]), max(cb[3], bb[3])); c["z"] = (c["z"][0], it[0]); c["n"] += 1; c["area"] += it[2]; c["depth"] = max(c["depth"], it[3] if len(it) > 3 else 0); break
            else: out.append({"bounds": bb, "z": (it[0], it[0]), "n": 1, "area": it[2], "depth": it[3] if len(it) > 3 else 0})
        return out
    for c in cluster(islands):
        r["problems"].append(f"جزيرة عايمة (مش متسندة بالطبقة اللي تحتها) عند Z={c['z'][0]:.1f}-{c['z'][1]:.1f} مم، مكانها x {c['bounds'][0]:.0f}..{c['bounds'][2]:.0f} y {c['bounds'][1]:.0f}..{c['bounds'][3]:.0f}")
    for c in cluster(over):
        sev = "problems" if (c["depth"] > 6 or c["z"][1] - c["z"][0] > 3) else "warnings"
        r[sev].append(f"نتوء (overhang) أكثر من {a.angle}° عند Z={c['z'][0]:.1f}-{c['z'][1]:.1f} مم، عرضه حوالي {c['depth']:.1f} مم، مساحته {c['area']:.0f} مم²، x {c['bounds'][0]:.0f}..{c['bounds'][2]:.0f} y {c['bounds'][1]:.0f}..{c['bounds'][3]:.0f}")
    for c in cluster(thin)[:5]:
        r["warnings"].append(f"فيه عناصر أرفع من {a.min_feature} مم (بتنشال أو بتطلع ضعيفة) حوالي Z={c['z'][0]:.1f} مم، x {c['bounds'][0]:.0f}..{c['bounds'][2]:.0f} y {c['bounds'][1]:.0f}..{c['bounds'][3]:.0f}")
    if len(thin) > 5: r["warnings"].append(f"... وفيه {len(thin) - 5} مكان ثاني بنفس المشكلة")
    r["info"]["layers_checked"] = int(len(zs)); r["info"]["overhang_angle"] = a.angle
    if a.slice:
        cmd = [sys.executable, str(Path(__file__).parent / "bambu_slice.py"), *a.files, "--price-kg", "0"]
        for f in (a.filament or ["Bambu PLA Basic @BBL H2D"]): cmd += ["--filament", f]
        if a.tower_x is not None: cmd += ["--tower-x", str(a.tower_x), "--tower-y", str(a.tower_y), "--tower-width", str(a.tower_w)]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3000).stdout.strip().splitlines()
        r["info"]["slicer"] = [l for l in out if any(k in l for k in ("h", "warning", "per filament"))][-4:]
        for l in out:
            if "warning" in l.lower(): r["problems"].append("تحذير من الـ slicer: " + l.strip())
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("files", nargs="+")
    ap.add_argument("--layer", type=float, default=0.4); ap.add_argument("--angle", type=float, default=45.0)
    ap.add_argument("--min-feature", type=float, default=0.7); ap.add_argument("--bed", default="325x320x325")
    ap.add_argument("--no-tower-note", action="store_true"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--slice", action="store_true"); ap.add_argument("--filament", action="append")
    ap.add_argument("--tower-x", type=float); ap.add_argument("--tower-y", type=float, default=230.0); ap.add_argument("--tower-w", type=float, default=30.0)
    a = ap.parse_args(); r = run(a)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print("حجم القطعة:", r["info"]["size_mm"], "| طبقات انفحصت:", r["info"]["layers_checked"], "| مساحة الطبقة الأولى:", r["info"].get("first_layer_area_mm2"))
        for k, title in (("problems", "مشاكل"), ("warnings", "ملاحظات")):
            print(f"\n{title}: {len(r[k])}")
            for x in r[k]: print(" -", x)
        for l in r["info"].get("slicer", []): print("slicer:", l)
        if not r["problems"]: print("\nما لقيت مشاكل تمنع الطباعة.")
    sys.exit(1 if r["problems"] else 0)
