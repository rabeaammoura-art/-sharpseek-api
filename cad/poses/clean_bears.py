"""Clean the 4 teddy-bear poses (GPT sheet, 2x2) into ONE-colour vector shapes: body / cream / navy / yellow.
Usage: python cad/poses/clean_bears.py <sheet.png> <out_dir>
The sheet is GPT output (original bear, no third-party character). Shade lines (darker creases) are merged into the body
colour, anti-aliasing halos removed by an opening, contours smoothed. Writes poses.pkl (shapely, px y-down, per pose) + preview.
"""
import pickle
import sys
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.cluster.vq import kmeans2
from shapely.geometry import Polygon
from shapely.ops import unary_union

CELLS = [(8, 7, 624, 623), (633, 7, 1248, 623), (8, 632, 624, 1248), (633, 632, 1248, 1248)]
PROTO = {"bg": (197, 198, 200), "cream": (246, 235, 214), "yellow": (252, 200, 60), "navy": (38, 78, 128)}
NAMES = ["sleep", "cheer", "balloon", "star"]


def classify(cell):
    px = cell.reshape(-1, 3).astype(float)
    rng = np.random.default_rng(1)
    sample = px[rng.choice(len(px), 20000, replace=False)]
    cent, _ = kmeans2(sample, 9, minit="++", seed=3)
    d = ((px[:, None, :] - cent[None]) ** 2).sum(2)
    lab = d.argmin(1)
    role = {}
    for k, c in enumerate(cent):
        best = min(PROTO, key=lambda r: np.linalg.norm(c - np.array(PROTO[r])))
        role[k] = best if np.linalg.norm(c - np.array(PROTO[best])) < 30 else "body"
    out = np.array([role[l] for l in lab]).reshape(cell.shape[:2])
    return out


def polys(mask, sigma=1.4, min_area=40):
    f = ndi.gaussian_filter(mask.astype(float), sigma)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    res = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if pg.area >= min_area:
            res.append(pg.simplify(0.3))
    return unary_union(res) if res else Polygon()


def main():
    sheet = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    result = {}
    for name, (x0, y0, x1, y1) in zip(NAMES, CELLS):
        cell = sheet[y0:y1, x0:x1]
        r = classify(cell)
        body = ndi.binary_opening(r == "body", iterations=2)
        lab, n = ndi.label(body)
        if n > 1:                                   # keep every real body part (paws can be cut off by shade lines)
            sizes = ndi.sum(body, lab, range(1, n + 1)); body = np.isin(lab, [i + 1 for i, a in enumerate(sizes) if a > 1500])
        body = ndi.binary_fill_holes(body | ndi.binary_dilation(body, iterations=1) & (r != "bg") & (r != "cream"))
        masks = {"body": body,
                 "cream": ndi.binary_opening(r == "cream", iterations=2),
                 "navy": ndi.binary_opening(r == "navy", iterations=1),
                 "yellow": ndi.binary_opening(r == "yellow", iterations=2)}
        result[name] = {k: polys(m) for k, m in masks.items()}
        print(name, {k: round(v.area) for k, v in result[name].items()})
    pickle.dump(result, open(out / "poses.pkl", "wb"))
    # preview: one colour for every bear
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MP
    def patch(g, **kw):
        res = []
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            if p.is_empty or p.geom_type != "Polygon": continue
            v, c = [], []
            for ring in [p.exterior] + list(p.interiors):
                cc = list(ring.coords); v += cc; c += [MP.MOVETO] + [MP.LINETO] * (len(cc) - 2) + [MP.CLOSEPOLY]
            res.append(PathPatch(MP(v, c), **kw))
        return res
    fig, axs = plt.subplots(2, 2, figsize=(9, 9), dpi=120)
    for ax, name in zip(axs.flat, NAMES):
        ax.set_facecolor("#d8d8d8")
        for key, col, z in [("body", "#C8A078", 2), ("cream", "#F5ECD7", 3), ("yellow", "#F0C446", 3), ("navy", "#3E628A", 4)]:
            for p in patch(result[name][key], fc=col, ec="none", zorder=z): ax.add_patch(p)
        ax.set_xlim(0, 616); ax.set_ylim(616, 0); ax.set_aspect("equal"); ax.axis("off")
    fig.tight_layout(); fig.savefig(out / "bears_clean.png"); print("wrote", out / "bears_clean.png")


if __name__ == "__main__":
    main()
