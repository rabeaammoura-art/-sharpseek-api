"""Filament-painting ("HueForge"-style) keychain: a flat print in thin layers where colour comes
from how many translucent layers sit over a white base. Faces keep their shading and features.

Filaments are stacked by height: white base, then skin, brown, black. Every pixel gets the layer
count whose simulated colour (light passing the stacked layers) is closest to the picture.

Usage: python hueforge.py <image> <girl|boy> <out dir> [height_mm]
Writes out/<name>.stl (one object), colour_changes.json (for Bambu Studio), preview.png
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from make_keychain import letter                      # noqa: E402
from photo_keychain import bow_shape                  # noqa: E402

PX = 0.2                 # mm per pixel of the height map
FIRST, LH = 0.16, 0.08   # first layer and layer height, mm
BASE_LAYERS = 12         # white base: first layer + 11 x 0.08 = 1.04 mm
# filament stack above the base: (name, colour, transmission distance mm, layers)
STACK = [("skin", "#D9A07A", 1.4, 6), ("brown", "#5C3A24", 0.9, 5), ("black", "#1A1A1A", 0.5, 5)]
WHITE = "#F6F6F6"
OUTLINE_MM, BORDER_MM = 0.6, 0.9   # dark rim hugging the shape (no filled gaps)

PEOPLE = {
    "girl": dict(letter="S", style="bow", crop=(560, 250, 898, 1088)),
    "boy": dict(letter="O", style="star", crop=(66, 278, 348, 1112)),
}


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255.0


def level_colours():
    """Simulated colour (sRGB 0-1) for 0..N layers above the white base."""
    cols = [rgb(WHITE)]
    below = rgb(WHITE)
    for name, hexcol, td, n in STACK:
        f = rgb(hexcol)
        for k in range(1, n + 1):
            a = min(1.0, k * LH / td)
            cols.append(below * (1 - a) + f * a)
        below = cols[-1]
    return np.array(cols)


def to_lab(rgb01):
    u8 = np.clip(rgb01 * 255, 0, 255).astype(np.uint8).reshape(-1, 1, 3)
    return cv2.cvtColor(u8[..., ::-1], cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)


def figure(image, crop, fig_h):
    img = cv2.imread(str(image))
    x0, y0, x1, y1 = crop
    img = img[y0:y1, x0:x1]
    scale = fig_h / img.shape[0] / PX                    # source px -> map px
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bg = ((hsv[..., 2] > 232) & (hsv[..., 1] < 22)).astype(np.uint8)
    h, w = bg.shape
    ff, m = bg.copy(), np.zeros((h + 2, w + 2), np.uint8)
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if ff[sy, sx]:
            cv2.floodFill(ff, m, (sx, sy), 2)
    fig = (ff != 2).astype(np.uint8)
    n, cc, st, _ = cv2.connectedComponentsWithStats(fig)
    fig = (cc == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    fig = cv2.morphologyEx(fig, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return img, fig


def letter_shapes(person, H):
    """(shape, role) with role in fill / light / dark, letter coordinates in mm."""
    if person["style"] == "bow":
        L = letter(person["letter"], H, 0, 0)
        minx, miny, maxx, maxy = L.bounds
        bow, knot = bow_shape(minx + 0.24 * H, maxy - 0.02 * H, 0.12 * H)
        inline = L.buffer(-0.034 * H).difference(L.buffer(-0.05 * H))
        return [(L, "fill"), (inline, "light"), (bow, "fill"), (knot, "dark")]
    L = letter(person["letter"], H, 0, 0)                       # bold round O
    minx, miny, maxx, maxy = L.bounds
    inline = L.buffer(-0.034 * H).difference(L.buffer(-0.05 * H))
    star = star_shape(minx + 0.14 * H, maxy - 0.08 * H, 0.13 * H, 0.055 * H)
    return [(L, "fill"), (inline, "light"), (star, "fill")]


def star_shape(cx, cy, r_out, r_in, points=5):
    pts = [(cx + (r_out if k % 2 == 0 else r_in) * math.sin(math.pi * k / points),
            cy + (r_out if k % 2 == 0 else r_in) * math.cos(math.pi * k / points)) for k in range(2 * points)]
    from shapely.geometry import Polygon
    return Polygon(pts).buffer(0.25 * r_in).buffer(-0.1 * r_in)


def raster(geom, shape, origin):
    """Rasterise a shapely geometry into a uint8 mask (row 0 = top) on the map grid."""
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for p in getattr(geom, "geoms", [geom]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        to_px = lambda cs: np.array([[(x - origin[0]) / PX, h - (y - origin[1]) / PX] for x, y in cs], np.int32)
        cv2.fillPoly(m, [to_px(p.exterior.coords)], 1)
        for r in p.interiors:
            cv2.fillPoly(m, [to_px(r.coords)], 0)
    return m


def build(image, who, height):
    person = PEOPLE[who]
    fig_h = height * 0.86
    img, fig = figure(image, person["crop"], fig_h)
    fh, fw = fig.shape

    # letter behind the figure, figure on its lower right (all in mm, y up)
    items = letter_shapes(person, height * 0.62)
    L_all = unary_union([g for g, _ in items])
    lminx, lminy, lmaxx, lmaxy = L_all.bounds
    fx0 = lmaxx - fw * PX * 0.55                       # figure left edge, mm
    fy0 = lminy - 0.10 * height                        # figure bottom, mm
    fig_poly_px = cv2.findContours(fig, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    from shapely.geometry import Polygon
    fig_poly = unary_union([Polygon([(fx0 + p[0][0] * PX, fy0 + (fh - p[0][1]) * PX) for p in c]).buffer(0)
                            for c in fig_poly_px if len(c) >= 3])
    outline = unary_union([fig_poly, L_all]).buffer(BORDER_MM + OUTLINE_MM)
    # keyring tab on the highest point of the shape, overlapping it so it is part of the piece
    top_pt = max(outline.exterior.coords, key=lambda q: q[1])
    tab = (top_pt[0], top_pt[1] + 2.8)
    outline = unary_union([outline, Point(tab).buffer(5.0, 64)])
    hole = Point(tab).buffer(2.3, 64)
    outline = outline.difference(hole)

    ox, oy = outline.bounds[0] - 1, outline.bounds[1] - 1
    W = int(math.ceil((outline.bounds[2] - ox + 1) / PX)); Hh = int(math.ceil((outline.bounds[3] - oy + 1) / PX))
    inside = raster(outline, (Hh, W), (ox, oy)) > 0

    levels = level_colours(); lab_levels = to_lab(levels)
    N = len(levels) - 1
    top = N
    lev = np.zeros((Hh, W), np.int16)

    # letter: fill = full skin tone, light = white, dark = black, then dark outline
    tone = {"fill": STACK[0][3] + 2, "light": 0, "dark": top}
    for g, role in items:
        lev[raster(g, (Hh, W), (ox, oy)) > 0] = tone[role]
    lev[raster(L_all.boundary.buffer(OUTLINE_MM / 2 + 0.15), (Hh, W), (ox, oy)) > 0] = top

    # figure: best-matching layer count per pixel
    c0 = int(round((fx0 - ox) / PX)); r0 = Hh - int(round((fy0 - oy) / PX)) - fh
    tgt = cv2.GaussianBlur(img, (3, 3), 0)[..., ::-1].astype(float) / 255.0
    tl = to_lab(tgt.reshape(-1, 3)).reshape(fh, fw, 3)
    d = ((tl[..., None, :] - lab_levels[None, None]) ** 2 * np.array([2.0, 1.0, 1.0])).sum(-1)
    flev = d.argmin(-1).astype(np.int16)
    region = lev[r0:r0 + fh, c0:c0 + fw]
    region[fig > 0] = flev[fig > 0]
    edge = cv2.morphologyEx(fig, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    pale = (hsv[..., 2] > 200) & (hsv[..., 1] < 40)
    near_edge = cv2.dilate(edge.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    region[(edge | (pale & near_edge)) & (fig > 0)] = top  # crisp dark edge, no white fringe
    covered = np.zeros((Hh, W), bool)
    covered[r0:r0 + fh, c0:c0 + fw] |= fig > 0
    covered |= raster(L_all.buffer(OUTLINE_MM / 2 + 0.15), (Hh, W), (ox, oy)) > 0
    lev[inside & ~covered] = top                       # only the thin rim left between them

    # outer border ring in the darkest tone
    border = inside & ~(raster(outline.buffer(-BORDER_MM), (Hh, W), (ox, oy)) > 0)
    lev[border] = top
    lev[~inside] = -1
    return lev, levels, (ox, oy), outline


def heights(lev):
    base_top = FIRST + (BASE_LAYERS - 1) * LH
    return np.where(lev >= 0, base_top + np.maximum(lev, 0) * LH, 0.0), base_top


def write_stl(z, inside, path):
    """Watertight column mesh from a height map (binary STL)."""
    h, w = z.shape
    tris = []
    ys, xs = np.nonzero(inside)
    X0, X1 = xs * PX, (xs + 1) * PX
    Y0, Y1 = (h - ys - 1) * PX, (h - ys) * PX
    Z = z[ys, xs]; zero = np.zeros_like(Z)
    def quad(a, b, c, d):  # a,b,c,d counter-clockwise seen from outside
        tris.append(np.stack([a, b, c], 1)); tris.append(np.stack([a, c, d], 1))
    P = lambda x, y, zz: np.stack([x, y, zz], 1)
    quad(P(X0, Y0, Z), P(X1, Y0, Z), P(X1, Y1, Z), P(X0, Y1, Z))                 # top
    quad(P(X0, Y0, zero), P(X0, Y1, zero), P(X1, Y1, zero), P(X1, Y0, zero))     # bottom
    zpad = np.pad(np.where(inside, z, 0.0), 1)
    for dy, dx in ((0, 1), (0, -1), (-1, 0), (1, 0)):                             # side walls
        nz = zpad[ys + 1 + dy, xs + 1 + dx]
        m = nz < Z
        lo, hi = nz[m], Z[m]
        x0, x1, y0, y1 = X0[m], X1[m], Y0[m], Y1[m]
        if dx == 1:   # wall at x1 facing +x
            quad(P(x1, y0, lo), P(x1, y1, lo), P(x1, y1, hi), P(x1, y0, hi))
        elif dx == -1:
            quad(P(x0, y1, lo), P(x0, y0, lo), P(x0, y0, hi), P(x0, y1, hi))
        elif dy == -1:  # row above = +y
            quad(P(x1, y1, lo), P(x0, y1, lo), P(x0, y1, hi), P(x1, y1, hi))
        else:
            quad(P(x0, y0, lo), P(x1, y0, lo), P(x1, y0, hi), P(x0, y0, hi))
    T = np.concatenate(tris).astype(np.float32)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, T
    with open(path, "wb") as f:
        f.write(b"\0" * 80); f.write(np.uint32(len(T)).tobytes()); f.write(rec.tobytes())
    return len(T)


if __name__ == "__main__":
    image, who, out = sys.argv[1:4]
    height = float(sys.argv[4]) if len(sys.argv) > 4 else 90.0
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    lev, levels, origin, outline = build(image, who, height)
    z, base_top = heights(lev)
    inside = lev >= 0
    ntri = write_stl(z, inside, out / "hueforge.stl")

    # preview: simulated look, background grey
    prev = np.where(inside[..., None], levels[np.maximum(lev, 0)], np.array([0.9, 0.9, 0.9]))
    cv2.imwrite(str(out / "preview.png"), cv2.resize((prev[..., ::-1] * 255).astype(np.uint8), None, fx=3, fy=3,
                                                   interpolation=cv2.INTER_NEAREST))
    # colour changes for Bambu Studio: filament 1 = white from the start, then one per band
    changes, layer = [], BASE_LAYERS
    for i, (name, hexcol, td, n) in enumerate(STACK):
        changes.append({"type": "ToolChange", "print_z": round(FIRST + layer * LH, 3), "extruder": i + 2,
                        "color": hexcol, "extra": name})
        layer += n
    json.dump({"mode": "MultiAsSingle", "gcodes": changes}, open(out / "colour_changes.json", "w"), indent=1)
    h, w = lev.shape
    print(f"{w * PX:.1f} x {h * PX:.1f} mm, max {z.max():.2f} mm thick, {ntri} triangles; changes at",
          [c["print_z"] for c in changes])
