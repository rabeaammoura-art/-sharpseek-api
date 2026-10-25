"""Vector-trace the source art into per-colour motif polygons (potrace), stored as JSON under motifs/.

    python trace.py                 # all themes, all motifs
    python trace.py cat             # one theme
    python trace.py cat tag bottle  # some motifs of a theme

Pipeline per motif: crop -> erase/paint fixes -> Lanczos x3 -> bilateral smooth -> nearest-palette
classification -> median clean-up -> one bitmap per colour -> potrace Bezier curves -> shapely polygons in mm.
Nothing is voxelised: the output is plain polygons, so meshes stay small and edges stay smooth.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import potrace
from PIL import Image
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

from themes import ART, THEMES

HERE = Path(__file__).parent
UP = 3            # upscale factor before classification
SEAL_PX = 4       # width (source px) of the temporary sealing strip


def flatten_curve(curve, n=10):
    pts = [(curve.start_point.x, curve.start_point.y)]
    p0 = pts[0]
    for seg in curve.segments:
        if seg.is_corner:
            pts.append((seg.c.x, seg.c.y))
            pts.append((seg.end_point.x, seg.end_point.y))
        else:
            c1, c2, e = (seg.c1.x, seg.c1.y), (seg.c2.x, seg.c2.y), (seg.end_point.x, seg.end_point.y)
            for i in range(1, n + 1):
                t = i / n
                a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
                pts.append((a * p0[0] + b * c1[0] + c * c2[0] + d * e[0], a * p0[1] + b * c1[1] + c * c2[1] + d * e[1]))
        p0 = pts[-1]
    return pts


def mask_to_geom(mask, mm_per_px, height_px):
    """potrace a boolean mask -> shapely geometry (even-odd nesting), mm, y up."""
    bm = potrace.Bitmap(~mask)   # potracer inverts its input: pass background=True
    plist = bm.trace(turdsize=4, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY, alphamax=1.0,
                     opticurve=True, opttolerance=0.3)
    geom = Polygon()
    for curve in plist:
        pts = [(x * mm_per_px, (height_px - y) * mm_per_px) for x, y in flatten_curve(curve)]
        if len(pts) < 3:
            continue
        ring = Polygon(pts).buffer(0)
        if ring.is_empty:
            continue
        geom = geom.symmetric_difference(ring)
    return geom


def _touches(p, edge, u, tol=0.3):
    b = p.bounds
    return {"bottom": b[1] <= u.bounds[1] + tol, "top": b[3] >= u.bounds[3] - tol,
            "left": b[0] <= u.bounds[0] + tol, "right": b[2] >= u.bounds[2] - tol}[edge]


def classify(rgb, palette):
    names = list(palette)
    cols = np.array([palette[n][0] for n in names], np.float32)
    d = ((rgb[..., None, :].astype(np.float32) - cols[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    printed = sorted({palette[n][1] for n in names})
    lut = np.array([printed.index(palette[n][1]) for n in names], np.uint8)
    return lut[idx], printed


def trace_motif(img, theme, spec):
    x0, y0, x1, y1 = spec["box"]
    palette = theme["palette"]
    crop = img[y0:y1, x0:x1].copy()
    erase_rgb = 255 if spec["bg"] == "flood" else [v for k, (v, p) in palette.items() if p == spec["bg"]][0]
    for ex0, ey0, ex1, ey1 in spec.get("erase", []):
        crop[max(0, ey0 - y0):max(0, ey1 - y0), max(0, ex0 - x0):max(0, ex1 - x0)] = erase_rgb
    for pts in spec.get("erase_poly", []):            # free-form erase (px, source coords)
        cv2.fillPoly(crop, [np.array([(x - x0, y - y0) for x, y in pts], np.int32)], (255, 255, 255) if erase_rgb == 255 else erase_rgb)
    for color, (ex0, ey0, ex1, ey1) in spec.get("paint", []):
        rgb = [v for k, (v, p) in palette.items() if p == color][0]
        crop[max(0, ey0 - y0):max(0, ey1 - y0), max(0, ex0 - x0):max(0, ex1 - x0)] = rgb
    h, w = crop.shape[:2]
    up = cv2.resize(crop, (w * UP, h * UP), interpolation=cv2.INTER_LANCZOS4)
    up = cv2.bilateralFilter(up, 7, 40, 7)
    outline_rgb = [v for k, (v, p) in palette.items() if p == theme["outline"]][0]
    s = SEAL_PX * UP
    clip = [0, 0, w * UP, h * UP]               # left, top, right, bottom of the usable area (px)
    for side in spec.get("seal", []):
        if side == "bottom":
            up[-s:, :] = outline_rgb; clip[3] -= s
        elif side == "top":
            up[:s, :] = outline_rgb; clip[1] += s
        elif side == "left":
            up[:, :s] = outline_rgb; clip[0] += s
        elif side == "right":
            up[:, -s:] = outline_rgb; clip[2] -= s
    lab, printed = classify(up, palette)
    lab = cv2.medianBlur(lab, 9)
    if spec["bg"] == "flood":
        near_white = (up.min(-1) > 232).astype(np.uint8)
        n, cc = cv2.connectedComponents(near_white, connectivity=4)
        border = set(np.unique(np.concatenate([cc[0], cc[-1], cc[:, 0], cc[:, -1]]))) - {0}
        bg = np.isin(cc, list(border))
        for sx, sy in spec.get("open", []):     # enclosed background pockets that should stay open
            k = cc[(sy - y0) * UP, (sx - x0) * UP]
            if k:
                bg |= cc == k
    else:
        bg = lab == printed.index(spec["bg"])
    mm = spec["scale"] / UP
    layers = {}
    usable = box(clip[0] * mm, (h * UP - clip[3]) * mm, clip[2] * mm, (h * UP - clip[1]) * mm)
    for cx0, cy0, cx1, cy1 in spec.get("cut", []):   # regions painted as outline for sealing, removed afterwards
        usable = usable.difference(box((cx0 - x0) * spec["scale"], (h - (cy1 - y0)) * spec["scale"],
                                       (cx1 - x0) * spec["scale"], (h - (cy0 - y0)) * spec["scale"]))
    if "clip_circle" in spec:                    # round dome: drop everything outside (px circle in source coords)
        from shapely.geometry import Point
        cx, cy, r = spec["clip_circle"]
        usable = usable.intersection(Point((cx - x0) * spec["scale"], (h - (cy - y0)) * spec["scale"]).buffer(r * spec["scale"], 128))
    for i, name in enumerate(printed):
        if spec["bg"] != "flood" and name == spec["bg"]:
            continue
        m = (lab == i) & ~bg
        if not m.any():
            continue
        g = mask_to_geom(m, mm, h * UP).intersection(usable)
        polys = [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if isinstance(p, Polygon) and not p.is_empty]
        for c, edge in spec.get("drop_edge", []):   # stray bits of neighbouring art touching a cut edge
            if c == name:
                polys = [p for p in polys if not _touches(p, edge, usable)]
        if polys:
            layers[name] = [{"ext": [[round(x, 3), round(y, 3)] for x, y in p.exterior.coords],
                             "holes": [[[round(x, 3), round(y, 3)] for x, y in r.coords] for r in p.interiors]}
                            for p in polys]
    return {"width_mm": round(w * spec["scale"], 3), "height_mm": round(h * spec["scale"], 3),
            "tab_x_mm": round((spec["tab_x_px"] - x0) * spec["scale"], 3) if "tab_x_px" in spec else None,
            "layers": layers}


def main(argv):
    only_theme = argv[0] if argv else None
    only_motifs = set(argv[1:])
    img = np.asarray(Image.open(HERE / ART).convert("RGB"))
    for tname, theme in THEMES.items():
        if only_theme and tname != only_theme:
            continue
        out = HERE / "motifs" / f"{tname}.json"
        out.parent.mkdir(exist_ok=True)
        data = json.loads(out.read_text()) if out.exists() and only_motifs else {}
        for mname, spec in theme["motifs"].items():
            if only_motifs and mname not in only_motifs:
                continue
            data[mname] = trace_motif(img, theme, spec)
            npts = sum(len(p["ext"]) + sum(map(len, p["holes"])) for L in data[mname]["layers"].values() for p in L)
            print(f"{tname}/{mname}: {data[mname]['width_mm']:.1f}x{data[mname]['height_mm']:.1f} mm, "
                  f"{ {k: len(v) for k, v in data[mname]['layers'].items()} } polys, {npts} pts", flush=True)
        out.write_text(json.dumps(data, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1:])
