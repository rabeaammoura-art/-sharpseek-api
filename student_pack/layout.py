"""Compose a student-pack piece (tag, bottle, pencil, ruler) from traced motifs + a typed name.

All geometry is shapely polygons in mm, x right / y up, lower-left of the piece at (0, 0).
A piece is a painter's-algorithm list of (colour, polygon) ops; `resolve()` turns it into disjoint
per-colour regions (later ops cover earlier ones), applies the minimum-feature clean-up, cuts the holes
and returns a `Piece` ready for meshing.

Layer stack (per theme `heights`): base slab BASE in the outline colour over the whole silhouette, then every
colour region is raised from BASE up to its own height.  Pencil plates use a 10.4 mm base instead and the
same raises on top.
"""
from dataclasses import dataclass, field

from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from geo import load_motifs
from textgeo import BOLD, EXTRABOLD, text_geom
from themes import THEMES

BASE = 1.6
PENCIL_BASE = 10.4
MIN_FEATURE = 0.8
HOLE_D = 5.0                      # hanging hole
PENCIL_HOLE_D = 7.7               # 7.2 pencil + 0.5 clearance
TUNNEL_CENTER_Z = 5.2
TUNNEL_ROOF_CUT = 4.4             # teardrop apex cut this far above the tunnel axis (roof z = 9.6 < 10.4 - 0.8)
RULER_W, RULER_H, RULER_MM = 165.0, 50.0, 150
NAME_FONT = EXTRABOLD


@dataclass
class Piece:
    kind: str
    theme: str
    name: str
    parts: dict                   # colour -> shapely geometry (disjoint, clipped to silhouette, holes cut)
    silhouette: object            # shapely geometry (holes cut)
    base: float
    tops: dict                    # colour -> top z (mm)
    outline: str
    holes: list = field(default_factory=list)      # [(cx, cy, diameter)] through holes
    tunnel: dict = None           # pencil: {"y": .., "d": .., "zc": .., "roof_cut": ..}
    notes: list = field(default_factory=list)

    @property
    def bounds(self):
        return self.silhouette.bounds

    @property
    def size(self):
        b = self.bounds
        return b[2] - b[0], b[3] - b[1], max(self.tops.values())


# ------------------------------------------------------------------ helpers
def _polys(g):
    if g is None or g.is_empty:
        return []
    return [p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.geom_type == "Polygon" and not p.is_empty]


def opening(g, r):
    return g.buffer(-r, join_style=1).buffer(r, join_style=1)


def _drop_small(g, min_area=2.0):
    return unary_union([p for p in _polys(g) if p.area >= min_area])


def place(motif, x, y, scale=1.0, mirror=False):
    """Motif layers -> [(colour, geom)] with the motif's lower-left corner at (x, y)."""
    out = []
    for color, g in motif["layers"].items():
        if mirror:
            g = affinity.scale(g, -1, 1, origin=(motif["width"] / 2, 0))
        g = affinity.scale(g, scale, scale, origin=(0, 0))
        out.append((color, affinity.translate(g, x, y)))
    return out


def fit_scale(motif, max_w=None, max_h=None, cap=1.0):
    s = cap
    if max_w: s = min(s, max_w / motif["width"])
    if max_h: s = min(s, max_h / motif["height"])
    return s


def name_block(theme, name, cap_h, max_letters_w, min_cap=5.0):
    """Letters + rings.  Returns (ops, letters, R) in local coords, letters' lower-left at (R, R)."""
    th = THEMES[theme]
    rings = th["text_rings"]
    R = sum(w for _, w in rings)
    letters = text_geom(name.upper(), cap_h, NAME_FONT).buffer(0.2, join_style=1)   # slightly bubbly
    lw = letters.bounds[2] - letters.bounds[0]
    notes = []
    if lw > max_letters_w:
        k = max_letters_w / lw
        letters = affinity.scale(letters, k, k, origin=(0, 0))
        if cap_h * k < min_cap:
            notes.append(f"name '{name}' is long: letters only {cap_h * k:.1f} mm tall")
    b = letters.bounds
    letters = affinity.translate(letters, R - b[0], R - b[1])
    ops, cum = [], 0.0
    layers = []
    for color, w in rings:
        cum += w
        layers.append((color, cum))
    for color, c in reversed(layers):
        ring = letters.buffer(c, join_style=1)
        if c > 1.5:   # bubble outline: round off the notches between letters
            ring = ring.buffer(1.0, join_style=1).buffer(-1.0, join_style=1)
        ops.append((color, ring, False))
    ops.append((th["letters"], letters, False))
    return ops, letters, R, notes


