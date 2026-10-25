"""Price list for the student pack: slice every theme x colours x piece once (catalog), then quote any order from it.

    python pricing.py --catalog            # slice 2 themes x 3 colour counts x 4 pieces (~30 min, 3 in parallel) -> catalog.json
    python pricing.py                      # print the price table from catalog.json + prices.json

Cost per piece = filament (model + purge grams) + machine time (electricity + hourly rate) + labour.
Selling price = cost * (1 + markup), rounded UP to `round_up_to`.  Pack = sum of pieces - pack_discount + packaging.
All money numbers live in prices.json (the shipped values are assumptions - set your own).
"""
import argparse
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import generate
from themes import BASE_THEMES, resolve_theme

HERE = Path(__file__).parent
CATALOG = HERE / "catalog.json"
PRICES = HERE / "prices.json"
PIECES = generate.PIECES
SAMPLE_NAME = "LAYLA"            # 5 letters = typical name length; real orders can differ a little


def load_prices(material=None):
    """prices.json; `material` (or its "material" key) picks the landed JOD/kg from the filament sheet."""
    p = json.loads(PRICES.read_text())
    if "materials" in p:
        p["material"] = material or p["material"]
        p["filament_per_kg"] = p["materials"][p["material"]]
    return p


def piece_cost(p, seconds, grams):
    return grams / 1000 * p["filament_per_kg"] + seconds / 3600 * (p["printer_watts"] / 1000 * p["electricity_per_kwh"] + p["machine_hour_rate"]) + p["labor_per_piece"]


def round_up(x, step):
    return math.ceil(x / step - 1e-9) * step


def piece_price(p, seconds, grams):
    return round_up(piece_cost(p, seconds, grams) * (1 + p["markup"]), p["round_up_to"])


def quote(p, cat, base, colours, pieces, numbers=None):
    """Selling price for an order line.  Full pack = fixed `pack_price`; a partial order = the pieces' share of the pack price
    x `single_premium`, rounded up.  `numbers` = {piece: (seconds, grams)} from an exact slice, else the catalog.
    Returns (price_each, {piece: cost}, pack_cost)."""
    num = {k: (cat[key(base, colours, k)]["seconds"], cat[key(base, colours, k)]["grams"]) for k in PIECES}
    if numbers:
        num.update(numbers)
    cost = {k: piece_cost(p, *num[k]) for k in PIECES}
    full = sum(cost.values()) + p["packaging_per_pack"]
    if set(pieces) == set(PIECES):
        return p["pack_price"], {k: cost[k] for k in pieces}, full
    share = sum(cost[k] for k in pieces) / sum(cost.values())
    return round_up(p["pack_price"] * share * p["single_premium"], p["round_up_to"]), {k: cost[k] for k in pieces}, sum(cost[k] for k in pieces) + p["packaging_per_pack"]


def pack_price(p, piece_prices):
    if p.get("pack_price"):
        return p["pack_price"]
    return round_up(sum(piece_prices) * (1 - p["pack_discount"]) + p["packaging_per_pack"], p["round_up_to"])


def key(theme, colours, piece):
    return f"{theme}:{colours}:{piece}"


def slice_one(args):
    path, stem = args
    subprocess.run([sys.executable, str(HERE / "verify_slice.py"), str(path)], capture_output=True, text=True)
    res = json.loads((HERE / "out" / "bambu" / stem / "result.json").read_text())
    pl = res["sliced_plates"][0]
    return stem, {"seconds": int(pl["total_predication"]),
                  "grams": round(sum(f["total_used_g"] for f in pl["filaments"]), 2),
                  "model_g": round(sum(f["main_used_g"] for f in pl["filaments"]), 2)}


def build_catalog(jobs=3, themes=BASE_THEMES):
    work, names = [], {}
    for base in themes:
        for colours in (2, 3, 4):
            theme = resolve_theme(base, colours)
            for kind in PIECES:
                piece = generate.layout.KINDS[kind](theme, SAMPLE_NAME)
                stem = f"cat_{theme}_{kind}"
                d = HERE / "out" / "catalog"
                generate.mesh.export_piece(piece, d, stem)
                work.append((d / f"{stem}.3mf", stem)); names[stem] = key(base, colours, kind)
    cat = json.loads(CATALOG.read_text()) if CATALOG.exists() else {}
    with ThreadPoolExecutor(jobs) as ex:
        for stem, r in ex.map(slice_one, work):
            cat[names[stem]] = r
            print(names[stem], r, flush=True)
    cat["_meta"] = {"sample_name": SAMPLE_NAME, "printer": "Bambu Lab H2D 0.4", "process": "0.20mm Standard", "filament": "Bambu PETG Basic"}
    CATALOG.write_text(json.dumps(cat, indent=1))


def table(material=None):
    cat, p = json.loads(CATALOG.read_text()), load_prices(material)
    print(f"{p['currency']}, filament {p['material']} at {p['filament_per_kg']}/kg landed, electricity {p['electricity_per_kwh']}/kWh, packaging {p['packaging_per_pack']}. "
          f"Machine time and labour not charged.\n")
    print(f"{'theme':13s}{'col':>4s}{'cost':>8s}{'price':>8s}{'profit':>8s}{'margin':>8s}   single piece prices ({'/'.join(PIECES)})   hours  grams")
    for base in BASE_THEMES:
        for colours in (2, 3, 4):
            price, costs, full = quote(p, cat, base, colours, PIECES)
            singles = [quote(p, cat, base, colours, (k,))[0] for k in PIECES]
            hrs = sum(cat[key(base, colours, k)]["seconds"] for k in PIECES) / 3600
            g = sum(cat[key(base, colours, k)]["grams"] for k in PIECES)
            print(f"{base:13s}{colours:>4d}{full:>8.2f}{price:>8.2f}{price - full:>8.2f}{(price - full) / price:>8.0%}   " + " / ".join(f"{x:.2f}" for x in singles) + f"   {hrs:.1f}h  {g:.0f}g")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--material", help="PETG | AD-PETG | PLA+ | ... (keys of prices.json materials)")
    a = ap.parse_args()
    build_catalog(a.jobs) if a.catalog else table(a.material)
