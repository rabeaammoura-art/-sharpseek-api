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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--printer", default="Bambu Lab H2D 0.4 nozzle")
    ap.add_argument("--process", default="0.20mm Standard @BBL H2D")
    ap.add_argument("--filament", default="Bambu ASA @BBL H2D 0.4 nozzle")
    ap.add_argument("--plate", default="Textured PEI Plate")
    ap.add_argument("--support", action="store_true", help="enable tree(auto) supports")
    ap.add_argument("--price-kg", type=float, default=30.0, help="filament price per kg")
    ap.add_argument("--kwh-price", type=float, default=0.20, help="electricity price per kWh")
    ap.add_argument("--watts", type=float, default=350.0, help="average printer power draw")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    machine = flatten("machine", a.printer)
    process = flatten("process", a.process)
    process["curr_bed_type"] = a.plate
    if a.support:
        process.update(enable_support="1", support_type="tree(auto)")
    for name, d in (("machine", machine), ("process", process), ("filament", flatten("filament", a.filament))):
        json.dump(d, open(OUT / f"{name}.json", "w"), indent=1)
    cx, cy = plate_center(machine)
    total_s = total_g = 0.0

    for stl in map(Path, a.stl):
        part_dir = OUT / stl.stem
        part_dir.mkdir(exist_ok=True)
        centred = part_dir / "centred.stl"
        # The CLI does not move objects onto the plate; put the model at the nozzle-area centre.
        subprocess.run(["prusa-slicer", "--center", f"{cx},{cy}", "--export-stl", "-o", str(centred),
                        str(stl.resolve())], check=True, capture_output=True)
        with open(part_dir / "log.txt", "w") as log:
            subprocess.run([CLI, "--load-settings", f"{OUT / 'machine.json'};{OUT / 'process.json'}",
                            "--load-filaments", str(OUT / "filament.json"), "--arrange", "0", "--orient", "0",
                            "--slice", "0", "--outputdir", str(part_dir), "--export-3mf", "out.3mf",
                            str(centred)], stdout=log, stderr=log)
        res = json.load(open(part_dir / "result.json"))
        if res["return_code"] != 0:
            print(f"{stl.stem}: FAILED - {res['error_string']} (see {part_dir / 'log.txt'})")
            continue
        plate = res["sliced_plates"][0]
        s = int(plate["total_predication"])
        grams = sum(f["total_used_g"] for f in plate["filaments"])
        total_s += s
        total_g += grams
        print(f"{stl.stem}: {hm(s)}  {grams:.1f} g  {cost(s, grams, a):.2f}  -> {part_dir / 'out.3mf'}")
        if plate["warning_message"]:
            print(f"  warning: {plate['warning_message']}")
    filament = total_g / 1000 * a.price_kg
    power = total_s / 3600 * a.watts / 1000 * a.kwh_price
    print(f"TOTAL: {hm(total_s)}  {total_g:.1f} g  filament {filament:.2f} + electricity {power:.2f}"
          f" = {filament + power:.2f}")


def hm(seconds) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m"


def cost(seconds, grams, a) -> float:
    return grams / 1000 * a.price_kg + seconds / 3600 * a.watts / 1000 * a.kwh_price


if __name__ == "__main__":
    sys.exit(main())
