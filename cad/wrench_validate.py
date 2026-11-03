"""Validation of the wrench key holder STLs: watertight, interference between components, size vs bed (325 mm)."""
import itertools, sys
from pathlib import Path
import trimesh

out = Path(sys.argv[1])
ms = {f.stem: trimesh.load(f) for f in sorted((out / "stl").glob("*.stl"))}
bad = 0
for k, m in ms.items():
    ok = m.is_watertight
    bad += not ok
    ext = m.extents
    print(f"{k:24s} watertight={ok} extents={ext[0]:.0f}x{ext[1]:.0f}x{ext[2]:.0f} fits_bed={max(ext[:2]) < 300}")
# interference between components of the same variant (assembled positions): overlap of bounding boxes then boolean volume
def inter(a, b):
    try:
        return a.intersection(b, engine="manifold").volume
    except Exception:
        return None
names = [k for k in ms if not k.startswith("brake_")]
pairs = 0
for a, b in itertools.combinations(names, 2):
    if a.split("__")[0] == b.split("__")[0]:
        continue                       # colours of one part touch by design
    ma, mb = ms[a], ms[b]
    if (ma.bounds[1] < mb.bounds[0] - 1e-6).any() or (mb.bounds[1] < ma.bounds[0] - 1e-6).any():
        continue
    v = inter(ma, mb); pairs += 1
    if v is None or v > 1.0:
        print("INTERFERENCE", a, b, v)
for var in ("disc", "drum"):
    for b in [k for k in ms if k.startswith(f"brake_{var}")]:
        for a in names:
            ma = ms[a]
            if (ma.bounds[1] < ms[b].bounds[0]).any() or (ms[b].bounds[1] < ma.bounds[0]).any():
                continue
            v = inter(ma, ms[b])
            if v is None or v > 1.0:
                print("INTERFERENCE", a, b, v)
print("non-watertight:", bad, "| pairs checked:", pairs)