# ------------------------------------------------------------------ resolve
def resolve(kind, theme, name, ops, silhouette, holes=(), base=BASE, tunnel=None, notes=()):
    th = THEMES[theme]
    colors = list(th["heights"])
    canvas = {c: Polygon() for c in colors}
    exempt_geom = {c: Polygon() for c in colors}
    for color, g, exempt in ops:
        if exempt:
            exempt_geom[color] = exempt_geom[color].union(g)
        g = g if exempt else _drop_small(opening(g, MIN_FEATURE / 2))
        if g.is_empty:
            continue
        for c in colors:
            if c != color and not canvas[c].is_empty:
                canvas[c] = canvas[c].difference(g)
        canvas[color] = canvas[color].union(g)
    hole_geoms = [Point(cx, cy).buffer(d / 2, 64) for cx, cy, d in holes]
    cut = unary_union(hole_geoms) if hole_geoms else Polygon()
    sil = silhouette.difference(cut)
    parts = {}
    for c, g in canvas.items():
        g = g.intersection(sil)
        if not exempt_geom[c].is_empty:      # ticks/numbers keep their 0.5 mm lines; everything else is re-cleaned
            g = unary_union([_drop_small(opening(g, MIN_FEATURE / 2)), g.intersection(exempt_geom[c].buffer(0.02))])
        else:
            g = _drop_small(opening(g, MIN_FEATURE / 2))
        g = unary_union(_polys(g.buffer(0))).simplify(0.02)
        if not g.is_empty:
            parts[c] = g
    tops = {c: base + (h - BASE) for c, h in th["heights"].items()}
    return Piece(kind, theme, name, parts, sil.simplify(0.02), base, tops, th["outline"],
                 [tuple(h) for h in holes], tunnel, list(notes))


def make_silhouette(ops, extra=None, close=0.6, min_hole=10.0):
    g = unary_union([o[1] for o in ops] + ([extra] if extra is not None else []))
    g = g.buffer(close, join_style=1).buffer(-close, join_style=1)
    g = opening(g, 0.4)                       # no hair-thin spurs on the outline
    polys = []
    for p in _polys(g):
        polys.append(Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= min_hole]))
    return unary_union(polys)


def add_tab(sil, tab_x, hole_d=HOLE_D, wall=2.0):
    """Hanging tab: rounded stem + ring above the silhouette at tab_x, hole of hole_d.  Returns (tab, hole)."""
    R = hole_d / 2 + wall
    ys = []
    for dx in (-R * 0.8, 0, R * 0.8):
        line = box(tab_x + dx - 0.05, -50, tab_x + dx + 0.05, 500).intersection(opening(sil, 0.6))
        if not line.is_empty:
            ys.append(line.bounds[3])
    top = min(ys)
    cy = top + hole_d / 2 + 0.6
    tab = unary_union([Point(tab_x, cy).buffer(R, 64), box(tab_x - R, top - 4, tab_x + R, cy)])
    return tab, (tab_x, cy, hole_d)


def normalise(ops, silhouette, holes, tunnel=None):
    """Shift so the silhouette's lower-left is (0, 0)."""
    b = silhouette.bounds
    dx, dy = -b[0], -b[1]
    ops = [(c, affinity.translate(g, dx, dy), e) for c, g, e in ops]
    sil = affinity.translate(silhouette, dx, dy)
    holes = [(x + dx, y + dy, d) for x, y, d in holes]
    if tunnel:
        tunnel = dict(tunnel, y=tunnel["y"] + dy)
    return ops, sil, holes, tunnel


