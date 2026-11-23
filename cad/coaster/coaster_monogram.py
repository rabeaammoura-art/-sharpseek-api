"""Clear TPU coaster with a gold monogram letter + frame (owner 2026-11-23, after a marble/gold reference picture).

    python cad/coaster/coaster_monogram.py --letter R [--no-branch] --out OUT.3mf

Ø95 x 3.0 mm, same layers as coaster_text.py: TPU 0.4 (face, on the plate) | gold inlay 0.6 | TPU 2.0, rounded edges,
mirrored. Inlay = Cinzel Bold letter (OFL, cad/fonts) inside a thin inner ring, an outer rim ring near the edge, and an
own laurel branch on the left crossing the inner ring. ONE inlay colour (gold silk) -> fast, no colour swaps per layer.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import coaster, coaster_text as ct     # noqa: E402
from threemf import write_bambu_3mf    # noqa: E402

FONT = HERE.parent / "fonts" / "Cinzel-Bold.ttf"
RING_C, RING_R, RING_W = (4.0, 1.0), 31.0, 1.0       # inner frame ring (centre slightly right, like the picture)
RIM_R, RIM_W = 44.6, 1.4                             # outer rim ring (TPU edge wall outside it ~2.2 mm)


def letter(ch, height=30.0):
    tp = TextPath((0, 0), ch, size=100, prop=FontProperties(fname=str(FONT)))
    rings = sorted((r for r in (Polygon(p).buffer(0) for p in tp.to_polygons() if len(p) > 3) if r.area > 1), key=lambda r: -r.area)
    depth = [sum(1 for q in rings if q.area > r.area and q.contains(r)) for r in rings]
    g = unary_union([r for r, d in zip(rings, depth) if d % 2 == 0]).difference(unary_union([r for r, d in zip(rings, depth) if d % 2 == 1]))
    b = g.bounds; s = height / (b[3] - b[1])
    g = affinity.scale(affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2), s, s, origin=(0, 0))
    return affinity.translate(g, *RING_C)


def leaf(L, W):
    R = (L * L / 4 + W * W / 4) / W
    g = Point(0, -(R - W / 2)).buffer(R, 64).intersection(Point(0, R - W / 2).buffer(R, 64))
    return affinity.translate(affinity.rotate(g, 90, origin=(0, 0)), L / 2, 0)


def branch():
    """laurel branch on the left: curved stem from bottom to top-left, leaves and berry sprigs"""
    t = np.linspace(0, 1, 80)
    p0, p1, p2 = np.array([-4.0, -34.0]), np.array([-24.0, -14.0]), np.array([-33.0, 24.0])
    pts = (1 - t)[:, None] ** 2 * p0 + 2 * ((1 - t) * t)[:, None] * p1 + t[:, None] ** 2 * p2
    stem = LineString(pts).buffer(0.55, 16)
    parts = [stem]
    for i, u in enumerate(np.linspace(0.12, 0.95, 9)):
        k = int(u * 79); d = pts[min(k + 1, 79)] - pts[max(k - 1, 0)]; ang = np.degrees(np.arctan2(d[1], d[0]))
        side = 1 if i % 2 else -1
        if i % 3 == 2:      # berry sprig: short stalk + 3 berries
            base = pts[k]; a = np.radians(ang + side * 50)
            tip = base + 5.0 * np.array([np.cos(a), np.sin(a)])
            parts.append(LineString([base, tip]).buffer(0.45, 8))
            for da in (-35, 0, 35):
                aa = np.radians(ang + side * 50 + da); bp = tip + 1.6 * np.array([np.cos(aa), np.sin(aa)])
                parts.append(LineString([tip, bp]).buffer(0.4, 8)); parts.append(Point(*bp).buffer(1.0, 24))
        else:
            lf = affinity.rotate(leaf(9.0 - 2.0 * u, 3.6), ang + side * 42, origin=(0, 0))
            parts.append(affinity.translate(lf, *pts[k]))
    top = affinity.rotate(leaf(6.0, 2.4), np.degrees(np.arctan2(*(pts[-1] - pts[-3])[::-1])), origin=(0, 0))
    parts.append(affinity.translate(top, *pts[-1]))
    return unary_union(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--letter", default="R"); ap.add_argument("--no-branch", action="store_true")
    ap.add_argument("--colour", default="#D4AF37"); ap.add_argument("--out", required=True); ap.add_argument("--stl", action="store_true")
    a = ap.parse_args()
    ring = Point(*RING_C).buffer(RING_R + RING_W / 2, 256).difference(Point(*RING_C).buffer(RING_R - RING_W / 2, 256))
    rim = Point(0, 0).buffer(RIM_R + RIM_W / 2, 256).difference(Point(0, 0).buffer(RIM_R - RIM_W / 2, 256))
    geo = [letter(a.letter), ring, rim] + ([] if a.no_branch else [branch()])
    gold = unary_union(geo)
    thin = gold.difference(gold.buffer(-0.35).buffer(0.35))
    print(f"gold inlay {gold.area:.0f} mm2, under 0.7 mm {thin.area:.2f} mm2")
    ink = coaster.extrude(gold, ct.Z0, ct.Z1)
    tpu = trimesh.boolean.difference([ct.rounded_disc(), ink], engine="manifold")
    parts = [(n, coaster.mirror_x(m), s) for n, m, s in [("clear_tpu", tpu, 1), ("gold", ink, 2)]]
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = ["#E8F1F5", a.colour, "#C8102E", "#E07A1F"]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
