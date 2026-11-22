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
# slots: 1 body beige, 2 name + stems dark brown, 3 cloud light brown, 4 flowers + drops purple, 5 leaves olive
NAMES = [("body", "#F4DCC8"), ("name", "#5B3A22"), ("cloud", "#B8895F"), ("flowers", "#D2A9D6"), ("leaves", "#A98C52")]

L = pickle.load(open(HERE.parent / "out" / "mizna2" / "layers.pkl", "rb"))
disc = Point(0, 0).buffer(C.D / 2, 128)
_b = [p for p in L["brown"].geoms]
L["cloud"] = unary_union([p for p in _b if p.centroid.y > 24 and p.centroid.x > 10])
L["name"] = unary_union([p for p in _b if not (p.centroid.y > 24 and p.centroid.x > 10)])
L["flowers"], L["leaves"] = L["lilac"], L["olive"]
art = unary_union([L[k] for k in ("name", "cloud", "flowers", "leaves")])
body = disc.difference(art)
meshes = {"body": C.extrude(body, 0, T)}
meshes["body"] = C.trimesh.util.concatenate([meshes["body"]]) if False else meshes["body"]
# body = pocketed layer (0..FACE) + solid top (FACE..T): one mesh from two extrusions
meshes["body"] = C.trimesh.boolean.union([C.extrude(body, 0, FACE), C.extrude(disc, FACE, T)], engine="manifold")
for k in ("name", "cloud", "flowers", "leaves"):
    meshes[k] = C.extrude(L[k], 0, FACE)
parts = [(n, C.mirror_x(meshes[n]), i + 1) for i, (n, _) in enumerate(NAMES)]
for n, m, _ in parts:
    print(f"{n}: z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f} faces {len(m.faces)} watertight {m.is_watertight}")
cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
cfg["filament_colour"] = [h for _, h in NAMES]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["1"] * 5
cfg["filament_type"] = ["PLA"] * 5
for k, v in list(cfg.items()):          # per-filament arrays: 4 -> 5 entries
    if isinstance(v, list) and len(v) == 4 and k not in ("filament_colour", "filament_map", "filament_type") and k.startswith(("filament", "nozzle_temp", "hot_plate", "cool_plate", "textured", "eng_plate", "fan", "close_fan", "overhang_fan", "slow_down", "required_nozzle", "flush", "enable_pressure", "pressure_advance", "temperature", "reduce_fan", "full_fan", "additional_cooling", "activate_air")):
        v.append(v[-1])
if "filament_self_index" in cfg:
    cfg["filament_self_index"] = [str(i) for i in range(1, 6)]
out = HERE.parent / "print_files" / "mizna2" / "mizna2_95x3_5colours_facedown.3mf"
out.parent.mkdir(parents=True, exist_ok=True)
write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
print("->", out)
if "--stl" in sys.argv:
    for n, m, _ in parts:
        m.export(out.with_name(f"{out.stem}_{n}.stl"))
