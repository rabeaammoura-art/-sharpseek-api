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
# slots (owner 2026-11-22): 1 body beige, 2 name + cloud light brown, 3 flowers + drops purple, 4 leaves + stems olive
NAMES = [("body", "#F4DCC8"), ("name_cloud", "#7A4A2B"), ("flowers", "#D2A9D6"), ("leaves_stems", "#A98C52")]

TEXT = sys.argv[sys.argv.index("--text") + 1] if "--text" in sys.argv else None   # e.g. --text "#141414": name + cloud in that colour
if TEXT:
    NAMES[1] = ("name_cloud", TEXT)
L = pickle.load(open(HERE.parent / "out" / "mizna2" / "layers.pkl", "rb"))
disc = Point(0, 0).buffer(C.D / 2, 128)
_b = [p for p in L["brown"].geoms]
_txt = [p for p in _b if (-14 < p.centroid.y < 24.5 and abs(p.centroid.x) < 36) or (p.centroid.y > 24 and p.centroid.x > 10)]
L["name_cloud"] = unary_union(_txt)
L["flowers"] = L["lilac"]
L["leaves_stems"] = unary_union([L["olive"]] + [p for p in _b if p not in _txt])
art = unary_union([L[k] for k in ("name_cloud", "flowers", "leaves_stems")])
body = disc.difference(art)
meshes = {"body": C.extrude(body, 0, T)}
meshes["body"] = C.trimesh.util.concatenate([meshes["body"]]) if False else meshes["body"]
# body = pocketed layer (0..FACE) + solid top (FACE..T): one mesh from two extrusions
meshes["body"] = C.trimesh.boolean.union([C.extrude(body, 0, FACE), C.extrude(disc, FACE, T)], engine="manifold")
BLACK = float(sys.argv[sys.argv.index("--black") + 1]) if "--black" in sys.argv else 0.0   # light-brown skin thickness over black
for k in ("name_cloud", "flowers", "leaves_stems"):
    meshes[k] = C.extrude(L[k], 0, BLACK if (k == "name_cloud" and BLACK) else FACE)
if BLACK:                                   # black behind the light brown (face is on the bed, so z > BLACK is behind it)
    NAMES.append(("black_under", "#141414"))
    meshes["black_under"] = C.extrude(L["name_cloud"], BLACK, FACE)
N = len(NAMES)
parts = [(n, C.mirror_x(meshes[n]), i + 1) for i, (n, _) in enumerate(NAMES)]
for n, m, _ in parts:
    print(f"{n}: z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f} faces {len(m.faces)} watertight {m.is_watertight}")
cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
cfg["filament_colour"] = [h for _, h in NAMES]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["1"] * N
cfg["filament_type"] = ["PLA"] * N
for k, v in list(cfg.items()):              # per-filament arrays: 4 -> N entries
    if N > 4 and isinstance(v, list) and len(v) == 4 and k.startswith(("filament", "nozzle_temp", "hot_plate", "cool_plate", "textured", "eng_plate", "supertack", "fan", "close_fan", "overhang_fan", "slow_down", "required_nozzle", "reduce_fan", "full_fan", "additional_", "activate_air", "temperature", "pre_start", "no_slow", "override_process", "impact", "volumetric", "long_retr", "retraction_dist", "chamber_temp", "during_print", "complete_print", "cooling_", "counter_", "hole_", "diameter_limit", "circle_comp")) and k not in ("filament_colour", "filament_map", "filament_type"):
        v.extend([v[-1]] * (N - 4))
if "filament_self_index" in cfg:
    cfg["filament_self_index"] = [str(i) for i in range(1, N + 1)]
out = HERE.parent / "print_files" / "mizna2" / ("mizna2_95x3_blackunder_facedown.3mf" if BLACK else "mizna2_95x3_blacktext_facedown.3mf" if TEXT else "mizna2_95x3_4colours_facedown.3mf")
out.parent.mkdir(parents=True, exist_ok=True)
write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
print("->", out)
if "--stl" in sys.argv:
    for n, m, _ in parts:
        m.export(out.with_name(f"{out.stem}_{n}.stl"))
