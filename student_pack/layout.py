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
from textgeo import BOLD, EXTRABOLD, STENCIL, text_geom
from themes import THEMES

BASE = 1.6
PENCIL_BASE = 13.0                # tested MakerWorld pencil topper: 13 mm tall body
MIN_FEATURE = 0.8
HOLE_D = 5.0                      # hanging hole
PENCIL_HOLE_D = 7.7               # tested topper: 8.0 mm hole (fits standard hexagonal pencils with rounded corners)
TUNNEL_CENTER_Z = 6.0             # floor wall 2.0 mm like the tested topper
TUNNEL_ROOF_CUT = 4.4             # teardrop apex cut this far above the tunnel axis (roof z = 10.4, roof wall 2.6 mm; tested topper: 3.0 with a round hole + supports)
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
    tab: object = None            # hanging-loop footprint (shapely), part of the outline colour
    tab_top: float = None         # if set, the loop is raised to this height (mm) for strength
    tab_colour: str = None        # colour of the loop (default: the outline colour)

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
    if NAME_CUT and NAME_STENCIL:      # stencil font: counters are already open, no bridges needed
        letters = text_geom(name.upper(), cap_h, STENCIL)
    else:
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
    inner = layers[0][0] if layers else None
    for color, c in reversed(layers):
        ring = letters.buffer(c, join_style=1)
        if th.get("fill_counters"):         # ring colour also fills the insides of O, A, R ... (no base colour dot showing through)
            ring = unary_union([Polygon(p.exterior) for p in _polys(ring)])
        if c > 1.5:   # bubble outline: round off the notches between letters
            ring = ring.buffer(1.0, join_style=1).buffer(-1.0, join_style=1)
        # the innermost ring fills the narrow gaps between and inside letters; when its colour differs from the base slab colour,
        # keep those slivers (< 0.8 mm) instead of letting the min-feature clean-up drop them and the base colour show through
        ops.append((color, ring, (c == layers[0][1] and color != th["outline"])))
    ops.append((th["letters"], letters, False))
    return ops, letters, R, notes


RULER_TOP = 2.0        # ruler: every colour ends at the same height (flat, painted-style ticks/numbers); slab 1.6 + 0.4 colour layer
NAME_CUT = False       # ruler: cut the name through the plate (stencil) instead of raising it
NAME_STENCIL = False   # with NAME_CUT: use a stencil font (no floating islands) instead of bridges


def stencil(letters, bridge=1.4):
    """Letters as a through-cut: the islands inside O, A, R ... stay attached to the plate by two vertical
    bridges (up and down) of `bridge` mm across the stroke."""
    bars = []
    for p in _polys(letters):
        for ring in p.interiors:
            c = Polygon(ring).centroid
            bars.append(LineString([(c.x, p.bounds[1] - 1), (c.x, p.bounds[3] + 1)]).buffer(bridge / 2, cap_style=2))
    return letters.difference(unary_union(bars)) if bars else letters


# ------------------------------------------------------------------ resolve
def resolve(kind, theme, name, ops, silhouette, holes=(), base=BASE, tunnel=None, notes=(), cutouts=None, top=None):
    th = THEMES[theme]
    colors = list(th["heights"])
    gf = th.get("gap_fill")
    if gf and kind in gf.get("pieces", ("tag", "bottle", "pencil", "ruler")):
        # gaps between the artwork colours (narrower than the 0.8 mm print limit) would show the base slab colour: lay an under-layer of the
        # line colour below everything inside the artwork area, so a gap shows that colour (like the dark-base themes) instead of the base colour
        art = unary_union([g for c, g, e in ops if c != th["outline"] and not g.is_empty])
        r = gf.get("close", 1.5)
        under = art.buffer(r, join_style=1).buffer(-r, join_style=1).intersection(silhouette.buffer(-gf.get("edge", 1.5), join_style=1))   # keep the outer rim in the base colour
        if not under.is_empty:
            ops = [(gf["colour"], under, True)] + list(ops)
    ec = th.get("edge_snap")
    if ec and kind in ec.get("pieces", ("tag", "bottle")):
        # the art colour that forms the outer rim stops a hair short of the silhouette edge, leaving an unprintable base-colour line: extend it to the edge
        ycol = unary_union([g for c, g, e in ops if c == ec["colour"] and not g.is_empty])
        strip = silhouette.difference(silhouette.buffer(-ec.get("width", 1.0), join_style=1)).intersection(ycol.buffer(ec.get("width", 1.0), join_style=1))
        if not strip.is_empty:
            ops = [(ec["colour"], strip.union(ycol), False)] + list(ops)
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
    hole_geoms = [Point(cx, cy).buffer(d / 2, 64) for cx, cy, d in holes] + ([cutouts] if cutouts is not None and not cutouts.is_empty else [])
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
    tops = {c: base + (h - BASE) for c, h in th["heights"].items()} if top is None else {c: top for c in th["heights"]}   # top: one flat height for every colour
    return Piece(kind, theme, name, parts, sil.simplify(0.02), base, tops, th["outline"],
                 [tuple(h) for h in holes], tunnel, list(notes))


