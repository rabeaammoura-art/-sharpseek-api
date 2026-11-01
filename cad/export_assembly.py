"""export_assembly.py - write the plaque + its stand parts in their ASSEMBLED positions as one 3MF, for /print-test.

Usage: python export_assembly.py plaque/example_ar_rails.json [--out out/assembly]
Currently: stand "rails" (plaque + bridge sliding in the rails). The bridge is moved from its print frame (standing on
its edge) into the plaque frame; the folding leg is not placed yet (its hinge pose is not exported).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import trimesh

import newborn_plaque as n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default="out/assembly")
    a = ap.parse_args()
    data = json.load(open(a.data, encoding="utf-8"))
    if data.get("stand") != "rails":
        raise SystemExit("assembly export is implemented for stand 'rails' only")
    size = float(data.get("size", 300))
    layers = n.build(data)
    plaque = trimesh.util.concatenate([m for m in (n.to_mesh(layers[r]) for r in ("base", "main", "accent", "animal")) if m is not None])
    bridge, leg, info, world = n.make_bridge(size)
    # print frame (X across, Y out of the back, Z along the rails) -> plaque frame (x, y up the plaque, z up from the back face)
    y_c = -size / 2 + n.RAIL_PIVOT * size
    T = np.array([[1, 0, 0, 0], [0, 0, 1, y_c - n.TAB_LEN / 2], [0, -1, 0, 0], [0, 0, 0, 1]], float)
    bridge = bridge.copy()
    bridge.apply_transform(T)
    scene = trimesh.Scene({"plaque": plaque, "bridge": bridge})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"assembly_{Path(a.data).stem}_{int(size)}.3mf"
    scene.export(str(path))
    print("wrote", path)


if __name__ == "__main__":
    main()
