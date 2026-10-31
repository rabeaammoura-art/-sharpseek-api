"""Slice STLs with Bambu Studio using the official Bambu Lab system profiles.

Usage: python bambu_slice.py [--support] [--printer NAME] [--process NAME]
                             [--filament NAME] [--plate TYPE] [--price-kg N] [--kwh-price N]
                             [--watts N] part.stl ...

Defaults: Bambu Lab H2D 0.4 nozzle, 0.20mm Standard, Bambu ASA, Textured PEI Plate.
Each part is sliced on its own plate; prints time, filament weight and cost per part and in total.
"""
import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from prices import DEFAULT_FILE, load_prices, price_for  # noqa: E402
OUT = ROOT / "out" / "bambu"
CLI = str(ROOT / "bambu-studio")


def profiles_dir() -> Path:
    loc = subprocess.check_output(
        ["flatpak", "info", "--user", "--show-location", "com.bambulab.BambuStudio"], text=True).strip()
    return Path(loc) / "files/share/BambuStudio/profiles/BBL"


def flatten(kind: str, name: str) -> dict:
    """Resolve the `inherits` chain; the CLI does not do it for loaded files."""
    index = {}
    for f in glob.glob(str(profiles_dir() / kind / "**/*.json"), recursive=True):
        try:
            d = json.load(open(f))
        except ValueError:
            continue
        if "name" in d:
            index[d["name"]] = d

    def resolve(n):
        d = index[n]
        merged = dict(resolve(d["inherits"])) if d.get("inherits") else {}
        merged.update(d)
        return merged

    d = resolve(name)
    d.pop("inherits", None)
    d["from"] = "system"
    return d


def plate_center(machine: dict) -> tuple:
    """Centre of the first extruder's area (an object must fit one nozzle's area on H2D)."""
    area = machine.get("extruder_printable_area", [",".join(machine["printable_area"])])[0]
    pts = [tuple(map(float, p.split("x"))) for p in area.split(",")]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


PER_FILAMENT_SINGLES = ("filament_colour", "filament_map", "filament_map_2", "filament_is_mixed", "filament_nozzle_map",
                        "filament_volume_map", "filament_change_length_nc", "default_filament_colour",
                        "default_filament_profile")


