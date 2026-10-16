"""Relief keychain: flat filament colours (skin, white shirt, blue jeans, brown hair, black lines)
with the figure raised as a shallow 3D relief so the face gets real shadows from the light.

Stack: black base plate under everything, then each colour as columns up to its height.
Each colour region of the figure is a flat plateau whose height comes from a depth map (depth.py),
so the parts stand out from each other (hands over the shirt, face over the hair) and cast shadows,
while the face and palms stay flat with no layer lines across them. The drawing's dark lines on the
face and hands are kept (engraved one layer) so the features stay the original drawing's.

Usage: python relief.py <image> <girl|boy> <depth.npy> <out dir> [height_mm]
Writes <colour>.stl per filament, preview.png and heights.npz (for renders).
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from hueforge import PEOPLE, letter_shapes  # noqa: E402

PX = 0.1                     # mm per map pixel
BASE = 1.2                   # black backing plate, mm
PLATE = 2.0                  # top of letter / rim / lowest point of the figure
LAYER = 0.12                 # print layer height; plateaus sit on whole layers
PLATEAU_LO, PLATEAU_HI = 0.36, 1.8   # height above PLATE of the farthest / nearest region, mm
MIN_PLATEAU = 2.0            # mm2; smaller regions (eyes, teeth) take the height around them
ROUND_W, ROUND_H = 0.8, 0.24 # rounded rim of each region: width, drop (two layers)
LINE_DEPTH = 0.12            # face lines sit one layer below the skin around them
OUTLINE_MM = 1.1             # black rim around the whole shape

# class -> (filament name, display colour); index = class id
CLASSES = [("black", "#1C1C1C"), ("white", "#F4F4F4"), ("skin", "#D69C76"),
           ("blue", "#4F739E"), ("brown", "#4A2C1A"), ("pink", "#F27BA8")]
BLACK, WHITE, SKIN, BLUE, BROWN, PINK = range(6)
# reference colours in the drawing (RGB) -> class
REFS = [((235, 236, 242), WHITE), ((214, 214, 226), WHITE), ((190, 190, 208), WHITE),
        ((147, 145, 166), WHITE), ((168, 166, 186), WHITE), ((186, 187, 189), WHITE),   # shirt / shoe shadows
        ((228, 174, 140), SKIN), ((205, 142, 108), SKIN), ((238, 196, 168), SKIN), ((180, 118, 88), SKIN), ((160, 100, 72), SKIN), ((145, 92, 68), SKIN),
        ((87, 116, 135), BLUE), ((112, 140, 160), BLUE), ((60, 85, 110), BLUE), ((36, 52, 76), BLUE),
        ((92, 62, 44), BROWN), ((120, 86, 62), BROWN), ((66, 45, 33), BROWN),
        ((30, 24, 22), BLACK), ((48, 36, 32), BLACK)]


def raster(geom, shape, origin):
    """Rasterise a shapely geometry into a uint8 mask (row 0 = top) on this map's grid."""
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    to_px = lambda cs: np.array([[(x - origin[0]) / PX, h - (y - origin[1]) / PX] for x, y in cs], np.int32)
    for p in getattr(geom, "geoms", [geom]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        cv2.fillPoly(m, [to_px(p.exterior.coords)], 1)
        for r in p.interiors:
            cv2.fillPoly(m, [to_px(r.coords)], 0)
    return m


def lab(rgb):
    u8 = np.clip(np.asarray(rgb, np.float32), 0, 255).astype(np.uint8).reshape(-1, 1, 3)
    return cv2.cvtColor(u8, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)


def load(image, who, depth_path, fig_h):
    x0, y0, x1, y1 = PEOPLE[who]["crop"]
    img = cv2.imread(image)[y0:y1, x0:x1]
    dep = np.load(depth_path)
    s = fig_h / img.shape[0] / PX
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    dep = cv2.resize(dep, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    bg = ((hsv[..., 2] > 240) & (hsv[..., 1] < 14)).astype(np.uint8)
    # background = pure-white areas reached from the border, plus enclosed pure-white holes > 1 mm2
    n, cc, st, _ = cv2.connectedComponentsWithStats(bg, connectivity=4)
    h, w = bg.shape
    keep_bg = np.zeros(n, bool)
    for i in range(1, n):
        x, y, ww, hh, a = st[i]
        touches = x == 0 or y == 0 or x + ww == w or y + hh == h
        keep_bg[i] = touches or a * PX * PX > 1.0
    fig = ~keep_bg[cc]
    fig = cv2.morphologyEx(fig.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, cc, st, _ = cv2.connectedComponentsWithStats(fig)
    fig = cc == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    return img, dep, fig


def mode_filter(cls, mask, k=3, keep=None):
    """Per-pixel majority over a k x k window, only inside mask; `keep` pixels stay as they are."""
    votes = np.stack([cv2.boxFilter((cls == c).astype(np.float32), -1, (k, k), normalize=False)
                      for c in range(len(CLASSES))])
    out = np.where(mask, votes.argmax(0), cls)
    if keep is not None:
        out[keep] = cls[keep]
    return out


def classify(img, fig):
    rgb = cv2.GaussianBlur(img, (3, 3), 0)[..., ::-1]
    L = lab(rgb.reshape(-1, 3)).reshape(*rgb.shape[:2], 3)
    refs = lab([r for r, _ in REFS]); ids = np.array([c for _, c in REFS])
    d = ((L[..., None, :] - refs) ** 2 * np.array([1.4, 1.0, 1.0], np.float32)).sum(-1)
    cls = ids[d.argmin(-1)]
    # dark pixels: thick dark areas are hair (brown), thin ones are drawn lines (black)
    dark = (L[..., 0] < 75) & np.isin(cls, (BLACK, BROWN)) & (L[..., 2] > 120)   # not the dark-blue denim
    thick = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0
    cls[dark & thick] = BROWN
    cls[dark & ~thick] = BLACK
    cls[~fig] = BLACK
    # drawn lines on the skin (mouth, eyelids, nose, fingers) are lighter than the hair lines:
    # take whatever is clearly darker than the skin around it
    skin = (cls == SKIN) & fig
    w = cv2.GaussianBlur(skin.astype(np.float32), (0, 0), 1.5 / PX)
    loc = cv2.GaussianBlur(np.where(skin, L[..., 0], 0), (0, 0), 1.5 / PX) / np.maximum(w, 1e-3)
    cls[skin & (w > 0.35) & (L[..., 0] < loc - 45)] = BLACK
    # pure-white specks left between curls and along the silhouette are background: make them rim (black)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    pure = (hsv[..., 2] > 240) & (hsv[..., 1] < 14) & fig
    n, cc, st, _ = cv2.connectedComponentsWithStats(pure.astype(np.uint8))
    rim = cv2.distanceTransform(fig.astype(np.uint8), cv2.DIST_L2, 5) * PX < 0.5
    for i in range(1, n):
        m = cc == i
        ring = (cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~m
        around = cls[ring & fig]
        if (ring & ~fig).any() or (around.size and np.mean(np.isin(around, (BROWN, BLACK))) > 0.5):
            cls[m] = BLACK
    cls[pure & rim] = BLACK
    # pastel bows / small odd blobs on the shirt -> white: small skin or pink components inside white
    # and dark folds on the jeans that read as hair -> blue
    for c, into in ((SKIN, WHITE), (BROWN, BLUE), (WHITE, BLUE), (BLUE, None)):
        n, cc, st, _ = cv2.connectedComponentsWithStats(((cls == c) & fig).astype(np.uint8))
        big = st[1:, cv2.CC_STAT_AREA].max()
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < {SKIN: 0.2, BROWN: 0.2, WHITE: 0.04}.get(c, 0.02) * big:
                ring = cv2.dilate((cc == i).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
                around = cls[ring & (cc != i) & fig & ((cls != BLACK) | (into is None))]
                if not around.size:
                    continue
                major = np.bincount(around, minlength=6).argmax()
                if into is None or major == into:     # None: small blue bits take whatever surrounds them
                    cls[cc == i] = major
    # black lines inside one flat region (shirt folds, jeans seams, hair strands) take that region's colour;
    # lines on skin (face features, fingers) and lines between two regions stay black
    near = np.stack([cv2.dilate((cls == c).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
                     for c in range(len(CLASSES))])
    blk = (cls == BLACK) & fig
    for c in (WHITE, BLUE, BROWN):
        others = [o for o in (WHITE, SKIN, BLUE, BROWN) if o != c]
        only = near[c] & ~near[others].any(0)
        cls[blk & only] = c
    # clean speckle, keep the face lines
    face_lines = (cls == BLACK) & near[SKIN] & fig
    for _ in range(2):
        cls = mode_filter(cls, fig, 3, keep=face_lines)
    # face lines at least ~0.4 mm wide (one nozzle line), growing into the skin only
    grown = cv2.dilate(((cls == BLACK) & near[SKIN] & fig).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    cls[grown & (cls == SKIN)] = BLACK
    # pale or blue bits caught between hair curls at the silhouette -> rim
    edge = cv2.distanceTransform(fig.astype(np.uint8), cv2.DIST_L2, 5) * PX < 0.8
    hairy = cv2.dilate((cls == BROWN).astype(np.uint8), np.ones((13, 13), np.uint8)) > 0
    cls[edge & hairy & np.isin(cls, (WHITE, BLUE))] = BLACK
    # islands under 0.1 mm2 -> majority of their surroundings
    for c in range(len(CLASSES)):
        n, cc, st, _ = cv2.connectedComponentsWithStats(((cls == c) & fig).astype(np.uint8))
        for i in np.nonzero(st[1:, cv2.CC_STAT_AREA] * PX * PX < 0.1)[0] + 1:
            m = cc == i
            ring = (cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & ~m & fig
            if ring.any():
                cls[m] = np.bincount(cls[ring], minlength=6).argmax()
    return cls


def relief(dep, fig, cls):
    """Layered relief: every colour region is a flat plateau at its own height (from the depth map, in
    whole layers), with only a rounded rim at its edges, so no layer lines run across the face or hands."""
    d = dep.astype(np.float32)
    lo, hi = np.percentile(d[fig], [2, 98])
    dn = np.clip((d - lo) / (hi - lo), 0, 1)
    h = np.zeros(fig.shape, np.float32)
    own = np.zeros(fig.shape, bool)
    for c in (WHITE, SKIN, BLUE, BROWN):
        n, cc, st, _ = cv2.connectedComponentsWithStats(((cls == c) & fig).astype(np.uint8))
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] * PX * PX < MIN_PLATEAU:
                continue                                   # eyes, teeth: take the height around them
            m = cc == i
            h[m] = PLATEAU_LO + (PLATEAU_HI - PLATEAU_LO) * np.median(dn[m])
            own |= m
    h = np.round(h / LAYER) * LAYER
    # small parts and drawn lines take the highest plateau next to them
    k = np.ones((3, 3), np.uint8)
    todo = fig & ~own
    for _ in range(60):
        if not todo.any():
            break
        grown = cv2.dilate(np.where(own, h, 0), k)
        reach = todo & (cv2.dilate(own.astype(np.uint8), k) > 0)
        h[reach] = grown[reach]; own |= reach; todo &= ~reach
    # soft rounded rim inside each plateau (a couple of layers), lines engraved one layer
    rim = np.zeros(fig.shape, np.float32)
    for c in (WHITE, SKIN, BLUE, BROWN):
        m = ((cls == c) & fig).astype(np.uint8)
        body = ((m > 0) | ((cls == BLACK) & fig)).astype(np.uint8)   # drawn lines don't start a rim
        dist = cv2.distanceTransform(body, cv2.DIST_L2, 3) * PX
        s = np.clip(dist / ROUND_W, 0, 1)
        rim = np.where(m > 0, ROUND_H * (1 - (1 - s) ** 2) - ROUND_H, rim)
    h = h + rim
    h[(cls == BLACK) & fig] -= LINE_DEPTH
    return np.where(fig, PLATE + np.maximum(h, 0.15), 0)


def build(image, who, depth_path, height):
    fig_h = height * 0.86
    img, dep, fig = load(image, who, depth_path, fig_h)
    fh, fw = fig.shape
    cls_f = classify(img, fig)
    zf = relief(dep, fig, cls_f)

    items = letter_shapes(PEOPLE[who], height * 0.62)
    L_all = unary_union([g for g, _ in items])
    lminx, lminy, lmaxx, lmaxy = L_all.bounds
    fx0 = lmaxx - fw * PX * 0.55
    fy0 = lminy - 0.10 * height
    cont = cv2.findContours(fig.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    fig_poly = unary_union([Polygon([(fx0 + p[0][0] * PX, fy0 + (fh - p[0][1]) * PX) for p in c]).buffer(0)
                            for c in cont if len(c) >= 3])
    outline = unary_union([fig_poly, L_all]).buffer(OUTLINE_MM)
    top_pt = max(outline.exterior.coords, key=lambda q: q[1])
    tab = (top_pt[0], top_pt[1] + 2.8)
    outline = unary_union([outline, Point(tab).buffer(5.0, 64)]).difference(Point(tab).buffer(2.3, 64))

    ox, oy = outline.bounds[0] - 1, outline.bounds[1] - 1
    W = int(math.ceil((outline.bounds[2] - ox + 1) / PX)); H = int(math.ceil((outline.bounds[3] - oy + 1) / PX))
    inside = raster(outline, (H, W), (ox, oy)) > 0
    cls = np.full((H, W), BLACK, np.int16)
    z = np.where(inside, PLATE, 0.0)
    colour = {"fill": PINK, "light": WHITE, "dark": BLACK}
    for g, role in items:
        cls[raster(g, (H, W), (ox, oy)) > 0] = colour[role]
    cls[raster(L_all.boundary.buffer(0.35), (H, W), (ox, oy)) > 0] = BLACK
    c0 = int(round((fx0 - ox) / PX)); r0 = H - int(round((fy0 - oy) / PX)) - fh
    reg_c, reg_z = cls[r0:r0 + fh, c0:c0 + fw], z[r0:r0 + fh, c0:c0 + fw]
    reg_c[fig], reg_z[fig] = cls_f[fig], zf[fig]
    cls[~inside] = -1; z[~inside] = 0
    return cls, z, inside


def write_body(z, mask, z0, path):
    """Watertight column mesh: columns from z0 up to z over `mask` (binary STL)."""
    h, w = z.shape
    tris = []
    ys, xs = np.nonzero(mask)
    X0, X1 = xs * PX, (xs + 1) * PX
    Y0, Y1 = (h - ys - 1) * PX, (h - ys) * PX
    Z = z[ys, xs]; B = np.full_like(Z, z0)
    P = lambda x, y, zz: np.stack([x, y, zz], 1)
    def quad(a, b, c, d):
        tris.append(np.stack([a, b, c], 1)); tris.append(np.stack([a, c, d], 1))
    quad(P(X0, Y0, Z), P(X1, Y0, Z), P(X1, Y1, Z), P(X0, Y1, Z))
    quad(P(X0, Y0, B), P(X0, Y1, B), P(X1, Y1, B), P(X1, Y0, B))
    zpad = np.pad(np.where(mask, z, z0), 1, constant_values=z0)
    for dy, dx in ((0, 1), (0, -1), (-1, 0), (1, 0)):
        nz = zpad[ys + 1 + dy, xs + 1 + dx]
        m = nz < Z
        lo, hi = nz[m], Z[m]
        x0, x1, y0, y1 = X0[m], X1[m], Y0[m], Y1[m]
        if dx == 1:
            quad(P(x1, y0, lo), P(x1, y1, lo), P(x1, y1, hi), P(x1, y0, hi))
        elif dx == -1:
            quad(P(x0, y1, lo), P(x0, y0, lo), P(x0, y0, hi), P(x0, y1, hi))
        elif dy == -1:
            quad(P(x1, y1, lo), P(x0, y1, lo), P(x0, y1, hi), P(x1, y1, hi))
        else:
            quad(P(x0, y0, lo), P(x1, y0, lo), P(x1, y0, hi), P(x0, y0, hi))
    T = np.concatenate(tris).astype(np.float32)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(T), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = nrm, T
    with open(path, "wb") as f:
        f.write(b"\0" * 80); f.write(np.uint32(len(T)).tobytes()); f.write(rec.tobytes())


if __name__ == "__main__":
    image, who, depth_path, out = sys.argv[1:5]
    height = float(sys.argv[5]) if len(sys.argv) > 5 else 90.0
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    cls, z, inside = build(image, who, depth_path, height)
    np.savez_compressed(out / "heights.npz", cls=cls, z=z, px=PX)
    used = []
    for c, (name, _) in enumerate(CLASSES):
        if c == BLACK:   # black = base plate everywhere + black columns on top
            zb = np.where(cls == BLACK, z, BASE)
            write_body(zb, inside, 0.0, out / f"{name}.stl")
        else:
            m = cls == c
            if not m.any():
                continue
            write_body(z, m, BASE, out / f"{name}.stl")
        used.append(name)
    pal = np.array([[int(h[i:i + 2], 16) for i in (5, 3, 1)] for _, h in CLASSES], np.uint8)  # BGR
    prev = np.where(inside[..., None], pal[np.maximum(cls, 0)], 230).astype(np.uint8)
    cv2.imwrite(str(out / "preview.png"), prev)
    print("filaments (AMS order):", " ".join(used))
    print(f"size {inside.shape[1] * PX:.1f} x {inside.shape[0] * PX:.1f} mm, thickness {z.max():.2f} mm")
