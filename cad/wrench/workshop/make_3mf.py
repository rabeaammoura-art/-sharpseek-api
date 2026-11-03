"""Pack the v5 STLs into one 3-colour Bambu Studio 3MF (slot 1 black, 2 white, 3 orange, slot 4 spare), PLA template, prime tower beside the piece.
Usage: python cad/wrench/workshop/make_3mf.py <v5_out_dir> <out.3mf> [--tower-x 150 --tower-y 230 --tower-w 30]"""
import argparse, sys
from pathlib import Path
import trimesh
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from threemf import build_project_settings, write_bambu_3mf

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--tower-x", type=float, default=150.0); ap.add_argument("--tower-y", type=float, default=230.0); ap.add_argument("--tower-w", type=float, default=30.0)
ap.add_argument("--material", default="pla", choices=("pla", "petg")); ap.add_argument("--scale", type=float, default=1.0, help="uniform scale of the whole piece (scale test print)")
a = ap.parse_args(); src = Path(a.src)
load = lambda *names: trimesh.util.concatenate([trimesh.load(src / "stl" / f"{n}.stl") for n in names])
black = load("body__black", "workshop__black", "hooks__black"); white = load("workshop__white"); orange = load("body__orange", "workshop__orange")
allm = trimesh.util.concatenate([black, white, orange]); b = allm.bounds
mid = ((b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2)
for m in (black, white, orange):
    m.apply_translation([-mid[0], -mid[1], 0]); m.apply_scale(a.scale)                  # centre the piece on its own origin, then scale (scale test)
center = (162.5, 100.0)                                                           # plate position (x 12.5..312.5 for 300 mm; left nozzle reaches 325)
template = (Path(__file__).resolve().parents[2] / "config" / f"bambu_project_4fil_{a.material}.config").read_bytes()
colours = ["#1A1A1A", "#F2F2F2", "#FF7A00", "#1A1A1A"]
write_bambu_3mf(a.out, [("black", black, 1), ("white", white, 2), ("orange", orange, 3)], center=center, name=Path(a.out).stem,
                project_settings=build_project_settings(template, colours, (a.tower_x, a.tower_y, a.tower_w)))
print("wrote", a.out, "piece", ((b[1] - b[0]) * a.scale).round(1).tolist(), "at", center, "scale", a.scale)