def prepare_3mf(src: Path, filament_files: list, part_dir: Path, base_cmd: list, tower=None, nozzle=1) -> Path:
    """Give a multi-colour 3MF a project_settings.config that matches the loaded filaments.

    The CLI expands most per-filament arrays when --load-filaments is used, but leaves a few
    (colour, map, ...) at length 1, which makes it crash with more than two filaments. We let the
    CLI write a project from a tiny cube, fix those arrays, and swap it into a copy of the 3MF."""
    import zipfile
    import trimesh
    n = len(filament_files)
    cube = part_dir / "cube.stl"
    trimesh.creation.box((10, 10, 10)).export(cube)
    with open(part_dir / "prep.log", "w") as log:
        subprocess.run(base_cmd + ["--arrange", "1", "--orient", "0", "--slice", "0", "--outputdir", str(part_dir),
                                   "--export-3mf", "prep.3mf", str(cube)], stdout=log, stderr=log)
    cfg = json.loads(zipfile.ZipFile(part_dir / "prep.3mf").read("Metadata/project_settings.config"))
    for k in PER_FILAMENT_SINGLES:
        if isinstance(cfg.get(k), list) and len(cfg[k]) == 1:
            cfg[k] = cfg[k] * n
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", [str(nozzle)] * n   # every colour on one nozzle (1 left, 2 right)
    cfg["skirt_loops"], cfg["brim_type"] = "0", "no_brim"                 # skirt/brim would leave the printable area beside a 300 mm plate
    # prime tower: explicit either way (the Bambu default adds one for multi-colour prints)
    cfg["enable_prime_tower"] = "1" if tower else "0"
    if tower:
        cfg["wipe_tower_x"], cfg["wipe_tower_y"], cfg["prime_tower_width"] = [str(tower[0])], [str(tower[1])], str(tower[2])
        cfg["prime_tower_brim_width"] = "0"   # the tower brim would not fit in the strip beside a 300 mm plate
    out = part_dir / "input.3mf"
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "Metadata/project_settings.config":
                data = json.dumps(cfg, indent=4).encode()
            zout.writestr(item, data)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--printer", default="Bambu Lab H2D 0.4 nozzle")
    ap.add_argument("--process", default="0.20mm Standard @BBL H2D")
    ap.add_argument("--filament", action="append",
                    help="filament profile name; repeat once per filament slot of a multi-colour 3MF "
                         "(default: Bambu ASA @BBL H2D 0.4 nozzle)")
    ap.add_argument("--plate", default="Textured PEI Plate")
    ap.add_argument("--tower-x", type=float, help="enable the prime tower at this x (mm) for multi-colour 3MF files; "
                    "without it NO tower is used, which under-estimates time and filament")
    ap.add_argument("--tower-y", type=float, default=140.0)
    ap.add_argument("--nozzle", type=int, default=1, choices=(1, 2), help="H2D nozzle for every colour: 1 = left (x 0-325), 2 = right (x 25-350)")
    ap.add_argument("--tower-width", type=float, default=40.0)
    ap.add_argument("--support", action="store_true", help="enable tree(auto) supports")
    ap.add_argument("--price-kg", type=float, default=None,
                    help="override: one filament price per kg (JOD) for every slot; "
                         "default: landed prices from config/filament_prices.xlsx")
    ap.add_argument("--prices-file", default=str(DEFAULT_FILE))
    ap.add_argument("--kwh-price", type=float, default=0.10, help="electricity price per kWh (JOD)")
    ap.add_argument("--watts", type=float, default=350.0, help="average printer power draw")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    machine = flatten("machine", a.printer)
    process = flatten("process", a.process)
    process["curr_bed_type"] = a.plate
    if a.support:
        process.update(enable_support="1", support_type="tree(auto)")
    # "profile name=Sheet type" prices a slot with another stock-sheet type, e.g.
    # "Bambu PLA Basic @BBL H2D=Walnut PLA" (printed with the PLA profile, priced as Walnut PLA)
    parsed = [(f.partition("=")[0].strip(), f.partition("=")[2].strip() or None)
              for f in (a.filament or ["Bambu ASA @BBL H2D 0.4 nozzle"])]
    filaments = [p for p, _ in parsed]
    overrides = [t for _, t in parsed]
    if a.price_kg is not None:
        slot_prices = [a.price_kg] * len(filaments)
        print(f"prices: {a.price_kg:.3f} JOD/kg (--price-kg)")
    else:
        sheet = load_prices(a.prices_file)
        resolved = []
        for fname, override in zip(filaments, overrides):
            if override is None:
                resolved.append(price_for(fname, sheet))
            elif override in sheet:
                resolved.append((override, sheet[override]))
            else:
                raise SystemExit(f"'{override}' is not in the price sheet (have: {', '.join(sheet)})")
        slot_prices = [p for _, p in resolved]
        print("prices (landed, from stock sheet): " + ", ".join(sorted({f"{t} {p:.3f} JOD/kg" for t, p in resolved})))
    for name, d in (("machine", machine), ("process", process)):
        json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    filament_files = []
    for i, fname in enumerate(filaments):
        f = OUT / f"filament{i}.json"
        json.dump(flatten("filament", fname), open(f, "w"), indent=1)
        filament_files.append(str(f))
    cx, cy = plate_center(machine)
    total_s = total_g = total_fil = 0.0

    for stl in map(Path, a.stl):
        part_dir = OUT / stl.stem
        part_dir.mkdir(exist_ok=True)
        base_cmd = [CLI, "--load-settings", f"{OUT / 'machine.json'};{OUT / 'process.json'}",
                    "--load-filaments", ";".join(filament_files)]
        if stl.suffix.lower() == ".3mf":
            # already positioned, parts carry their filament slots
            tower = (a.tower_x, a.tower_y, a.tower_width) if a.tower_x is not None else None
            centred = prepare_3mf(stl.resolve(), filament_files, part_dir, base_cmd, tower, a.nozzle) if len(filament_files) > 2 \
                else stl.resolve()
            print("prime tower: " + (f"ON at x={tower[0]:.0f} y={tower[1]:.0f} width={tower[2]:.0f}" if tower else "OFF (estimate excludes purge)"))
        else:
            centred = part_dir / "centred.stl"
            # The CLI does not move objects onto the plate; put the model at the nozzle-area centre.
            subprocess.run(["prusa-slicer", "--center", f"{cx},{cy}", "--export-stl", "-o", str(centred),
                            str(stl.resolve())], check=True, capture_output=True)
        with open(part_dir / "log.txt", "w") as log:
            subprocess.run([CLI, "--load-settings", f"{OUT / 'machine.json'};{OUT / 'process.json'}",
                            "--load-filaments", ";".join(filament_files), "--arrange", "0", "--orient", "0",
                            "--slice", "0", "--outputdir", str(part_dir), "--export-3mf", "out.3mf",
                            str(centred)], stdout=log, stderr=log)
        res = json.load(open(part_dir / "result.json"))
        if res["return_code"] != 0:
            print(f"{stl.stem}: FAILED - {res['error_string']} (see {part_dir / 'log.txt'})")
            continue
        plate = res["sliced_plates"][0]
        s = int(plate["total_predication"])
        grams = sum(f["total_used_g"] for f in plate["filaments"])
        fil_cost = sum(f["total_used_g"] / 1000 * slot_prices[min(int(f.get("id", i + 1)) - 1, len(slot_prices) - 1)]
                       for i, f in enumerate(plate["filaments"]))
        total_s += s
        total_g += grams
        total_fil += fil_cost
        print(f"{stl.stem}: {hm(s)}  {grams:.1f} g  {fil_cost + s / 3600 * a.watts / 1000 * a.kwh_price:.2f}"
              f"  -> {part_dir / 'out.3mf'}")
        if len(plate["filaments"]) > 1:
            print("  per filament: " + ", ".join(f"#{f.get('filament_id', i)} {f['total_used_g']:.1f} g"
                                                 for i, f in enumerate(plate["filaments"])))
        if plate["warning_message"]:
            print(f"  warning: {plate['warning_message']}")
    filament = total_fil
    power = total_s / 3600 * a.watts / 1000 * a.kwh_price
    print(f"TOTAL: {hm(total_s)}  {total_g:.1f} g  filament {filament:.2f} + electricity {power:.2f}"
          f" = {filament + power:.2f}")


def hm(seconds) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m"


if __name__ == "__main__":
    sys.exit(main())
