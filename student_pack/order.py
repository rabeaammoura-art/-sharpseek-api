"""Order automation: orders.csv -> print files + quote for every order.

    python order.py orders.csv                 # files + quote from the price catalog (instant)
    python order.py orders.csv --exact         # also slice every order's real pieces in Bambu Studio and quote from that
    python order.py orders.csv --plates        # + one plate 3MF per (theme, colours) group, two kids per plate (shared colour changes)

orders.csv columns (header required):
    order_id,name,theme,colors,pieces,qty
    1001,OSAYD,construction,2,all,1
    1002,Sally,cat,4,tag|ruler,2
`theme` = construction | cat, `colors` = 2 | 3 | 4, `pieces` = all or a | separated list of tag/pencil/ruler/bottle, `qty` optional.
Output: out/orders/<order_id>_<NAME>_<theme><colors>/ (3MF/STL/PNG/pack.json/report.json), out/orders/quotes.csv, and the table below.
"""
import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import generate
import pricing
from themes import BASE_THEMES, resolve_theme

HERE = Path(__file__).parent


def read_orders(path):
    rows = []
    for i, r in enumerate(csv.DictReader(open(path, newline="", encoding="utf-8-sig")), start=2):
        r = {k.strip(): (v or "").strip() for k, v in r.items()}
        if not r.get("name"):
            continue
        if r["theme"] not in BASE_THEMES:
            raise SystemExit(f"line {i}: theme {r['theme']!r} not in {BASE_THEMES}")
        colours = int(r.get("colors") or 4)
        if colours not in (2, 3, 4):
            raise SystemExit(f"line {i}: colors must be 2, 3 or 4")
        pcs = generate.PIECES if r.get("pieces", "all") in ("", "all") else tuple(x.strip() for x in r["pieces"].split("|"))
        bad = [x for x in pcs if x not in generate.PIECES]
        if bad:
            raise SystemExit(f"line {i}: unknown pieces {bad}")
        rows.append(dict(order_id=r.get("order_id") or str(len(rows) + 1), name=r["name"], base=r["theme"], colours=colours,
                         pieces=pcs, qty=int(r.get("qty") or 1)))
    return rows


def exact_numbers(out_dir, stem_pieces):
    files = [out_dir / f"{s}.3mf" for s in stem_pieces]
    subprocess.run([sys.executable, str(HERE / "verify_slice.py"), *map(str, files)], capture_output=True, text=True)
    res = {}
    for s in stem_pieces:
        pl = json.loads((HERE / "out" / "bambu" / s / "result.json").read_text())["sliced_plates"][0]
        res[s] = (int(pl["total_predication"]), sum(f["total_used_g"] for f in pl["filaments"]))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--out", default=str(HERE / "out" / "orders"))
    ap.add_argument("--exact", action="store_true")
    ap.add_argument("--plates", action="store_true")
    a = ap.parse_args()
    prices = pricing.load_prices()
    cat = json.loads(pricing.CATALOG.read_text()) if pricing.CATALOG.exists() else {}
    cur = prices["currency"]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    quote_rows, groups = [], {}
    print(f"{'order':>6s} {'name':12s} {'theme':13s}{'col':>4s} {'pieces':22s}{'qty':>4s}{'each':>8s}{'total':>9s}  ({cur}, assumed margins)")
    for o in read_orders(a.csv):
        theme = resolve_theme(o["base"], o["colours"])
        d = out / f"{o['order_id']}_{re.sub(r'[^A-Za-z0-9]+', '', o['name']).upper()}_{theme}"
        generate.build(o["name"], theme, d.parent / d.name, o["pieces"], False)
        gen_dir = d.parent / d.name / f"{re.sub(r'[^A-Za-z0-9]+', '_', o['name']).strip('_').upper()}_{theme}"
        stem_base = re.sub(r"[^A-Za-z0-9]+", "_", o["name"]).strip("_").lower()
        stems = {k: f"{stem_base}_{k}" for k in o["pieces"]}
        numbers = {}
        if a.exact:
            ex = exact_numbers(gen_dir, list(stems.values()))
            numbers = {k: ex[s] for k, s in stems.items()}
        else:
            for k in o["pieces"]:
                e = cat.get(pricing.key(o["base"], o["colours"], k))
                if not e:
                    raise SystemExit("no catalog numbers: run  python pricing.py --catalog  first (or use --exact)")
                numbers[k] = (e["seconds"], e["grams"])
        each, piece_costs, cost_total = pricing.quote(prices, cat, o["base"], o["colours"], o["pieces"], numbers if a.exact else None)
        label = "PACK" if set(o["pieces"]) == set(generate.PIECES) else "|".join(o["pieces"])
        total = each * o["qty"]
        piece_prices = {k: round(c, 2) for k, c in piece_costs.items()}
        hours = sum(s for s, _ in numbers.values()) / 3600
        print(f"{o['order_id']:>6s} {o['name']:12s} {theme:13s}{o['colours']:>4d} {label:22s}{o['qty']:>4d}{each:>8.2f}{total:>9.2f}   ~{hours:.1f} h print, {sum(g for _, g in numbers.values()):.0f} g, cost {cost_total:.2f}")
        quote_rows.append(dict(order_id=o["order_id"], name=o["name"], theme=o["base"], colors=o["colours"], pieces=label, qty=o["qty"],
                               price_each=f"{each:.2f}", total=f"{total:.2f}", print_hours=f"{hours:.2f}",
                               grams=f"{sum(g for _, g in numbers.values()):.0f}", files=str(gen_dir), cost_each=f"{cost_total:.2f}"))
        groups.setdefault((o["base"], o["colours"]), []).extend([(o["name"], theme)] * o["qty"])
    with open(out / "quotes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(quote_rows[0])); w.writeheader(); w.writerows(quote_rows)
    print(f"\nGrand total {sum(float(r['total']) for r in quote_rows):.2f} {cur}   (quotes: {out / 'quotes.csv'})")
    if a.plates:
        for (base, colours), jobs in groups.items():
            for i in range(0, len(jobs), 2):                      # two kids per plate = the most that fits
                generate.build_plate(jobs[i:i + 2], out / "plates", generate.PIECES, False)


if __name__ == "__main__":
    main()
