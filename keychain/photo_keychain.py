"""Turn a cartoon of a person into a multi-colour FDM keychain with a decorated letter.

Big regions (hair, skin, clothes, accents) come from the picture: the figure is cut from its
white background, pixels are sorted into filament colours by simple colour rules (so shading
keeps its region's colour), thin line work is dropped, and every region is smoothed and
outlined like a sticker. The face (eyes, brows, nose, smile, cheeks) is redrawn as clean vector
shapes at positions measured on the picture, because at keychain size the original pixels of
the face are too small to survive printing.

Usage: python photo_keychain.py <image> <person> <out dir> [height_mm]
       person = girl | boy  (see PEOPLE: crop, letter, style, face positions in image pixels)
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
from make_keychain import letter  # noqa: E402

UP = 3              # work at 3x the source resolution for smoother contours
REGION_MIN = 1.0    # mm: colour regions narrower than this are merged into neighbours
LINE = 0.42         # mm: half width of outlines (0.84 mm lines)
BORDER = 1.6        # mm: outer border
BASE, TOP = 2.0, 3.2
FIG_H = 44.0        # mm: height of the cropped figure before final scaling

PALETTES = {
    "bow": {"black": "#1C1C1C", "brown": "#4A2C1A", "skin": "#D69C76", "white": "#F4F4F4", "pink": "#F27BA8"},
    "pixel": {"black": "#1C1C1C", "brown": "#4A2C1A", "skin": "#D69C76", "white": "#F4F4F4", "green": "#4FAF3C"},
}

# Positions in pixels of the source picture. hair_below: dark areas above this y are hair (brown),
# below it they are black clothes. print_to_shirt: bright prints on dark clothes become part of
# the clothes. min_area: per-colour smallest patch kept, mm^2 (default 5). body_from / skin_boxes:
# below body_from only the boxes (x0, y0, x1, y1) may hold skin, the rest is clothes (black).
# lines: extra dark strokes (3 points each), e.g. finger creases. eyes: (cx, cy, width, height, tilt deg);
# brows / mouth curves: 3 points each (start, middle, end).
PEOPLE = {
    "girl": dict(letter="S", style="bow", crop=(560, 250, 895, 630), hair_below=10_000,
                 eyes=[(657, 385, 27, 14, -8), (711, 376, 25, 13, -5)],
                 brows=[((639, 367), (652, 358), (667, 356)), ((695, 352), (706, 348), (718, 350))],
                 nose=(686, 411),
                 mouth=dict(upper=((666, 424), (692, 427), (718, 416)), lower=((669, 426), (694, 443), (716, 420))),
                 cheeks=[(650, 409), (728, 401)]),
    "boy": dict(letter="O", style="pixel", crop=(70, 280, 345, 650), hair_below=478,
                print_to_shirt=True, min_area={"skin": 15.0, "white": 15.0},
                body_from=505, skin_boxes=[(215, 462, 292, 660), (75, 612, 116, 660)],
                lines=[((224, 523), (240, 521), (256, 524)), ((226, 540), (241, 538), (256, 541))],
                eyes=[(174, 416, 30, 15, -6), (227, 410, 28, 14, 4)],
                brows=[((151, 400), (167, 391), (185, 389)), ((210, 384), (228, 383), (245, 391))],
                nose=(206, 445),
                mouth=dict(upper=((183, 458), (210, 463), (236, 454)), lower=((187, 461), (211, 479), (232, 458))),
                cheeks=[]),
}


# ---------------------------------------------------------------- picture -> colour regions
def figure_regions(path, crop, palette, person):
    hair_below = person["hair_below"]
    img = cv2.imread(str(path))
    x0, y0, x1, y1 = crop
    img = cv2.resize(img[y0:y1, x0:x1], None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    img = cv2.bilateralFilter(img, 9, 40, 9)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = (hsv[..., i].astype(int) for i in range(3))
    h_px, w_px = H.shape
    px = FIG_H / h_px                                     # mm per working pixel
    disk = lambda mm: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * max(1, round(mm / px)) + 1,) * 2)

    # figure = everything not connected to the white border
    bg = ((V > 232) & (S < 22)).astype(np.uint8)
    ff = bg.copy(); mask = np.zeros((h_px + 2, w_px + 2), np.uint8)
    for sx, sy in ((0, 0), (w_px - 1, 0), (0, h_px - 1), (w_px - 1, h_px - 1)):
        if ff[sy, sx]:
            cv2.floodFill(ff, mask, (sx, sy), 2)
    fig = cv2.morphologyEx((ff != 2).astype(np.uint8), cv2.MORPH_OPEN, disk(0.4))
    n, cc, st, _ = cv2.connectedComponentsWithStats(fig)
    fig = (cc == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    fig = cv2.morphologyEx(fig, cv2.MORPH_CLOSE, disk(0.8))

    names = [k for k in palette if k != "black"] + ["black"]
    accent = [k for k in names if k not in ("black", "brown", "skin", "white")][0]
    idx = {k: i for i, k in enumerate(names)}
    warm = (H <= 25) | (H >= 170)
    dark = V < 135
    dark_big = cv2.morphologyEx(dark.astype(np.uint8), cv2.MORPH_OPEN, disk(0.45)) > 0  # hair / black cloth, not lines
    lab = np.full(H.shape, -1)
    lab[~dark & (S < 45)] = idx["white"]
    lab[~dark & warm & (S >= 45)] = idx["skin"]
    lab[~dark & ~warm & (S >= 70)] = idx["black" if person.get("print_to_shirt") else accent]
    rows = np.arange(h_px)[:, None] / UP + y0                # source-picture y of each row
    lab[dark_big & (rows < hair_below)] = idx["brown"]
    lab[dark_big & (rows >= hair_below)] = idx["black"]
    if "body_from" in person:     # below the neck: skin only where the hands/arms are
        cols = np.arange(w_px)[None, :] / UP + x0
        allowed = np.zeros(H.shape, bool)
        for bx0, by0, bx1, by1 in person["skin_boxes"]:
            allowed |= (cols >= bx0) & (cols <= bx1) & (rows >= by0) & (rows <= by1)
        body = (rows >= person["body_from"]) & ~(allowed & (lab == idx["skin"]))
        lab[body] = idx["black"]
    lab[fig == 0] = -2

    k = len(names)
    def fill_unknown(lab, keep):
        lost = (~keep) & (fig > 0)
        for _ in range(200):
            if not lost.any():
                break
            votes = np.stack([cv2.blur(((lab == i) & keep).astype(np.float32), (7, 7)) for i in range(k)])
            best, has = votes.argmax(0), votes.max(0) > 0
            f = lost & has
            lab[f] = best[f]; keep |= f; lost &= ~f
        return lab
    lab = fill_unknown(lab, lab >= 0)                       # thin lines take their neighbours' colour
    r = disk(0.5)
    votes = np.stack([cv2.blur((lab == i).astype(np.float32), r.shape) for i in range(k)])
    lab = np.where(fig > 0, votes.argmax(0), -2)            # majority smoothing
    keep = np.zeros(lab.shape, bool)
    for i in range(k):                                      # drop regions too narrow to print
        keep |= cv2.morphologyEx((lab == i).astype(np.uint8), cv2.MORPH_OPEN, disk(REGION_MIN / 2)) > 0
    lab = fill_unknown(lab, keep)
    keep = np.ones(lab.shape, bool)                         # drop small patches (fold shadows, specks)
    for i in range(k):
        min_px = person.get("min_area", {}).get(names[i], 5.0) / (px * px)
        n, cc, st, _ = cv2.connectedComponentsWithStats((lab == i).astype(np.uint8))
        for c in range(1, n):
            if st[c, cv2.CC_STAT_AREA] < min_px:
                keep[cc == c] = False
    lab = fill_unknown(lab, keep)

    def polys(m):
        cs, hier = cv2.findContours(m.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        out = []
        for i, c in enumerate(cs if hier is not None else []):
            if hier[0][i][3] != -1 or len(c) < 3:
                continue
            holes, j = [], hier[0][i][2]
            while j != -1:
                if len(cs[j]) >= 3:
                    holes.append([(p[0][0] * px, (h_px - p[0][1]) * px) for p in cs[j]])
                j = hier[0][j][0]
            out.append(Polygon([(p[0][0] * px, (h_px - p[0][1]) * px) for p in c], holes).buffer(0))
        return unary_union(out).simplify(0.08).buffer(0) if out else Polygon()

    regions = {n: polys(lab == i) for n, i in idx.items()}
    to_mm = lambda sx, sy: ((sx - x0) * UP * px, (h_px - (sy - y0) * UP) * px)
    return polys(fig > 0), regions, to_mm, UP * px


# ---------------------------------------------------------------- face, drawn as vectors
def curve(p0, p1, p2, n=20):
    """Quadratic curve through p0 and p2 that passes through p1 at t = 0.5."""
    c = (2 * p1[0] - (p0[0] + p2[0]) / 2, 2 * p1[1] - (p0[1] + p2[1]) / 2)
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def face_items(person, to_mm, s):
    """Draw-order items (shape, colour, outline half-width or 0). s = mm per source pixel."""
    items = []
    for cx, cy in person["cheeks"]:
        x, y = to_mm(cx, cy)
        items.append((affinity.scale(Point(x, y).buffer(1, 32), 1.3, 0.75), "pink", 0))
    for cx, cy, w, h, tilt in person["eyes"]:
        x, y = to_mm(cx, cy)
        ew, eh = max(w * s, 2.8), max(h * s, 1.7)
        white = affinity.rotate(affinity.scale(Point(x, y).buffer(1, 48), ew / 2, eh / 2), -tilt)
        iris = Point(x, y - 0.05).buffer(eh * 0.5, 32)
        lid = LineString(curve((x - ew * 0.55, y + eh * 0.05), (x, y + eh * 0.62), (x + ew * 0.55, y + eh * 0.05)))
        items += [(white, "white", 0), (iris.intersection(white.buffer(0.15)), "brown", 0),
                  (Point(x, y - 0.05).buffer(eh * 0.22, 24), "black", 0),
                  (Point(x + eh * 0.2, y + eh * 0.18).buffer(0.36, 24), "white", 0),
                  (affinity.rotate(lid, -tilt, origin=(x, y)).buffer(LINE * 1.05, cap_style=1), "black", 0)]
    for b in person["brows"]:
        items.append((LineString(curve(*[to_mm(*p) for p in b])).buffer(0.55, cap_style=1), "brown", 0))
    for ln in person.get("lines", []):
        items.append((LineString(curve(*[to_mm(*p) for p in ln])).buffer(LINE, cap_style=1), "black", 0))
    nx, ny = to_mm(*person["nose"])
    items.append((LineString(curve((nx - 0.9, ny + 0.15), (nx, ny - 0.35), (nx + 0.9, ny + 0.15))).buffer(LINE, cap_style=1), "black", 0))
    up = curve(*[to_mm(*p) for p in person["mouth"]["upper"]])
    lo = curve(*[to_mm(*p) for p in person["mouth"]["lower"]])
    mouth = Polygon(up + lo[::-1]).buffer(0.15)
    if mouth.bounds[3] - mouth.bounds[1] < 1.8:   # keep the open smile tall enough to read
        mouth = affinity.scale(mouth, 1.0, 1.8 / (mouth.bounds[3] - mouth.bounds[1]), origin="centroid")
    items.append((mouth, "white", LINE))
    return items


# ---------------------------------------------------------------- the decorated letter
def bow_shape(cx, cy, s):
    loopL = Polygon([(cx, cy), (cx - s, cy + 0.6 * s), (cx - s * 1.05, cy - 0.55 * s)]).buffer(0.18 * s)
    loopR = affinity.scale(loopL, -1, 1, origin=(cx, cy))
    tails = Polygon([(cx - 0.1 * s, cy), (cx - 0.55 * s, cy - 1.0 * s), (cx - 0.25 * s, cy - 1.05 * s), (cx, cy - 0.3 * s),
                     (cx + 0.25 * s, cy - 1.05 * s), (cx + 0.55 * s, cy - 1.0 * s), (cx + 0.1 * s, cy)]).buffer(0.05 * s)
    return unary_union([loopL, loopR, tails]), Point(cx, cy).buffer(0.26 * s)


def letter_items(ch, style, H):
    """(shape, colour, outlined) in draw order."""
    if style == "bow":   # pink S, thin white inline, a bow on top (like the bows on her shirt)
        L = letter(ch, H, 0, 0)
        inline = L.buffer(-1.7).difference(L.buffer(-2.5))
        minx, miny, maxx, maxy = L.bounds
        bow, knot = bow_shape(maxx - 9.5, maxy - 0.5, 6.0)
        return [(L, "pink", True), (inline, "white", False), (bow, "pink", True), (knot, "pink", True)]
    # Minecraft-style pixel O: ring of green blocks with dark seams and a few light blocks
    cell, n = 5.2, 9
    c0 = cell * n / 2
    blocks, light = [], []
    for i in range(n):
        for j in range(n):
            x, y = i * cell, j * cell
            r = math.hypot(x + cell / 2 - c0, (y + cell / 2 - c0) / 1.08)
            if 2.6 * cell <= r <= 4.55 * cell:
                blocks.append(box(x, y, x + cell, y + cell))
                if (i + 2 * j) % 7 == 0:
                    light.append(box(x + 1.0, y + 1.0, x + cell - 1.0, y + cell - 1.0))
    ring = unary_union(blocks)
    seams = unary_union([b.boundary.buffer(0.4) for b in blocks]).intersection(ring)
    k = H / (ring.bounds[3] - ring.bounds[1])
    sc = lambda g: affinity.scale(g, k, k, origin=(0, 0))
    return [(sc(ring), "green", True), (sc(unary_union(light)), "white", False), (sc(seams), "black", False)]


# ---------------------------------------------------------------- assemble
def build(image, who):
    person = PEOPLE[who]
    palette = PALETTES[person["style"]]
    fig_poly, regions, to_mm, s = figure_regions(image, person["crop"], palette, person)

    # sticker outlines between the picture's regions
    strokes = [fig_poly.boundary.buffer(LINE)] + [g.boundary.buffer(LINE) for g in regions.values() if not g.is_empty]
    paint = {n: g for n, g in regions.items() if n != "black"}
    black = unary_union(strokes + [regions.get("black", Polygon())])
    for item, col, outl in face_items(person, to_mm, s):      # face on top
        paint = {n: g.difference(item) for n, g in paint.items()}
        black = black.difference(item)
        if col == "black":
            black = black.union(item)
        else:
            paint[col] = paint.get(col, Polygon()).union(item)
        if outl:
            ring = item.boundary.buffer(outl)
            paint = {n: g.difference(ring) for n, g in paint.items()}
            black = black.union(ring)

    # letter behind: place the figure on its lower right
    items = letter_items(person["letter"], person["style"], 50.0)
    lb = unary_union([g for g, _, _ in items]).bounds
    fb = fig_poly.bounds
    dx, dy = lb[2] - (fb[2] - fb[0]) * 0.62 - fb[0], lb[1] - 2 - fb[1]
    mv = lambda g: affinity.translate(g, dx, dy)
    fig_poly, black = mv(fig_poly), mv(black)
    paint = {n: mv(g) for n, g in paint.items()}

    covered, lstrokes = fig_poly, []
    for shape, col, outlined in reversed(items):
        v = shape.difference(covered)
        if col == "black":
            black = black.union(v)
        else:
            paint[col] = paint.get(col, Polygon()).union(v)
        if outlined:
            lstrokes.append(shape.boundary.buffer(LINE).intersection(v.buffer(LINE)))
        covered = covered.union(shape)
    lstrokes = unary_union(lstrokes).difference(fig_poly)
    paint = {n: g.difference(lstrokes).difference(black) for n, g in paint.items()}
    paint = {n: g.buffer(-0.05).buffer(0.05) for n, g in paint.items()}

    outline = unary_union([fig_poly] + [g for g, _, _ in items]).buffer(BORDER)
    minx, miny, maxx, maxy = outline.bounds
    tab = (minx + 9, maxy + 1.0)
    outline = unary_union([outline, Point(tab).buffer(5.2, 64)]).difference(Point(tab).buffer(2.4, 64))
    paint = {n: g.intersection(outline) for n, g in paint.items()}
    paint["black_top"] = outline.difference(unary_union(list(paint.values())))
    return outline, paint, palette


def export(outline, paint, palette, out, height):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from build123d import Compound, Face, Location, Wire, export_stl, extrude
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath

    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    k = height / (outline.bounds[3] - outline.bounds[1])
    sc = lambda g: affinity.scale(g, k, k, origin=(0, 0))
    polys = lambda g: [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and not p.is_empty]

    fig, ax = plt.subplots(figsize=(6, 6.8))
    for n, g in list(paint.items()):
        col = palette["black"] if n == "black_top" else palette[n]
        for p in polys(sc(g)):
            rings = [list(p.exterior.coords)] + [list(r.coords) for r in p.interiors]
            verts = [v for r in rings for v in r]
            codes = [c for r in rings for c in [MPath.MOVETO] + [MPath.LINETO] * (len(r) - 2) + [MPath.CLOSEPOLY]]
            ax.add_patch(PathPatch(MPath(verts, codes), color=col, lw=0))
    b = sc(outline).bounds
    ax.set_xlim(b[0] - 2, b[2] + 2); ax.set_ylim(b[1] - 2, b[3] + 2)
    ax.set_title(f"{b[2] - b[0]:.0f} x {b[3] - b[1]:.0f} mm, {TOP:.1f} mm thick")
    ax.set_aspect("equal"); ax.axis("off"); fig.patch.set_facecolor("#E6E6E6")
    fig.savefig(out / "preview.png", dpi=170, bbox_inches="tight"); plt.close(fig)

    def solid(g, z0, z1):
        parts = []
        for p in polys(sc(g)):
            if p.area < 0.05:
                continue
            outer = Wire.make_polygon([(x, y, 0) for x, y in p.exterior.coords[:-1]], close=True)
            holes = [Wire.make_polygon([(x, y, 0) for x, y in r.coords[:-1]], close=True) for r in p.interiors]
            parts.append(extrude(Face(outer, holes), amount=z1 - z0).moved(Location((0, 0, z0))))
        return parts

    bodies = {"black": Compound(children=solid(outline, 0, BASE) + solid(paint["black_top"], BASE, TOP))}
    for n, g in paint.items():
        if n != "black_top":
            bodies[n] = Compound(children=solid(g, BASE, TOP))
    for n, bd in bodies.items():
        export_stl(bd, str(out / f"{n}.stl"), tolerance=0.01, angular_tolerance=0.1)
    print(f"size {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} x {TOP} mm;", {n: round(v.volume / 1000, 2) for n, v in bodies.items()})


if __name__ == "__main__":
    image, who, out = sys.argv[1:4]
    height = float(sys.argv[4]) if len(sys.argv) > 4 else 66.0
    export(*build(image, who), out, height)
