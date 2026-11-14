"""Export the cleaned bear poses (clean_bears.py -> poses.pkl) to cad/poses/poses.json for the plaque generator.
Usage: python cad/poses/export_poses.py <poses.pkl> [cad/poses/poses.json]
Per pose and role (body / cream / navy / yellow): list of polygons [[exterior], [hole], ...] in px, y UP, origin = bottom centre of the
bear (without its cloud). The cloud under the sleeping / cheering bear is dropped (the plaque has its own name cloud)."""
import json
import pickle
import sys
from pathlib import Path

from shapely import affinity
from shapely.ops import unary_union

src = pickle.load(open(sys.argv[1], "rb"))
dst = Path(sys.argv[2] if len(sys.argv) > 2 else Path(__file__).with_name("poses.json"))
out = {}
for name, roles in src.items():
    cream = roles["cream"]
    parts = list(cream.geoms) if hasattr(cream, "geoms") else [cream]
    if name in ("sleep", "cheer"):
        cloud = max(parts, key=lambda p: p.area)
        parts = [p for p in parts if p is not cloud]
    roles = {**roles, "cream": unary_union(parts)}
    ref = unary_union([roles["body"], roles["yellow"]])
    x0, y0, x1, y1 = ref.bounds
    def norm(g):
        g = affinity.scale(g, 1, -1, origin=(0, 0))                    # y up
        return affinity.translate(g, -(x0 + x1) / 2, y0)               # after flip the old y1 is -y1 .. bottom = -y1
    # flipped bottom is -y1 -> translate so bottom = 0
    def norm2(g):
        g = affinity.scale(g, 1, -1, origin=(0, 0))
        return affinity.translate(g, -(x0 + x1) / 2, y1)
    out[name] = {"size": [x1 - x0, y1 - y0], "roles": {}}
    for role, g in roles.items():
        g = norm2(g)
        polys = []
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            if p.is_empty or p.geom_type != "Polygon":
                continue
            polys.append([[(round(x, 1), round(y, 1)) for x, y in p.exterior.coords]] +
                         [[(round(x, 1), round(y, 1)) for x, y in r.coords] for r in p.interiors])
        out[name]["roles"][role] = polys
    print(name, [round(v) for v in out[name]["size"]], {r: len(v) for r, v in out[name]["roles"].items()})
dst.write_text(json.dumps(out))
print("wrote", dst, dst.stat().st_size // 1024, "KB")
