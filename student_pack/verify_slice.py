"""Slice student-pack 3MFs in Bambu Studio (official H2D profiles, 4 AMS filaments) -> time + grams + cost.

    python verify_slice.py out/OSAYD_construction/*.3mf [--filament "Bambu PETG Basic @BBL H2D 0.4 nozzle"]

Defaults: Bambu Lab H2D 0.4 nozzle, 0.20mm Standard, Bambu PETG Basic, 4 AMS filaments (one per colour, colours
read from the 3MF), prime tower parked at the plate corner.  The estimate includes colour changes and the
purge/flush waste, which is why total grams are well above the model's own weight.

Needs the Bambu Studio toolchain from ../cad/setup.sh.  Results land in out/bambu/<name>/ (sliced 3MF + log).
"""
import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "cad"))
import bambu_slice as bs   # noqa: E402  (reuse the profile flattening / plate helpers)

OUT = HERE / "out" / "bambu"


def set_plate_position(src: Path, dst: Path, cx, cy):
    """Copy the 3MF with every build item moved from the generator's (128, 128) plate centre to the real plate centre."""
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zi.namelist():
            data = zi.read(n)
            if n == "3D/3dmodel.model":
                s = data.decode()
                s = re.sub(r'(<item objectid="\d+" transform="1 0 0 0 1 0 0 0 1 )([-\d.]+) ([-\d.]+)',
                           lambda m: f"{m.group(1)}{float(m.group(2)) + cx - 128:.3f} {float(m.group(3)) + cy - 128:.3f}", s)
                data = s.encode()
            zo.writestr(n, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--printer", default="Bambu Lab H2D 0.4 nozzle")
    ap.add_argument("--process", default="0.20mm Standard @BBL H2D")
    ap.add_argument("--filament", default="Bambu PETG Basic @BBL H2D 0.4 nozzle")
    ap.add_argument("--plate", default="Textured PEI Plate")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="override a process setting (value as JSON, e.g. flush_multiplier=[\"0.3\"])")
    ap.add_argument("--price-kg", type=float, default=8.0)
    ap.add_argument("--kwh-price", type=float, default=0.10)
    ap.add_argument("--watts", type=float, default=350.0)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    machine, process = bs.flatten("machine", a.printer), bs.flatten("process", a.process)
    process["curr_bed_type"] = a.plate
    pa = (machine.get("extruder_printable_area") or [",".join(machine["printable_area"])])[0]
    pts = [tuple(map(float, p.split("x"))) for p in pa.split(",")]
    cx, cy = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2, (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
    process.update(wipe_tower_x=[str(int(cx + 100))], wipe_tower_y=["10"])   # prime tower in the free right-hand strip
    for kv in a.set:
        k, v = kv.split("=", 1)
        v = json.loads(v)
        process[k] = [str(x) for x in v] if isinstance(v, list) else str(v)   # presets want strings
    fil = bs.flatten("filament", a.filament)
    for n, d in (("machine", machine), ("process", process), ("filament", fil)):
        json.dump(d, open(OUT / f"{n}.json", "w"), indent=1)
    tot_s = tot_g = 0.0
    for f in map(Path, a.files):
        d = OUT / f.stem
        d.mkdir(exist_ok=True)
        src = d / "in.3mf"
        set_plate_position(f, src, cx, cy)
        # the CLI sizes the filament list from the loaded presets: give each AMS slot its own file + colour
        cols = json.loads(zipfile.ZipFile(f).read("Metadata/project_settings.config"))["filament_colour"]
        files = []
        for i, c in enumerate(cols, 1):
            json.dump(dict(fil, filament_colour=[c], name=f"{fil['name']} slot{i}"), open(d / f"filament_{i}.json", "w"), indent=1)
            files.append(str(d / f"filament_{i}.json"))
        with open(d / "log.txt", "w") as log:
            subprocess.run([bs.CLI, "--load-settings", f"{OUT / 'machine.json'};{OUT / 'process.json'}",
                            "--load-filaments", ";".join(files),
                            "--arrange", "0", "--orient", "0", "--slice", "0",
                            "--outputdir", str(d), "--export-3mf", "out.3mf", str(src)], stdout=log, stderr=log)
        res = json.load(open(d / "result.json"))
        if res["return_code"] != 0:
            print(f"{f.stem}: FAILED - {res['error_string']} (see {d / 'log.txt'})")
            continue
        plate = res["sliced_plates"][0]
        s = int(plate["total_predication"])
        per = {x.get("id", i): round(x["total_used_g"], 2) for i, x in enumerate(plate["filaments"])}
        g = sum(x["total_used_g"] for x in plate["filaments"])
        net = sum(x["main_used_g"] for x in plate["filaments"])
        tot_s += s; tot_g += g
        cost = g / 1000 * a.price_kg + s / 3600 * a.watts / 1000 * a.kwh_price
        print(f"{f.stem}: {bs.hm(s)}  {g:.1f} g (model {net:.1f} + purge {g - net:.1f})  {cost:.2f} JOD  per-filament g: {per}")
        if plate["warning_message"]:
            print(f"  warning: {plate['warning_message']}")
    print(f"TOTAL: {bs.hm(tot_s)}  {tot_g:.1f} g")


if __name__ == "__main__":
    main()