def make_silhouette(ops, extra=None, close=0.6, min_hole=10.0, spur=0.4):
    g = unary_union([o[1] for o in ops] + ([extra] if extra is not None else []))
    g = g.buffer(close, join_style=1).buffer(-close, join_style=1)
    g = opening(g, spur)                      # no spurs thinner than 2 x spur on the outline (theme 'sil_open', default 0.4)
    polys = []
    for p in _polys(g):
        polys.append(Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= min_hole]))
    return unary_union(polys)


def add_tab(sil, tab_x, hole_d=HOLE_D, wall=3.0):      # wall 3.0 mm: measured on the tested Mariachi bag tag (~3 mm around the hole)
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
    overlap = th.get("tag_overlap", 1.2)       # how far the name ring rises over the bottom of the artwork (mm)
    my = letters.bounds[3] + R - overlap
    ops = [(c, g, False) for c, g in place(m, -cb[0] * ms, my - cb[1] * 0, ms)] + nops
    spur = th.get("sil_open", 0.4)
    sil = make_silhouette(ops, spur=spur)
    jf = th.get("join_fill")
    if jf:                                    # fill the small notches where the artwork's flat bottom meets the (wider) name pill
        closed = sil.buffer(jf, join_style=1).buffer(-jf, join_style=1)
        band = box(-5, my - 6.0, width + 5, my + 4.0)
        extra = closed.difference(sil).intersection(band)
        if not extra.is_empty:
            ops.append(((th.get("edge_snap") or {}).get("colour", th["outline"]), extra, False))
            sil = make_silhouette(ops, spur=spur)
    tab, hole = add_tab(sil, (m["tab_x"] - cb[0]) * ms)
    fil = th.get("tab_fillet")
    if fil:                                   # round the concave corners where the loop meets the outline (no notches)
        joined = unary_union([sil, tab])
        zone = box(hole[0] - 11, hole[1] - 12, hole[0] + 11, hole[1] + 4)
        tab = unary_union([tab, joined.buffer(fil, join_style=1).buffer(-fil, join_style=1).difference(joined).intersection(zone)])
    if th.get("tab_under_art"):               # the art stays visible where the hanging loop overlaps it
        ops.insert(0, (th.get("tab_colour") or th["outline"], tab, False))
    else:
        ops.append((th.get("tab_colour") or th["outline"], tab, False))
    sil = make_silhouette(ops, spur=spur)
    sb = sil.bounds
    ops, sil, holes, _ = normalise(ops, sil, [hole])
    piece = resolve(kind, theme, name, ops, sil, holes, notes=notes)
    if th.get("tab_height"):                   # raise the hanging loop (outline colour only) to this total height: the weak spot of a keychain
        piece.tab = affinity.translate(tab, -sb[0], -sb[1])
        piece.tab_top = th["tab_height"]
        piece.tab_colour = th.get("tab_colour")
    return piece


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
    sil = make_silhouette(ops, extra=capsule, spur=th.get("sil_open", 0.4))
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
    body_col = rc["body"] or th["outline"]      # the body is always a colour region, so ticks and numbers end flush with it
    ops.append((body_col, inner, False))
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
    ops.append((body_col, box(0, num_base - 0.4, W, layout_top).intersection(inner), True))   # keep the 0.5 mm gaps between ticks in the body colour (thinner than the 0.8 mm clean-up)
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
    cut = stencil(affinity.translate(letters, nx, ny)) if NAME_CUT else None
    return resolve("ruler", theme, name, ops, outer, [], notes=notes, cutouts=cut, top=RULER_TOP)


KINDS = {"tag": tag, "pencil": pencil, "ruler": ruler, "bottle": bottle}


def build_pack(theme, name):
    return {k: f(theme, name) for k, f in KINDS.items()}