# ------------------------------------------------------------------ pieces
def _tag(theme, name, kind, width, cap_h):
    th = THEMES[theme]
    m = load_motifs(theme)[kind]
    cb = unary_union(list(m["layers"].values())).bounds                  # artwork extents inside the crop
    ms = width / (cb[2] - cb[0])
    rings = th["text_rings"]
    R = sum(w for _, w in rings)
    nops, letters, R, notes = name_block(theme, name, cap_h, width - 2 * R - 0.5)
    lb = letters.bounds
    lw = lb[2] - lb[0]
    nops = [(c, affinity.translate(g, (width - lw) / 2 - R, 0), e) for c, g, e in nops]
    letters = affinity.translate(letters, (width - lw) / 2 - R, 0)
    overlap = 1.2
    my = letters.bounds[3] + R - overlap
    ops = [(c, g, False) for c, g in place(m, -cb[0] * ms, my - cb[1] * 0, ms)] + nops
    sil = make_silhouette(ops)
    tab, hole = add_tab(sil, (m["tab_x"] - cb[0]) * ms)
    ops.append((th["outline"], tab, False))
    sil = make_silhouette(ops)
    ops, sil, holes, _ = normalise(ops, sil, [hole])
    return resolve(kind, theme, name, ops, sil, holes, notes=notes)


def tag(theme, name):
    return _tag(theme, name, "tag", 70.0, 13.0)


def bottle(theme, name):
    return _tag(theme, name, "bottle", 48.0, 9.5)


def pencil(theme, name, length=85.0, plate_h=24.0):
    th = THEMES[theme]
    ms_all = load_motifs(theme)
    left, right = ms_all.get("pencil_l"), ms_all.get("pencil_r")
    mirror_right = False
    if right is None and left is not None:
        right, mirror_right = left, True
    R = sum(w for _, w in th["text_rings"])
    cap_default = 11.0
    sl = fit_scale(left, max_h=plate_h, cap=0.9) if left else 0
    sr = fit_scale(right, max_h=plate_h, cap=0.9) if right else 0
    wl = left["width"] * sl if left else 0
    wr = right["width"] * sr if right else 0
    overlap = 1.5
    avail = length - wl - wr + overlap * ((1 if left else 0) + (1 if right else 0)) - 2 * R
    nops, letters, R, notes = name_block(theme, name, cap_default, avail)
    lb = letters.bounds
    lw = lb[2] - lb[0]
    # name block origin x so that the whole piece is `length` long and centred between the motifs
    x_text = wl - overlap if left else 0
    if lw + 2 * R < length - wl - wr + 2 * overlap - 0.01:          # short name: centre it in the free space
        x_text += (length - wl - wr + 2 * overlap - (lw + 2 * R)) / 2 if (left or right) else (length - lw - 2 * R) / 2
    nops = [(c, affinity.translate(g, x_text, 0), e) for c, g, e in nops]
    letters = affinity.translate(letters, x_text, 0)
    yc = (letters.bounds[1] + letters.bounds[3]) / 2
    ops = []
    if left:
        ops += [(c, g, False) for c, g in place(left, 0, yc - left["height"] * sl / 2, sl)]
    if right:
        ops += [(c, g, False) for c, g in place(right, x_text + lw + 2 * R - overlap, yc - right["height"] * sr / 2, sr, mirror_right)]
    ops += nops
    pad = PENCIL_HOLE_D + 2 * 2.0                                      # always >= 2 mm wall each side of the tunnel
    capsule = box(1.0, yc - pad / 2 + 1.0, length - 1.0, yc + pad / 2 - 1.0).buffer(1.0, 16)
    sil = make_silhouette(ops, extra=capsule)
    tunnel = dict(y=yc, d=PENCIL_HOLE_D, zc=TUNNEL_CENTER_Z, roof_cut=TUNNEL_ROOF_CUT)
    ops, sil, holes, tunnel = normalise(ops, sil, [], tunnel)
    return resolve("pencil", theme, name, ops, sil, [], base=PENCIL_BASE, tunnel=tunnel, notes=notes)


