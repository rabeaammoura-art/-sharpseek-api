"""Flatten Bambu Studio presets for the command line.

The Bambu Studio CLI reads only the keys present in each JSON file; it does not walk the
`inherits` chain the way the GUI does. This resolves the chain against the system profiles
shipped with Bambu Studio and writes complete presets.

Usage: python flatten.py <BBL profiles dir> <out dir>
Writes machine.json, process.json, filament_<colour>.json for the W115 lens on an H2D.
"""
import json
import sys
from pathlib import Path

MACHINE = "Bambu Lab H2D 0.4 nozzle"
HERE = Path(__file__).parent
USER_PRESETS = ["process_w115.json", "filament_red.json", "filament_clear.json", "filament_amber.json"]


def index_profiles(root: Path):
    by_name = {}
    for f in root.rglob("*.json"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(j, dict) and "name" in j and "type" in j:
            by_name[(j["type"], j["name"])] = j
    return by_name


def resolve(by_name, kind, preset):
    """Merge the inherits chain, parents first; the preset's own keys win."""
    chain = [preset]
    while chain[-1].get("inherits"):
        parent = by_name.get((kind, chain[-1]["inherits"]))
        if parent is None:
            raise KeyError(f"{kind} preset '{chain[-1]['inherits']}' not found")
        chain.append(parent)
    merged = {}
    for p in reversed(chain):
        merged.update(p)
    return merged


def main(profiles_dir, out_dir):
    by_name = index_profiles(Path(profiles_dir))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    machine = resolve(by_name, "machine", by_name[("machine", MACHINE)])
    machine.update({"from": "system", "inherits": "", "name": MACHINE})
    (out / "machine.json").write_text(json.dumps(machine, indent=1))

    for fname in USER_PRESETS:
        user = json.loads((HERE / fname).read_text())
        kind = user["type"]
        flat = resolve(by_name, kind, user)
        flat.update({"from": "User", "inherits": user["inherits"], "name": user["name"]})
        if MACHINE not in flat.get("compatible_printers", [MACHINE]):
            raise ValueError(f"{fname}: '{user['inherits']}' is not compatible with {MACHINE}")
        target = "process.json" if kind == "process" else fname
        (out / target).write_text(json.dumps(flat, indent=1))
        print(f"{target}: {len(flat)} keys, inherits '{user['inherits']}'")
    print(f"machine.json: {len(machine)} keys")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
