"""Little-prince lamp diffuser: round 79 mm disc, relief = bear + name + date/time/weight/length (option 4 of the GPT sheet).

    .venv-cad/bin/python cad/diffuser.py cad/plaque/diffuser_ar.json   # -> cad/plaque/diffuser/diffuser_ar_preview.png

Edit the values in the JSON (name, date, time, ampm, weight, length, unit_w, unit_l); the bear/stars/icons are traced once
from cad/plaque/diffuser/gpt_option4_source.png. All numbers in mm, origin at the disc centre, y up.
"""
import argparse
import json
from pathlib import Path

import contourpy
import matplotlib
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely import affinity
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

from newborn_plaque import text_line

HERE = Path(__file__).parent
SRC = HERE / "plaque/diffuser/gpt_option4_source.png"
R = 39.5            # disc radius (diameter 79 = original diffuser)
SAFE = 36.0         # nothing of the relief goes beyond this radius
DISC_H, RELIEF_H = 1.34, 0.67
# option-4 disc inside the source image: centre / radius in pixels (full image coordinates)
PX_C, PX_R = (260.0, 512 + 256.0), 240.0
MM_PX = R / PX_R
MIN_LINE = 1.0      # mm, thinnest stroke that is kept after thickening


def trace(box_px, min_area=8):
    """Black pixels inside box_px=(x0,y0,x1,y1) of the source image -> shapely geometry in mm (disc-centred, y up)."""
    im = np.asarray(Image.open(SRC).convert("L"), float)
    x0, y0, x1, y1 = box_px
    c = ndi.zoom(im[y0:y1, x0:x1], 3, order=1)
    c = ndi.gaussian_filter(c, 1.2)
    gen = contourpy.contour_generator(z=-c, fill_type=contourpy.FillType.OuterOffset)
    polys = []
    for pts, offs in zip(*gen.filled(-128.0, 1e9)):
        rings = [pts[offs[i]:offs[i + 1]] for i in range(len(offs) - 1)]
        if not rings:
            continue
        def tomm(r):
            return [((x0 + px / 3 - PX_C[0]) * MM_PX, (PX_C[1] - (y0 + py / 3)) * MM_PX) for px, py in r]
        p = Polygon(tomm(rings[0]), [tomm(r) for r in rings[1:] if len(r) > 3])
        if p.is_valid and p.area > min_area * MM_PX ** 2:
            polys.append(p)
    return unary_union(polys)


def thicken(g, min_w=MIN_LINE):
    """Open thin strokes up to >= min_w mm (grow by the missing half-width, then remove nothing)."""
    return g.buffer(0.18, 8).buffer(-0.02, 8)


def fit_text(segs, lang, rtl, max_w, max_h=None):
    g, w = text_line(segs, lang, rtl)
    s = 1.0
    if w > max_w:
        s = max_w / w
    if max_h is not None and g.bounds[3] - g.bounds[1] > 0 and (g.bounds[3] - g.bounds[1]) * s > max_h:
        s = max_h / (g.bounds[3] - g.bounds[1])
    return affinity.scale(g, s, s, origin=(0, 0)) if s != 1 else g


def place(g, cx=None, left=None, right=None, cy=None, base=None):
    minx, miny, maxx, maxy = g.bounds
    dx = (cx - (minx + maxx) / 2) if cx is not None else (left - minx if left is not None else right - maxx)
    dy = (cy - (miny + maxy) / 2) if cy is not None else base
    return affinity.translate(g, dx, dy)


