"""Sanity checks for a plaque JSON in glow_cap mode (coverage of openings, bridging spans, base islands, mesh health).

Usage: python check_plaque.py plaque/example_ar_glowcap.json
"""
import json
import sys

import numpy as np
import shapely
import trimesh
from shapely.ops import unary_union

import newborn_plaque as n


def main(path):
    data = json.load(open(path, encoding="utf-8"))
    size = float(data.get("size", 300))
    layers = n.build(data)
    base = layers["base"]
    plate = [(g, z0, z1) for g, z0, z1 in base if z0 == 0][0][0]
    caps = unary_union([g for r in ("main", "accent", "animal", "base") for g, z0, z1 in layers[r]
                        if abs(z0 - n.BASE_H) < 1e-6])
    plate_geom = plate
    outer = n.rrect(0, 0, size, size, 30 * size / n.SIZE)
    openings = outer.difference(plate_geom)               # everything missing from the base = openings (+ outside)
    openings = openings.intersection(outer.buffer(-0.01))
    pieces = list(plate_geom.geoms) if hasattr(plate_geom, "geoms") else [plate_geom]
    leak = openings.difference(caps)
    print(f"size {size:.0f} mm | base pieces: {len(pieces)} | opening area {openings.area:.0f} mm2")
    print(f"uncovered opening area (light leaks / bare holes): {leak.area:.2f} mm2")
    islands = sorted(p.area for p in pieces)[:-1]
    print(f"base islands: {len(islands)}; smallest {min(islands) if islands else 0:.1f} mm2; <4 mm2: {sum(a < 4 for a in islands)}")
    spans = []
    for o in (openings.geoms if hasattr(openings, "geoms") else [openings]):
        if o.area > 1:
            spans.append(2 * shapely.maximum_inscribed_circle(o, 0.05).length)
    spans.sort(reverse=True)
    print("largest bridging spans (mm, across the opening):", [round(s, 1) for s in spans[:6]])
    print("openings wider than 20 mm:", sum(s > 20 for s in spans))
    for role in ("base", "main", "accent", "animal"):
        m = n.to_mesh(layers[role])
        if m is None:
            continue
        print(f"mesh {role:7s} watertight={m.is_watertight} bodies={m.body_count} volume={m.volume / 1000:7.2f} cm3")


if __name__ == "__main__":
    main(sys.argv[1])
