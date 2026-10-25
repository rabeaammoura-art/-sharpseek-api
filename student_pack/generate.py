"""Parametric student-pack generator: type a name + theme -> tag, pencil, ruler and bottle tag.

    python generate.py --name OSAYD --theme construction
    python generate.py --name "Lina" --theme cat --out out --pieces tag,ruler
    python generate.py --pack OSAYD:construction SALLY:cat      # several kids at once
    python generate.py --name OSAYD --theme construction --slice   # + Bambu Studio time/grams per piece
    python generate.py --list-themes

Per piece it writes, under out/<NAME>_<theme>/:
    <name>_<piece>.3mf          one object, one part per colour (named by colour, extruder = AMS slot)
    <name>_<piece>.stl          all colours merged;  <name>_<piece>_<colour>.stl  one STL per colour
    <name>_<piece>.png          top-down colour preview
    pack.json                   exact polygons + layer heights (read by fusion360/StudentPack.py)
    report.json                 sizes, volumes, checks (hole sizes, wall thickness, minimum feature, ...)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from shapely.geometry import Point

import layout
import mesh
import preview
from layout import MIN_FEATURE, _polys, opening
from themes import THEMES

HERE = Path(__file__).parent
PIECES = ("tag", "pencil", "ruler", "bottle")


def poly_json(g):
    return [{"ext": [[round(x, 3), round(y, 3)] for x, y in p.exterior.coords[:-1]],
             "holes": [[[round(x, 3), round(y, 3)] for x, y in r.coords[:-1]] for r in p.interiors]} for p in _polys(g)]


def checks(piece):
    """Print-readiness checks; returns (dict, [problems])."""
    res, bad = {}, []
    w, d, h = piece.size
    res["size_mm"] = [round(w, 2), round(d, 2), round(h, 2)]
    tick_color = THEMES[piece.theme]["ruler"]["ticks"]
    thin = {}
    for c, g in piece.parts.items():
        if piece.kind == "ruler" and c == tick_color:        # ticks/numbers: every 0.5 mm line must survive a 0.24 mm erosion
            lost = len(_polys(g)) - len(_polys(g.buffer(-0.24)))
            ok, limit = lost == 0, 0.5
            thin[c] = lost
        else:
            lost = g.area - opening(g, MIN_FEATURE / 2 - 0.05).area      # sliver area (corner rounding is < 1% of area)
            ok, limit = lost <= max(1.0, 0.01 * g.area), MIN_FEATURE
            thin[c] = round(lost, 2)
        if not ok:
            bad.append(f"{c}: features thinner than {limit} mm ({lost:.1f})")
    res["thin_area_mm2"] = thin
    for cx, cy, dia in piece.holes:
        wall = piece.silhouette.exterior.distance(Point(cx, cy)) - dia / 2 if piece.silhouette.geom_type == "Polygon" else None
        res["hole"] = {"diameter": dia, "wall_to_edge": None if wall is None else round(wall, 2)}
        if wall is not None and wall < 1.5:
            bad.append(f"hanging hole wall only {wall:.2f} mm")
    if piece.tunnel:
        t = piece.tunnel
        roof = t["zc"] + t["roof_cut"]
        res["tunnel"] = {"diameter": t["d"], "axis_z": t["zc"], "roof_z": round(roof, 2), "plate_z": piece.base,
                         "bottom_wall": round(t["zc"] - t["d"] / 2, 2), "top_wall": round(piece.base - roof, 2),
                         "teardrop_apex_cut": t["roof_cut"]}
        if piece.base - roof < 0.79 or t["zc"] - t["d"] / 2 < 1.0:
            bad.append("tunnel walls too thin")
    if piece.kind == "ruler":
        res["ruler"] = {"scale_mm": layout.RULER_MM, "tick_width": 0.5, "number_height": 3.2, "font": "Poppins Bold"}
    if piece.notes:
        bad += piece.notes
    return res, bad


def build(name, theme, outdir, pieces=PIECES, slice_=False):
    stem_base = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower() or "name"
    out = Path(outdir) / f"{stem_base.upper()}_{theme}"
    out.mkdir(parents=True, exist_ok=True)
    pack, report = {"name": name, "theme": theme, "pieces": {}}, {"name": name, "theme": theme, "pieces": {}}
    files = []
    for kind in pieces:
        p = layout.KINDS[kind](theme, name)
        stem = f"{stem_base}_{kind}"
        stats = mesh.export_piece(p, out, stem)
        preview.piece_png(p, out / f"{stem}.png")
        chk, bad = checks(p)
        report["pieces"][kind] = {**stats, **chk, "problems": bad}
        pack["pieces"][kind] = {"base": p.base, "tops": p.tops, "outline": p.outline, "order": stats["colours"],
                                "silhouette": poly_json(p.silhouette), "parts": {c: poly_json(g) for c, g in p.parts.items()},
                                "holes": [list(h) for h in p.holes], "tunnel": p.tunnel, "size_mm": stats["size_mm"]}
        files.append(out / f"{stem}.3mf")
        print(f"  {kind:7s} {p.size[0]:6.1f} x {p.size[1]:5.1f} x {p.size[2]:4.1f} mm  parts={stats['colours']}"
              f"{'  PROBLEMS: ' + '; '.join(bad) if bad else ''}")
    (out / "pack.json").write_text(json.dumps(pack, separators=(",", ":")))
    (out / "report.json").write_text(json.dumps(report, indent=1))
    if slice_:
        subprocess.run([sys.executable, str(HERE / "verify_slice.py"), *map(str, files)], check=False)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name")
    ap.add_argument("--theme", choices=list(THEMES))
    ap.add_argument("--pack", nargs="+", metavar="NAME:THEME")
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--pieces", default=",".join(PIECES))
    ap.add_argument("--slice", action="store_true", help="slice every 3MF in Bambu Studio (time + grams)")
    ap.add_argument("--list-themes", action="store_true")
    a = ap.parse_args()
    if a.list_themes:
        for k, t in THEMES.items():
            print(f"{k:14s} {t['label']}  colours: {', '.join(t['filament_rgb'])}")
        return
    jobs = [tuple(x.rsplit(":", 1)) for x in a.pack] if a.pack else [(a.name, a.theme)]
    if not all(jobs[0]) or not all(j[1] in THEMES for j in jobs):
        ap.error("give --name and --theme (or --pack NAME:THEME ...)")
    for name, theme in jobs:
        print(f"{name} / {theme}")
        build(name, theme, a.out, a.pieces.split(","), a.slice)


if __name__ == "__main__":
    main()
