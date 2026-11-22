"""Mizna v2 coaster 3D (95 x 3 mm, face down like Mizna v1): body with pockets + coloured face layer 1 mm.
Needs cad/out/mizna2/layers.pkl from trace.py.   python cad/mizna2/build3d.py [--stl]"""
import json, pickle, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "coaster")); sys.path.insert(0, str(HERE.parent))
import coaster as C  # noqa: E402
from threemf import write_bambu_3mf  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

FACE, T = 1.0, 3.0
NAMES = [("body", "#F4DCC8"), ("brown", "#5B3A22"), ("lilac", "#D2A9D6"), ("olive", "#A98C52")]

L = pickle.load(open(HERE.parent / "out" / "mizna2" / "layers.pkl", "rb"))
disc = Point(0, 0).buffer(C.D / 2, 128)
art = unary_union([L[k] for k in ("brown", "lilac", "olive")])
body = disc.difference(art)
meshes = {"body": C.extrude(body, 0, T)}
meshes["body"] = C.trimesh.util.concatenate([meshes["body"]]) if False else meshes["body"]
# body = pocketed layer (0..FACE) + solid top (FACE..T): one mesh from two extrusions
meshes["body"] = C.trimesh.boolean.union([C.extrude(body, 0, FACE), C.extrude(disc, FACE, T)], engine="manifold")
for k in ("brown", "lilac", "olive"):
    meshes[k] = C.extrude(L[k], 0, FACE)
parts = [(n, C.mirror_x(meshes[n]), i + 1) for i, (n, _) in enumerate(NAMES)]
for n, m, _ in parts:
    print(f"{n}: z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f} faces {len(m.faces)} watertight {m.is_watertight}")
cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
cfg["filament_colour"] = [h for _, h in NAMES]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["1", "1", "1", "1"]
cfg["filament_type"] = ["PLA"] * 4
out = HERE.parent / "print_files" / "mizna2" / "mizna2_95x3_facedown.3mf"
out.parent.mkdir(parents=True, exist_ok=True)
write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
print("->", out)
if "--stl" in sys.argv:
    for n, m, _ in parts:
        m.export(out.with_name(f"{out.stem}_{n}.stl"))
