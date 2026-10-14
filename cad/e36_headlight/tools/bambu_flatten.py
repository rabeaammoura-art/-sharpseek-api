"""Resolve Bambu Studio system profiles ('inherits' chains) into standalone JSON for the CLI.
usage: bambu_flatten.py <profiles/BBL dir> <kind> <name> <out.json> [key=value ...]"""
import sys, json
from pathlib import Path
root, kind, name, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
idx = {}
for p in (root / kind).glob("*.json"):
    try:
        d = json.loads(p.read_text())
        idx[d.get("name", p.stem)] = d
    except Exception:
        pass
def resolve(n):
    d = dict(idx[n]); parent = d.get("inherits")
    if parent:
        base = resolve(parent); base.update(d); d = base
    return d
d = resolve(name); d.pop("inherits", None)
pass  # keep system names and compatibility lists: the CLI checks them
for kv in sys.argv[5:]:
    k, v = kv.split("=", 1)
    d[k] = v if not v.startswith("[") else json.loads(v)
Path(out).write_text(json.dumps(d, indent=1)); print(out, len(d), "keys")
