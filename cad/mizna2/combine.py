"""Put several coasters from cad/out/names on ONE plate (2 x 2, prime tower on the right).
Slots: 1 body tan (nozzle 2) | 2 black | 3 olive | 4 brown | 5 accent (nozzle 1).
  python cad/mizna2/combine.py OUT.3mf name1 name2 ..."""
import json, sys, zipfile
from pathlib import Path
import trimesh
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from threemf import write_bambu_3mf_multi  # noqa: E402

D = HERE.parent / "out" / "names"
SLOT = {"plate": 1, "black": 2, "olive": 3, "brown": 4}
ACCENT = {"duaa": ("lavender", "#B9A3D6"), "islam": ("cream", "#FFF3E0"), "maimouna": ("cream", "#FFF3E0")}   # default pink
PINK = ("pink", "#F2A6A0")
out, names = Path(sys.argv[1]), sys.argv[2:]
cfg = json.loads(zipfile.ZipFile(D / "haya.3mf").read("Metadata/project_settings.config"))   # 5-filament project settings
acc_of = {n: ACCENT.get(n, PINK) for n in names if (D / f"{n}_accent.stl").exists()}
acc_cols = list(dict.fromkeys(acc_of.values()))              # one slot per accent colour: 5, 6, ...
N = 4 + len(acc_cols)
cfg["filament_colour"] = ["#C8A578", "#141414", "#8F8B3A", "#B4703A"] + [h for _, h in acc_cols]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2"] + ["1"] * (N - 1)
cfg["filament_type"] = ["PLA"] * N
for k, v in list(cfg.items()):                                  # per-filament arrays: 5 -> N entries
    if N > 5 and isinstance(v, list) and len(v) == 5 and k not in ("filament_colour", "filament_map", "filament_type") and k.startswith(("filament", "nozzle_temp", "hot_plate", "cool_plate", "textured", "eng_plate", "supertack", "fan", "close_fan", "overhang_fan", "slow_down", "required_nozzle", "reduce_fan", "full_fan", "additional_", "activate_air", "temperature", "pre_start", "no_slow", "override_process", "impact", "volumetric", "long_retr", "retraction_dist", "chamber_temp", "during_print", "complete_print", "cooling_", "counter_", "hole_", "diameter_limit", "circle_comp")):
        v.extend([v[-1]] * (N - 5))
if "filament_self_index" in cfg:
    cfg["filament_self_index"] = [str(i) for i in range(1, N + 1)]
sx = sy = 100.0
objs = []
for i, n in enumerate(names):
    parts = [(k, trimesh.load(D / f"{n}_{k}.stl"), s) for k, s in SLOT.items() if (D / f"{n}_{k}.stl").exists()]
    if n in acc_of:
        parts.append(("accent", trimesh.load(D / f"{n}_accent.stl"), 5 + acc_cols.index(acc_of[n])))
    if len(names) <= 4:                      # 2 x 2, tower right of the plate (x 270, y 140)
        pos = (100.0 + sx * (i % 2), 110.0 + sy * (i // 2))
    else:                                    # 3 columns inside x 25-325 (both nozzles); the free 6th slot (275, 210) is for the tower
        pos = (75.0 + sx * (i % 3), 110.0 + sy * (i // 3))
    objs.append((n, parts, pos))
write_bambu_3mf_multi(out, objs, json.dumps(cfg, indent=4))
print("->", out, [(o[0], o[2]) for o in objs])
