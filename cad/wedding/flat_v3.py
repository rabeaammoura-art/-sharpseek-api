"""Wedding heart plaque, flat 2D preview v3 -- built from the owner's clean flat picture (heart outline, couple,
veil, hearts, rings, calendar icon). No banner (owner / partner decision: simpler, faster print, rings full size).

Usage:  python cad/wedding/flat_v3.py <flat_picture.png> <out_dir> [--size 280] [--frame 9]
        [--name1 أحمد --name2 سارة --date 15/06/2026]

Picture = third-party/GPT image: only passed as an argument, nothing traced from it is committed. Names and date are
re-typeset with the real fonts (the picture's letters are not reused); everything else is traced from the clean
colour masks (couple, veil, hearts, lines, rings, calendar) and smoothed. The frame is rebuilt 9 mm wide (picture: 3 mm)
so it can carry the back-lit box. Content is scaled down (about the heart centre) only as much as needed to fit inside it.
"""
import argparse
import math
import sys
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import flat_v1 as v1  # noqa: E402  (patch helper)
import newborn_plaque as n  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

# component ids come from scipy.ndimage.label on the colour masks of THIS picture (checked by bbox, see keep_* below)
NAVY_KEEP_BBOX = [(244, 363, 103, 230), (165, 727, 160, 817), (483, 1101, 205, 353), (417, 504, 852, 938)]  # head, couple, veil, calendar
GOLD_SKIP_BBOX = (13, 1236, 22, 1242)                                                                         # the thin outline
TEXT_NAME1 = (867, 362, 346)      # centre x, centre y, width (px) -- from the picture
TEXT_NAME2 = (857, 634, 347)
TEXT_DATE = (693, 893, 330)
PIVOT = (625.0, 650.0)


def masks(ref):
    rgb = np.asarray(Image.open(ref).convert("RGB")).astype(int)
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    gold = (R > 150) & (G > 100) & (B < 110) & (R - B > 80)
    navy = (R < 70) & (G < 80) & (B < 120)
    return gold, navy


def contours(mask, sigma=1.2, min_area=20):
    f = ndi.gaussian_filter(mask.astype(float), sigma)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if pg.area >= min_area:
            out.append(pg.simplify(0.25))
    return unary_union(out) if out else Polygon()


def pick(mask, bboxes, skip=None, tol=3):
    """Keep the connected components whose bbox matches (x0, x1, y0, y1) in `bboxes`; or all but `skip`."""
    lab, nl = ndi.label(mask)
    keep = np.zeros(mask.shape, bool)
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        bb = (sl[1].start, sl[1].stop, sl[0].start, sl[0].stop)
        area = (lab[sl] == i).sum()
        if skip is not None:
            if area > 300 and not all(abs(a - b) <= tol for a, b in zip(bb, skip)):
                keep |= lab == i
        elif any(all(abs(a - b) <= tol for a, b in zip(bb, k)) for k in bboxes):
            keep |= lab == i
    return keep


def heart_outline(gold):
    lab, _ = ndi.label(gold)
    big = lab == lab[gold].flat[np.argmax(np.bincount(lab[gold]))]
    filled = ndi.binary_fill_holes(big)
    filled = filled & filled[:, ::-1]                    # symmetric about the picture centre line
    filled = np.roll(filled, 0, axis=1)
    poly = contours(filled, sigma=2.5, min_area=1000)
    return poly.buffer(0)


def text_px(txt, kind, lang, cx, cy, width):
    g, w = n.text_line([(txt, 40, kind)], lang, lang == "ar")
    k = width / w
    g = affinity.scale(g, k, -k, origin=(0, 0))          # y up (font) -> y down (picture px)
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def build(ref, size, frame_mm, name1, name2, date):
    gold_m, navy_m = masks(ref)
    outer = heart_outline(gold_m)
    x0, y0, x1, y1 = outer.bounds
    s = size / (x1 - x0)                                 # mm per px
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    inner = outer.buffer(-frame_mm / s, join_style=2, mitre_limit=6)

    sel = pick(navy_m, NAVY_KEEP_BBOX)
    sel[852:938, 417:504] |= navy_m[852:938, 417:504]            # calendar icon incl. its small grid squares
    navy_px = contours(sel, sigma=1.0, min_area=8)
    gold_px = contours(pick(gold_m, None, skip=GOLD_SKIP_BBOX), sigma=1.0, min_area=40)
    texts = unary_union([
        text_px(name1, "name", "ar", *TEXT_NAME1),
        text_px(name2, "name", "ar", *TEXT_NAME2),
        text_px(date, "num", "en", *TEXT_DATE),
    ])
    content = unary_union([navy_px, gold_px, texts])

    # scale content about the pivot only as much as needed to sit inside the wider frame (1.2 mm margin)
    margin = inner.buffer(-1.2 / s)
    f = 1.0
    while f > 0.8 and not content.difference(margin).is_empty and content.difference(margin).area > 2.0:
        f -= 0.005
        content = affinity.scale(unary_union([navy_px, gold_px, texts]), f, f, origin=PIVOT)
    navy_f = affinity.scale(unary_union([navy_px, texts]), f, f, origin=PIVOT)
    gold_f = affinity.scale(gold_px, f, f, origin=PIVOT)

    def to_mm(g):
        return affinity.translate(affinity.scale(g, s, -s, origin=(0, 0)), -cx * s, cy * s)
    gold = unary_union([outer.difference(inner), gold_f]).difference(navy_f)
    return dict(gold=to_mm(gold), navy=to_mm(navy_f.difference(outer.difference(inner))), cream=to_mm(inner),
                outer=to_mm(outer), inner=to_mm(inner), scale=f, s=s, to_mm=to_mm, size_px=Image.open(ref).size,
                cxy=(cx, cy))


def render(L, path, ref=None):
    fig, ax = plt.subplots(figsize=(9, 9), dpi=140)
    ax.set_facecolor("#3b3330")
    a = 1.0
    if ref is not None:
        W, H = L["size_px"]
        s, (cx, cy) = L["s"], L["cxy"]
        ax.imshow(np.asarray(Image.open(ref).convert("RGB")), extent=[-cx * s, (W - cx) * s, -(H - cy) * s, cy * s], zorder=0)
        a = 0.55
    for g, col, z in [(L["cream"], "#fff1c9", 1), (L["gold"], "#d9a21b", 2), (L["navy"], "#161d3c", 3)]:
        for p in v1.patch(g, fc=col, ec="none", alpha=a, zorder=z):
            ax.add_patch(p)
    bx0, by0, bx1, by1 = L["outer"].bounds
    ax.set_xlim(bx0 - 6, bx1 + 6)
    ax.set_ylim(by0 - 6, by1 + 6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="#3b3330")
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("out")
    ap.add_argument("--size", type=float, default=280)
    ap.add_argument("--frame", type=float, default=9.0)
    ap.add_argument("--name1", default="أحمد")
    ap.add_argument("--name2", default="سارة")
    ap.add_argument("--date", default="15/06/2026")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    L = build(a.ref, a.size, a.frame, a.name1, a.name2, a.date)
    render(L, out / "flat_v3.png")
    render(L, out / "flat_v3_overlay.png", ref=a.ref)
    x0, y0, x1, y1 = L["outer"].bounds
    print(f"heart {x1 - x0:.1f} x {y1 - y0:.1f} mm, content scale {L['scale']:.3f}, frame {a.frame} mm")
