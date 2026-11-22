"""Mizna v2 coaster, version 3 (owner 2026-11-22): beige body, black name + cloud + drops, two identical sprigs
(left sprig mirrored on the right, flowers removed), olive leaves, brown stems. Spools = the owner's photo:
tan spool on the external holder (body, nozzle 2), AMS: black, olive, copper-brown.
Needs cad/out/mizna2/layers.pkl (trace.py).   python cad/mizna2/build3d_v3.py [--stl]"""
import json, pickle, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "coaster")); sys.path.insert(0, str(HERE.parent))
import coaster as C  # noqa: E402
from threemf import write_bambu_3mf  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

FACE, T = 1.0, 3.0
NAMES = [("body_tan", "#C8A578"), ("text_black", "#141414"), ("leaves_olive", "#8F8B3A"), ("stems_copper", "#B4703A")]
NOZZLE = ["2", "1", "1", "1"]          # body from the external spool (nozzle 2), the rest from the AMS (nozzle 1)

L = pickle.load(open(HERE.parent / "out" / "mizna2" / "layers.pkl", "rb"))
b = list(L["brown"].geoms)
txt = [p for p in b if (-14 < p.centroid.y < 24.5 and abs(p.centroid.x) < 36) or (p.centroid.y > 24 and p.centroid.x > 10)]
drops = [q for q in L["lilac"].geoms if q.centroid.y > 0]
mir = lambda g: affinity.scale(g, -1, 1, origin=(0, 0))
lv = [p for p in L["olive"].geoms if p.centroid.x < 0]
st = [p for p in b if p not in txt and p.centroid.x < 0]
G = {"text_black": unary_union(txt + drops),
     "leaves_olive": unary_union(lv + [mir(p) for p in lv]),
     "stems_copper": unary_union(st + [mir(p) for p in st])}
disc = Point(0, 0).buffer(C.D / 2, 128)
body = disc.difference(unary_union(list(G.values())))
meshes = {"body_tan": C.trimesh.boolean.union([C.extrude(body, 0, FACE), C.extrude(disc, FACE, T)], engine="manifold")}
for k, g in G.items():
    meshes[k] = C.extrude(g, 0, FACE)
parts = [(n, C.mirror_x(meshes[n]), i + 1) for i, (n, _) in enumerate(NAMES)]
for n, m, _ in parts:
    print(f"{n}: z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f} faces {len(m.faces)} watertight {m.is_watertight}")
cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
cfg["filament_colour"] = [h for _, h in NAMES]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", NOZZLE
cfg["filament_type"] = ["PLA"] * 4
out = HERE.parent / "print_files" / "mizna2" / "mizna2_v3_95x3_facedown.3mf"
write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
print("->", out)
if "--stl" in sys.argv:
    for n, m, _ in parts:
        m.export(out.with_name(f"{out.stem}_{n}.stl"))
