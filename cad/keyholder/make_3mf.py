"""Pack the key-holder STLs into one 3-colour Bambu Studio 3MF (1 black, 2 red, 3 white; slot 4 spare), PLA template, prime tower beside the piece.
Usage: python cad/keyholder/make_3mf.py <out_dir_with_stl> <out.3mf> [--tower-x 150 --tower-y 235 --tower-w 30]"""
import argparse, sys
from pathlib import Path
import trimesh
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from threemf import build_project_settings, write_bambu_3mf

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--tower-x", type=float, default=150.0); ap.add_argument("--tower-y", type=float, default=235.0); ap.add_argument("--tower-w", type=float, default=30.0)
ap.add_argument("--material", default="pla", choices=("pla", "petg"))
a = ap.parse_args(); src = Path(a.src)
parts = {n: trimesh.load(src / "stl" / f"keyholder__{n}.stl") for n in ("black", "red", "white")}
allm = trimesh.util.concatenate(list(parts.values())); b = allm.bounds
mid = ((b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2)
for m in parts.values():
    m.apply_translation([-mid[0], -mid[1], 0])
template = (Path(__file__).resolve().parents[1] / "config" / f"bambu_project_4fil_{a.material}.config").read_bytes()
colours = ["#1A1A1A", "#C4161C", "#F2F2F2", "#1A1A1A"]
write_bambu_3mf(a.out, [("black", parts["black"], 1), ("red", parts["red"], 2), ("white", parts["white"], 3)], center=(162.5, 100.0),
                name=Path(a.out).stem, project_settings=build_project_settings(template, colours, (a.tower_x, a.tower_y, a.tower_w)))
print("wrote", a.out, "piece", (b[1] - b[0]).round(1).tolist())