def ruler(theme, name):
    th = THEMES[theme]
    rc = th["ruler"]
    W, H, rim = RULER_W, RULER_H, rc["rim_w"]
    outer = box(0, 0, W, H).buffer(-4).buffer(4, 32)                       # R4 corners
    inner = outer.buffer(-rim, join_style=1)
    ops = [(rc["rim"], outer.difference(inner), False)]
    if rc["body"]:
        ops.append((rc["body"], inner, False))
    # --- hazard stripes along the bottom (construction)
    stripe_h = 0.0
    if rc["stripes"]:
        stripe_h = 5.5
        band = box(rim, rim, W - rim, rim + stripe_h)
        bars = []
        for k in range(-3, 24):
            x = rim + k * 10.0
            bars.append(Polygon([(x, rim), (x + 5.0, rim), (x + 5.0 + stripe_h, rim + stripe_h), (x + stripe_h, rim + stripe_h)]))
        ops.append((rc["stripes"], unary_union(bars).intersection(band).intersection(inner), False))
    # --- ticks and numbers: exact millimetres, 0.5 mm lines, 0 mark at x0
    x0 = (W - RULER_MM) / 2
    y_top = H - rim - 1.0
    ticks = []
    for mm in range(RULER_MM + 1):
        L = 4.2 if mm % 10 == 0 else (3.0 if mm % 5 == 0 else 2.0)
        ticks.append(box(x0 + mm - 0.25, y_top - L, x0 + mm + 0.25, y_top))
    numbers = []
    num_base = y_top - 4.2 - 0.6 - 3.2
    for cm in range(RULER_MM // 10 + 1):
        t = text_geom(str(cm), 3.2, BOLD)
        b = t.bounds
        numbers.append(affinity.translate(t, x0 + cm * 10 - (b[0] + b[2]) / 2, num_base))
    layout_top = H - rim + 0.01
    if rc["body"]:    # keep the 0.5 mm gaps between ticks in the body colour (they are thinner than the 0.8 mm clean-up)
        ops.append((rc["body"], box(0, num_base - 0.4, W, layout_top).intersection(inner), True))
    ops.append((rc["ticks"], unary_union(ticks + numbers), True))
    zone_top = num_base - 0.8
    zone_bot = rim + stripe_h + (0.4 if stripe_h else 1.2)
    zone_h = zone_top - zone_bot
    # --- name between the two motifs
    ms = load_motifs(theme)
    left, right = ms.get("ruler_l"), ms.get("ruler_r")
    margin, gap = rim + 3.0, 1.0
    sl = fit_scale(left, max_h=zone_h, max_w=45) if left else 0
    sr = fit_scale(right, max_h=zone_h, max_w=45) if right else 0
    wl = left["width"] * sl if left else 0
    wr = right["width"] * sr if right else 0
    R = sum(w for _, w in th["text_rings"])
    free_l, free_r = margin + wl + (gap if left else 0), W - margin - wr - (gap if right else 0)
    nops, letters, R, notes = name_block(theme, name, min(14.0, zone_h - 2 * R - 1.0), free_r - free_l - 2 * R)
    lb = letters.bounds
    tw = lb[2] - lb[0] + 2 * R
    th_ = lb[3] - lb[1] + 2 * R
    nx = free_l + (free_r - free_l - tw) / 2
    ny = zone_bot + (zone_h - th_) / 2
    nops = [(c, affinity.translate(g, nx, ny), e) for c, g, e in nops]
    halo = rc.get("halo")      # body colour = motif colour: give each motif a sticker outline in the outline colour
    for m_, s_, x_ in ((left, sl, margin), (right, sr, W - margin - wr)):
        if not m_:
            continue
        y_ = zone_bot + (zone_h - m_["height"] * s_) / 2 if not stripe_h else zone_bot
        placed = place(m_, x_, y_, s_)
        if halo:
            ops.append((th["outline"], unary_union([g for _, g in placed]).buffer(halo, join_style=1), False))
        ops += [(c, g, False) for c, g in placed]
    ops += nops
    # keep everything inside the rim
    ops = [(c, g.intersection(inner) if c not in (rc["rim"],) else g, e) for c, g, e in ops]
    return resolve("ruler", theme, name, ops, outer, [], notes=notes)


KINDS = {"tag": tag, "pencil": pencil, "ruler": ruler, "bottle": bottle}


def build_pack(theme, name):
    return {k: f(theme, name) for k, f in KINDS.items()}
