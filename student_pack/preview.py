"""Render colour layers (shapely geometries) to PNG with matplotlib."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch

HEX = {"black": "#1C1C1C", "yellow": "#F6BA1C", "orange": "#FA7614", "white": "#FCFCFC",
       "pink": "#EC307A", "lpink": "#FAA8C8"}


def _patch(poly, color):
    verts, codes = [], []
    for ring in [poly.exterior, *poly.interiors]:
        c = list(ring.coords)
        verts += c
        codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(verts, codes), facecolor=HEX.get(color, color), edgecolor="none", lw=0)


def draw(ax, layers, order=None, holes=None):
    for color in (order or list(layers)):
        g = layers.get(color)
        if g is None or g.is_empty:
            continue
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            if p.geom_type == "Polygon":
                ax.add_patch(_patch(p, color))
    ax.set_aspect("equal"); ax.autoscale_view()


def save(path, layers_list, order=None, titles=None, bg="#8a8a8a", scale=0.06):
    n = len(layers_list)
    fig, axes = plt.subplots(1, n, figsize=(sum(max(2, _w(l) * scale) for l in layers_list), 4.5), squeeze=False)
    fig.patch.set_facecolor(bg)
    for ax, layers, i in zip(axes[0], layers_list, range(n)):
        ax.set_facecolor(bg); draw(ax, layers, order); ax.set_xlim(*_lim(layers, 0)); ax.set_ylim(*_lim(layers, 1))
        ax.axis("off")
        if titles: ax.set_title(titles[i], color="white", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=130, facecolor=bg); plt.close(fig)


def _b(layers):
    bs = [g.bounds for g in layers.values() if not g.is_empty]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


def _w(layers): b = _b(layers); return b[2] - b[0]
def _lim(layers, k): b = _b(layers); return (b[k] - 1, b[k + 2] + 1)


def piece_png(piece, path, bg="#d9d9d9"):
    """Top-down colour render of one Piece."""
    import matplotlib.pyplot as plt
    b = piece.bounds
    w, h = b[2] - b[0], b[3] - b[1]
    fig, ax = plt.subplots(figsize=(max(3, w / 14), max(2, h / 14 + 0.4)))
    fig.patch.set_facecolor(bg); ax.set_facecolor(bg)
    layers = {"_base": piece.silhouette, **piece.parts}
    HEX["_base"] = HEX[piece.outline]
    draw(ax, layers)
    for hx, hy, d in piece.holes:
        ax.add_patch(plt.Circle((hx, hy), d / 2, fc=bg, ec="none"))
    if piece.tunnel:
        ax.axhline(piece.tunnel["y"], color="cyan", lw=0.6, ls="--")
    ax.set_xlim(b[0] - 2, b[2] + 2); ax.set_ylim(b[1] - 2, b[3] + 2); ax.axis("off"); ax.set_title(f"{piece.kind} {piece.name} {w:.1f}x{h:.1f}", fontsize=7)
    fig.tight_layout(); fig.savefig(path, dpi=140, facecolor=bg); plt.close(fig)