def build(cfg):
    lang, rtl = cfg["lang"], cfg["lang"] == "ar"
    parts = {}
    # --- decoration traced from the picture: bear + stars + line (top) and the 4 icons (left column)
    deco = trace((78, 512 + 28, 442, 512 + 172))
    deco = deco.intersection(Point(0, 0).buffer(37.5, 64))   # drops the GPT disc outline and the option label
    ic = {k: trace(b) for k, b in {
        "date": (98, 512 + 262, 162, 512 + 318), "time": (98, 512 + 320, 162, 512 + 362),
        "weight": (108, 512 + 366, 166, 512 + 414), "length": (134, 512 + 404, 192, 512 + 456)}.items()}
    # --- text
    name = fit_text([(cfg["name"], 12, "name")], lang, rtl, max_w=62, max_h=16.5)
    name = place(name, cx=0, base=0)
    lines = {
        "date": [(cfg["date"], 6, "num")],
        "time": [(cfg["time"], 6, "num"), (cfg["ampm"], 6, "word")],
        "weight": [(cfg["weight"], 6, "num"), (cfg["unit_w"], 6, "word")],
        "length": [(cfg["length"], 6, "num"), (cfg["unit_l"], 6, "word")],
    }
    ICON_H = 6.6
    tx, items = [], {}
    y = -3.5          # top of the first row: just under the name
    PITCH = 7.9
    block_w = 46.0
    for i, (k, segs) in enumerate(lines.items()):
        t = fit_text(segs, lang, rtl, max_w=block_w - 10, max_h=5.9)
        ig = ic[k]
        s = ICON_H / (ig.bounds[3] - ig.bounds[1])
        ig = affinity.scale(ig, s, s, origin=(0, 0))
        cy = y - PITCH * i - ICON_H / 2
        ig = place(ig, cx=0, cy=cy)
        t = place(t, cx=0, cy=cy)
        # row = icon + gap + text, centred as a group, icon on the reading-start side
        gap = 2.2
        wi, wt = ig.bounds[2] - ig.bounds[0], t.bounds[2] - t.bounds[0]
        total = wi + gap + wt
        x0 = -total / 2
        if not rtl:
            ig = place(ig, left=x0, cy=cy); t = place(t, left=x0 + wi + gap, cy=cy)
        else:
            t = place(t, left=x0, cy=cy); ig = place(ig, left=x0 + wt + gap, cy=cy)
        items[k] = (ig, t)
    # bear block: shift so its bottom line sits just above the name
    db = deco.bounds
    s_b = 0.9
    bear = affinity.scale(deco, s_b, s_b, origin=(0, 0))
    bear = affinity.translate(bear, -(bear.bounds[0] + bear.bounds[2]) / 2 , (name.bounds[3] + 1.6) - bear.bounds[1])
    relief = unary_union([bear, name] + [g for pair in items.values() for g in pair])
    b = relief.bounds
    return affinity.translate(relief, 0, -(b[1] + b[3]) / 2)   # centre the whole design vertically


def draw(ax, g, **kw):
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        codes, verts = [], []
        for ring in [p.exterior] + list(p.interiors):
            xy = np.asarray(ring.coords)
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
            verts += list(xy)
        ax.add_patch(PathPatch(MPath(verts, codes), **kw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cfg")
    a = ap.parse_args()
    cfg = json.load(open(a.cfg))
    g = build(cfg)
    out = HERE / "plaque/diffuser" / (Path(a.cfg).stem + "_preview.png")
    fig, ax = plt.subplots(figsize=(7, 7), dpi=130)
    ax.add_patch(plt.Circle((0, 0), R, fc="#f4f4ef", ec="#999", lw=1.5))
    ax.add_patch(plt.Circle((0, 0), SAFE, fc="none", ec="#c33", lw=0.6, ls="--"))
    draw(ax, g, fc="#1b1b1b", ec="none")
    ax.set_xlim(-R - 2, R + 2); ax.set_ylim(-R - 2, R + 2); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("diffuser 79 mm (red dashed = safe margin)  relief %.2f mm" % RELIEF_H, fontsize=9)
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    far = max(np.hypot(*np.asarray(p.exterior.coords).T).max() for p in getattr(g, "geoms", [g]))
    print("preview:", out, "| farthest point from centre %.1f mm (limit %.1f)" % (far, SAFE))
    print("bounds", [round(v, 1) for v in g.bounds])


if __name__ == "__main__":
    main()
