"""Window key-holder: trace the owner's flat 4-colour drawing into colour layers (shapely, mm) + flat preview.

    python cad/windowkey/trace_flat.py picture.png --out layers.json --preview flat.png [--width 300]

Picture: flat colours on a black background (kept local, not in git). Labels: cream (plate, cat), light pink, dark pink, green.
Output JSON: layer -> GeoJSON in mm, y up, silhouette bbox centred at 0,0.
"""
import argparse, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import contourpy
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union
from shapely import affinity

PAL = {"bg": (0, 0, 0), "cream": (252, 238, 220), "lpink": (250, 170, 188), "dpink": (204, 66, 100), "green": (100, 155, 55)}
DRAW = {"cream": "#FFF3E0", "lpink": "#F4B6C2", "dpink": "#D9667E", "green": "#6FA05B"}


def polys(mask, min_area=10):
    gen = contourpy.contour_generator(z=mask.astype(float), fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    out = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        g = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if g.area >= min_area:
            out.append(g)
    return unary_union(out) if out else Polygon()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("--out", required=True); ap.add_argument("--preview")
    ap.add_argument("--width", type=float, default=300.0); ap.add_argument("--sigma", type=float, default=1.3)
    a = ap.parse_args()
    rgb = np.array(Image.open(a.image).convert("RGB")).astype(float)
    names = list(PAL)
    d = ((rgb[:, :, None, :] - np.array([PAL[n] for n in names], float)[None, None]) ** 2).sum(-1)
    lab = d.argmin(-1)
    bg = 0
    fg = ndi.binary_fill_holes(ndi.binary_opening(lab != bg, iterations=2))
    comp, n = ndi.label(fg)
    if n > 1:
        fg = comp == 1 + int(np.argmax(ndi.sum(fg, comp, range(1, n + 1))))
    # anti-aliased edge pixels between two colours may be mis-labelled: smooth the label field, keep silhouette
    st = np.stack([ndi.gaussian_filter((lab == i).astype(float), a.sigma) for i in range(len(names))])
    lab = np.where(fg, st[1:].argmax(0) + 1, bg)
    ys, xs = np.nonzero(fg)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    s = a.width / (x1 - x0 + 1)
    def to_mm(g):
        g = affinity.scale(g, s, -s, origin=(0, 0))
        return affinity.translate(g, -(x0 + x1) / 2 * s, (y0 + y1) / 2 * s)
    res = {"silhouette": to_mm(polys(fg)).simplify(0.15)}
    for i, nme in enumerate(names):
        if nme != "bg":
            res[nme] = to_mm(polys(lab == i)).simplify(0.12)
    W, H = (x1 - x0 + 1) * s, (y1 - y0 + 1) * s
    json.dump({"width": W, "height": H, **{k: mapping(v) for k, v in res.items()}}, open(a.out, "w"))
    print(f"size {W:.0f} x {H:.0f} mm; area mm2:", {k: round(v.area) for k, v in res.items()})
    # smallest features: parts narrower than 0.7 mm (erosion test)
    for k in ("lpink", "dpink", "green", "cream"):
        g = res[k]
        thin = g.difference(g.buffer(-0.35).buffer(0.35))
        print(k, "thin (<0.7 mm) area mm2:", round(thin.area, 1))
    if a.preview:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import PathPatch
        from matplotlib.path import Path
        fig, ax = plt.subplots(figsize=(10, 10 * H / W)); ax.set_aspect("equal"); ax.axis("off")
        def draw(g, col):
            for p in getattr(g, "geoms", [g]):
                if p.is_empty: continue
                v, c = list(p.exterior.coords), [Path.MOVETO] + [Path.LINETO] * (len(p.exterior.coords) - 1)
                for r in p.interiors:
                    v += list(r.coords); c += [Path.MOVETO] + [Path.LINETO] * (len(r.coords) - 1)
                ax.add_patch(PathPatch(Path(v, c), fc=col, ec="none"))
        draw(res["silhouette"], DRAW["cream"])
        for k in ("lpink", "green", "dpink"):
            draw(res[k], DRAW[k])
        ax.set_xlim(-W / 2, W / 2); ax.set_ylim(-H / 2, H / 2)
        fig.savefig(a.preview, dpi=110, bbox_inches="tight", facecolor="#202020"); print("preview", a.preview)

if __name__ == "__main__":
    main()
