"""One 3-colour Bambu 3MF per column of the big (about 1 m) version: slot 1 black, 2 white, 3 orange; piece against the left edge of the plate, prime tower to its right.
Usage: python cad/wrench/workshop/make_3mf_big.py <v7_out_dir> <out_dir> [--tower-w 30]"""
import argparse, sys
from pathlib import Path
import trimesh
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from threemf import build_project_settings, write_bambu_3mf

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--tower-w", type=float, default=30.0)
ap.add_argument("--material", default="pla"); a = ap.parse_args(); src = Path(a.src); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
template = (Path(__file__).resolve().parents[2] / "config" / f"bambu_project_4fil_{a.material}.config").read_bytes()
colours = ["#1A1A1A", "#F2F2F2", "#FF7A00", "#1A1A1A"]
for k in range(1, 5):
    ms = {}
    for col in ("black", "white", "orange"):
        f = src / "stl" / f"column_{k}__{col}.stl"
        if f.exists(): ms[col] = trimesh.load(f)
    allm = trimesh.util.concatenate(list(ms.values())); b = allm.bounds; w, h = b[1][0] - b[0][0], b[1][1] - b[0][1]
    for m in ms.values(): m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, 0])
    cx = 4 + w / 2; cy = 160.0; tower_x = round(cx + w / 2 + 4, 1); tw = min(a.tower_w, 305 - tower_x)
    parts = [(c, m, i) for i, (c, m) in enumerate(ms.items(), start=1)]
    write_bambu_3mf(out / f"column_{k}.3mf", parts, center=(cx, cy), name=f"column_{k}", project_settings=build_project_settings(template, colours, (tower_x, 160.0, tw)))
    print(f"column_{k}: {w:.1f} x {h:.1f} mm, plate x {4:.0f}..{4 + w:.0f}, y {cy - h / 2:.0f}..{cy + h / 2:.0f}, tower x={tower_x} w={tw}")
