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
SLOT = {"plate": 1, "black": 2, "olive": 3, "brown": 4, "accent": 5}
out, names = Path(sys.argv[1]), sys.argv[2:]
cfg = json.loads(zipfile.ZipFile(D / "haya.3mf").read("Metadata/project_settings.config"))   # 5-filament project settings
cfg["filament_colour"] = ["#C8A578", "#141414", "#8F8B3A", "#B4703A", "#F2A6A0"]
cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1", "1"]
sx = sy = 100.0
objs = []
for i, n in enumerate(names):
    parts = [(k, trimesh.load(D / f"{n}_{k}.stl"), s) for k, s in SLOT.items() if (D / f"{n}_{k}.stl").exists()]
    objs.append((n, parts, (100.0 + sx * (i % 2), 110.0 + sy * (i // 2))))
write_bambu_3mf_multi(out, objs, json.dumps(cfg, indent=4))
print("->", out, [(o[0], o[2]) for o in objs])
