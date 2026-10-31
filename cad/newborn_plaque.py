"""Newborn keepsake plaque generator (300x300 mm, multi-colour, standing).

Usage: python newborn_plaque.py plaque/example_ar.json [--out out/plaque]

Reads the baby's data from a JSON file, builds flat colour layers with shapely
(Arabic text is shaped with HarfBuzz so letters join correctly), and writes
one STL per colour plus a PNG preview.
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh
import uharfbuzz as hb
from threemf import write_bambu_3mf
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

SIZE = 300.0
HALF = SIZE / 2
BASE_H = 2.4          # cream base plate
RAISE = 1.2           # raised detail on the base
FRAME_RAISE = 1.8
LIT_BASE_H = 1.2      # thin translucent front plate of the backlit version
TOP = BASE_H + RAISE  # second-level detail (eyes, muzzle) sits on top of level-1 detail
FONT_DIR = Path(__file__).parent / "fonts"   # bundled, so it works on Windows/macOS/Linux
FONTS = {
    "ar": FONT_DIR / "NotoKufiArabic-Bold.ttf",
    "ar_label": FONT_DIR / "NotoKufiArabic-Regular.ttf",
    "en": FONT_DIR / "NotoSans-Bold.ttf",
    "en_label": FONT_DIR / "NotoSans-Regular.ttf",
}
FALLBACK_EN = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")  # only used if a bundled font is missing

# preview colours only -- the real filament is chosen in the slicer
THEMES = {
    "blue":   {"base": "#f5ecd7", "main": "#3e628a", "accent": "#f0c446", "animal": "#c8a078"},
    "green":  {"base": "#f5ecd7", "main": "#5b8a72", "accent": "#f0c446", "animal": "#b9c3cc"},
    "pink":   {"base": "#f8ece4", "main": "#d9808c", "accent": "#f4d28a", "animal": "#f3e6d8"},
    "purple": {"base": "#f5ecd7", "main": "#8e739f", "accent": "#f0c446", "animal": "#e8b8c4"},
    "lit":    {"base": "#ffe9a8", "main": "#2b4666", "accent": "#d9a92e", "animal": "#7a5a3a"},  # simulated glow
}

ARABIC_DIGITS = str.maketrans("0123456789.", "٠١٢٣٤٥٦٧٨٩٫")
LABELS = {
    "ar": {"weight": "الوزن", "length": "الطول", "date": "التاريخ", "time": "الساعة"},
    "en": {"weight": "WEIGHT", "length": "LENGTH", "date": "DATE", "time": "TIME"},
}
UNITS = {"ar": {"weight": "كغم", "length": "سم"}, "en": {"weight": "kg", "length": "cm"}}
AMPM = {"ar": {"AM": "ص", "PM": "م"}, "en": {"AM": "AM", "PM": "PM"}}


# ---------------------------------------------------------------- text ----
class _FlatPen(BasePen):
    def __init__(self, glyph_set, steps=8):
        super().__init__(glyph_set)
        self.contours, self._cur, self.steps = [], None, steps

    def _moveTo(self, p):
        self._cur = [p]

    def _lineTo(self, p):
        self._cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            self._cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                              a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c = (1 - t) ** 2, 2 * t * (1 - t), t * t
            self._cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))

    def _closePath(self):
        if self._cur and len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = None

    _endPath = _closePath


def _signed_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2


class Font:
    def __init__(self, path):
        path = Path(path)
        if not path.exists():
            path = FALLBACK_EN
        self.hb_font = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))
        self.upem = self.hb_font.face.upem
        self.tt = TTFont(str(path))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self._cache = {}

    def glyph(self, gid):
        if gid not in self._cache:
            pen = _FlatPen(self.glyphs)
            self.glyphs[self.order[gid]].draw(pen)
            cs = [c for c in pen.contours if abs(_signed_area(c)) > 1e-6]
            if not cs:
                self._cache[gid] = None
            else:
                outer_sign = math.copysign(1, _signed_area(max(cs, key=lambda c: abs(_signed_area(c)))))
                outers = [Polygon(c).buffer(0) for c in cs if math.copysign(1, _signed_area(c)) == outer_sign]
                holes = [Polygon(c).buffer(0) for c in cs if math.copysign(1, _signed_area(c)) != outer_sign]
                g = unary_union(outers)
                if holes:
                    g = g.difference(unary_union(holes))
                self._cache[gid] = g
        return self._cache[gid]


_fonts = {}


def get_font(key):
    if key not in _fonts:
        _fonts[key] = Font(FONTS[key])
    return _fonts[key]


def shape_run(font, text, size, direction, script):
    """Shape one run. Returns (geometry with baseline at y=0 and left edge at x=0, advance width)."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.direction, buf.script = direction, script
    buf.language = "ar" if script == "Arab" else "en"
    hb.shape(font.hb_font, buf, {"kern": True, "liga": True, "calt": True})
    k = size / font.upem
    x, parts = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = font.glyph(info.codepoint)
        if g is not None:
            parts.append(affinity.translate(g, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    geom = unary_union(parts) if parts else Polygon()
    return affinity.scale(geom, k, k, origin=(0, 0)), x * k


def _subruns(text, size, kind, lang):
    """Split a segment into (text, size, font key, script, direction) runs.
    The Arabic font lacks '/' ':' so those use the Latin font."""
    if lang != "ar":
        return [(text, size, "en", "Latn", "ltr")]
    if kind == "word":
        return [(text, size, "ar", "Arab", "rtl")]
    out, cur, cur_digit = [], "", None
    for ch in text:
        is_digit = ch in "٠١٢٣٤٥٦٧٨٩٫"
        if cur and is_digit != cur_digit:
            out.append((cur, size, "ar" if cur_digit else "en", "Arab" if cur_digit else "Latn", "ltr"))
            cur = ""
        cur, cur_digit = cur + ch, is_digit
    if cur:
        out.append((cur, size, "ar" if cur_digit else "en", "Arab" if cur_digit else "Latn", "ltr"))
    return out


def text_line(segments, lang, rtl, gap=0.18):
    """segments: [(text, size, kind)] in logical order; kind 'num' (always LTR) or 'word'.
    Returns (geometry, width) with left edge x=0, baseline y=0."""
    runs = []
    for text, size, kind in segments:
        sub = [shape_run(get_font(fk), t, sz, d, sc) + (sz,) for t, sz, fk, sc, d in _subruns(text, size, kind, lang)]
        if sub:
            # a 'num' segment is one visual unit: keep its internal LTR order; words keep logical order
            g = unary_union([affinity.translate(gm, sum(a + gap * z for _, a, z in sub[:i]), 0)
                             for i, (gm, a, z) in enumerate(sub)])
            w = sum(a + gap * z for _, a, z in sub) - gap * sub[-1][2]
            runs.append((g, w, size))
    order = runs if not rtl else runs[::-1]  # visual left-to-right order
    placed, width = [], 0.0
    for geom, adv, size in order:
        placed.append(affinity.translate(geom, width, 0))
        width += adv + gap * size * 1.4
    width -= gap * size * 1.4 if runs else 0
    return unary_union(placed), max(width, 0.0)


def put_text(segments, lang, rtl, cx, y, anchor="center", max_width=None):
    geom, w = text_line(segments, lang, rtl)
    s = 1.0
    if max_width and w > max_width:
        s = max_width / w
        geom = affinity.scale(geom, s, s, origin=(0, 0))
        w *= s
    dx = {"center": cx - w / 2, "left": cx, "right": cx - w}[anchor]
    return affinity.translate(geom, dx, y)


# -------------------------------------------------------------- shapes ----
_K = 1.0  # xy scale of the current build (size / 300); used to keep printable line widths


def rw(w):
    """Line width in design units that is still >= 1.2 mm after scaling by _K."""
    return max(w, 1.2 / _K)


def circle(cx, cy, r):
    return Point(cx, cy).buffer(r, 24)


def rrect(cx, cy, w, h, r):
    return box(cx - w / 2 + r, cy - h / 2 + r, cx + w / 2 - r, cy + h / 2 - r).buffer(r, 12)


def ring(geom, width):
    """Outline of width `width` hugging the inside of geom."""
    return geom.difference(geom.buffer(-width, 12))


def star(cx, cy, r, rot=90):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else r * 0.48
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return Polygon(pts).buffer(r * 0.08, 6)


def heart(cx, cy, size):
    pts = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        pts.append((16 * math.sin(t) ** 3,
                    13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
    return affinity.translate(affinity.scale(Polygon(pts), size / 32, size / 32, origin=(0, 0)), cx, cy)


def crescent(cx, cy, r):
    return circle(cx, cy, r).difference(circle(cx + r * 0.45, cy + r * 0.2, r * 0.82))


# --------------------------------------------------------------- icons ----
def icon_scale(s=1):
    body = Polygon([(-13, -12), (13, -12), (9, 9), (-9, 9)]).buffer(2, 8)
    body = body.difference(circle(0, -1, 5.6))
    body = body.union(circle(0, -1, 2.0))
    cap = rrect(0, 13.5, 16, 4.5, 2)
    return affinity.scale(unary_union([body, cap]), s, s, origin=(0, 0))


def icon_ruler(s=1):
    r = rrect(0, 0, 9, 32, 2)
    for i in range(6):
        r = r.difference(box(-4.5, -12 + i * 4.8, -1.2 if i % 2 else -0.4, -11 + i * 4.8))
    return affinity.scale(affinity.rotate(r, 40, origin=(0, 0)), s, s, origin=(0, 0))


def icon_calendar(s=1):
    c = rrect(0, -1, 30, 26, 4)
    c = c.difference(rrect(0, -4, 24, 14, 1.5))
    c = c.union(box(-9, 9, -6, 16)).union(box(6, 9, 9, 16))
    for dx in (-6, 0, 6):
        c = c.union(box(dx - 2, -7, dx + 2, -3))
    return affinity.scale(c, s, s, origin=(0, 0))


def icon_clock(s=1):
    c = ring(circle(0, 0, 15), 3.2)
    c = c.union(box(-1.2, -0.5, 1.2, 9)).union(box(-0.5, -1.2, 7, 1.2)).union(circle(0, 0, 2.2))
    return affinity.scale(c, s, s, origin=(0, 0))


ICONS = {"weight": icon_scale, "length": icon_ruler, "date": icon_calendar, "time": icon_clock}


# -------------------------------------------------------------- animals ----
def animal_bear(cx, cy, cover):
    """Returns dict colour-role -> [(geometry, z0, z1)]. `cover` is the cloud in front of the bear."""
    head = circle(cx, cy, 20)
    ears = unary_union([circle(cx - 15.5, cy + 16, 8), circle(cx + 15.5, cy + 16, 8)])
    paws = unary_union([circle(cx - 13, cy - 14, 6), circle(cx + 13, cy - 14, 6)])
    inner_ears = unary_union([circle(cx - 15.5, cy + 16, 4), circle(cx + 15.5, cy + 16, 4)])
    muzzle = affinity.scale(circle(cx, cy - 6, 9.5), 1.15, 0.85, origin=(cx, cy - 6))
    eyes = unary_union([ring(circle(cx - 8, cy + 3.5, 3.8), rw(1.4)).intersection(box(cx - 12, cy - 1, cx - 3, cy + 4)),
                        ring(circle(cx + 8, cy + 3.5, 3.8), rw(1.4)).intersection(box(cx + 3, cy - 1, cx + 12, cy + 4))])
    nose = affinity.scale(circle(cx, cy - 3.5, 3), 1.15, 0.8, origin=(cx, cy - 3.5))
    mouth = box(cx - 0.55, cy - 7.5, cx + 0.55, cy - 3.5)
    body = unary_union([head, ears]).difference(cover)
    return {
        "animal": [(unary_union([body, paws]), BASE_H, TOP)],
        "base": [(unary_union([inner_ears, muzzle]).difference(cover), TOP, TOP + 0.6)],
        "main": [(unary_union([eyes, nose, mouth]).difference(cover), TOP, TOP + 0.6)],
        "_paws": paws,
    }


ANIMALS = {"bear": animal_bear}


# --------------------------------------------------------------- layout ----
def build(data):
    global _K, BASE_H, TOP
    size = float(data.get("size", 300))
    _K = k = size / SIZE
    lit = bool(data.get("lit"))
    BASE_H = LIT_BASE_H if lit else 2.4
    TOP = BASE_H + RAISE
    lang = data.get("lang", "ar")
    rtl = lang == "ar"
    layers = {"base": [], "main": [], "accent": [], "animal": []}

    def add(role, geom, z0=BASE_H, z1=TOP):
        if geom is not None and not geom.is_empty:
            layers[role].append((geom, z0, z1))

    plate = rrect(0, 0, SIZE, SIZE, 30)
    add("base", plate, 0, BASE_H)
    add("main", ring(plate, 12), BASE_H, BASE_H + FRAME_RAISE)

    # name banner (cloud) + animal peeking over it
    banner = unary_union([rrect(0, 58, 196, 38, 19), circle(0, 79, 17), circle(-38, 77, 13), circle(38, 77, 13),
                          circle(-72, 72, 10), circle(72, 72, 10)])
    animal = ANIMALS[data.get("animal", "bear")](0, 111, banner)
    paws = animal.pop("_paws")
    for role, items in animal.items():
        for g, z0, z1 in items:
            add(role, g, z0, z1)
    add("base", banner.difference(paws), BASE_H, TOP)  # cream fill hides animal parts behind the cloud
    add("main", ring(banner, rw(1.4)).difference(paws.buffer(1.0)), BASE_H, TOP)
    name = data["name"]
    add("main", put_text([(name, 25 if lang == "ar" else 21, "word")], lang, rtl, 0, 49.5, max_width=160), BASE_H, TOP + 0.4)

    # sky decoration
    add("accent", crescent(-98, 110, 19), BASE_H, TOP)
    for (x, y, r) in [(-70, 122, 8), (96, 112, 11), (74, 126, 6.5), (112, 88, 6)]:
        add("accent", star(x, y, r), BASE_H, TOP)
    add("main", star(-116, 70, 6), BASE_H, TOP)

    # info badges
    weight = data["weight"]
    length = data["length"]
    time = data["time"]
    ampm = AMPM[lang][data.get("ampm", "AM").upper()]
    date = data["date"]
    conv = (lambda s: s.translate(ARABIC_DIGITS)) if lang == "ar" else (lambda s: s)
    values = {
        "weight": [(conv(weight), 17, "num"), (UNITS[lang]["weight"], 9, "word")],
        "length": [(conv(length), 17, "num"), (UNITS[lang]["length"], 9, "word")],
        "date": [(conv(date), 14.5, "num")],
        "time": [(conv(time), 17, "num"), (ampm, 9, "word")],
    }
    order = ["weight", "length", "date", "time"]
    slots = [(66, 14), (-66, 14), (66, -34), (-66, -34)] if rtl else [(-66, 14), (66, 14), (-66, -34), (66, -34)]
    for key, (bx, by) in zip(order, slots):
        add("main", ring(rrect(bx, by, 124, 40, 10), rw(1.2)), BASE_H, TOP)
        add("main", affinity.translate(ICONS[key](1.0), bx - 39, by), BASE_H, TOP)
        tx_right, tx_left = bx + 55, bx - 19
        label_font = "ar_label" if rtl else "en_label"
        if k >= 0.6:  # labels are too small to print on the S size
            lab, _ = text_line([(LABELS[lang][key], 7.5, "word")], lang, rtl)
            lw = max(lab.bounds[2], 1)
            scale = min(1, 70 / lw)
            lab = affinity.scale(lab, scale, scale, origin=(0, 0))
            x0 = (tx_right - lw * scale) if rtl else tx_left
            add("main", affinity.translate(lab, x0, by + 6.5), BASE_H, TOP)
        vy = by - 13 if k >= 0.6 else by - 7
        g = put_text(values[key], lang, rtl, tx_right if rtl else tx_left, vy, "right" if rtl else "left", 72)
        add("main", g, BASE_H, TOP)

    # footprint area: raised rim, flat inside for a sticker / ink print
    pad = rrect(0, -97, 124, 62, 12)
    add("main", ring(pad, rw(1.2)), BASE_H, TOP)
    add("accent", heart(0, -97, 12), BASE_H, TOP)
    if lit:
        # backlit: coloured parts run through the thin translucent base (so they block the light),
        # the base keeps holes where they sit
        inlay = lambda z0: z0 <= BASE_H + 1e-6
        foot = unary_union([g for role in ("main", "accent", "animal") for g, z0, _ in layers[role] if inlay(z0)])
        layers["base"] = [(g.difference(foot) if z0 == 0 else g, z0, z1) for g, z0, z1 in layers["base"]]
        for role in ("main", "accent", "animal"):
            layers[role] = [(g, 0 if inlay(z0) else z0, z1) for g, z0, z1 in layers[role]]
    # parts must not share volume: a later colour slot wins where z-ranges overlap
    order = ["base", "main", "accent", "animal"]
    for i, role in enumerate(order):
        resolved = []
        for g, z0, z1 in layers[role]:
            for later in order[i + 1:]:
                for g2, a0, a1 in layers[later]:
                    if a0 < z1 and a1 > z0:
                        g = g.difference(g2)
            resolved.append((g, z0, z1))
        layers[role] = resolved
    return {role: [(affinity.scale(g, k, k, origin=(0, 0)), z0, z1) for g, z0, z1 in its]
            for role, its in layers.items()}


# ------------------------------------------------------------ lit box ----
BOX_DEPTH, BOX_WALL, BOX_BACK = 25.0, 2.6, 1.2


def make_lit_box(size):
    """Shallow white tray behind the backlit plate: LED strip stuck on its back panel, USB-C slot in the
    bottom wall, 12 small ledges hold the plate whose front face ends flush with the rim.
    Printed back panel down. Returns (mesh, info)."""
    k = size / SIZE
    half = size / 2 + 0.2                     # plate half-size + clearance
    r = 30 * k + 0.2
    outer = rrect(0, 0, 2 * (half + BOX_WALL), 2 * (half + BOX_WALL), r + BOX_WALL)
    ring = outer.difference(rrect(0, 0, 2 * half, 2 * half, r))
    plate_t = LIT_BASE_H + FRAME_RAISE
    ledge_top = BOX_DEPTH - plate_t
    slot = box(-5, -half - BOX_WALL - 1, 5, -half + 1)
    z0, z1 = 10.0, 14.5                       # USB-C slot height band
    tabs = unary_union([t for off in (-0.33 * size, 0, 0.33 * size) for t in (
        box(off - 15, -half - 0.1, off + 15, -half + 2.5), box(off - 15, half - 2.5, off + 15, half + 0.1),
        box(-half - 0.1, off - 15, -half + 2.5, off + 15), box(half - 2.5, off - 15, half + 0.1, off + 15))])
    cuts = sorted({0, BOX_BACK, z0, z1, ledge_top - 2.0, ledge_top, BOX_DEPTH})
    meshes = []
    for a, b in zip(cuts, cuts[1:]):       # one extrusion per slab, so no part overlaps another
        mid = (a + b) / 2
        g = outer if mid < BOX_BACK else (ring.difference(slot) if z0 < mid < z1 else ring)
        if ledge_top - 2.0 < mid < ledge_top:
            g = g.union(tabs)
        meshes += extrude(g, a, b)
    mesh = trimesh.util.concatenate(meshes)
    return mesh, {"outer": 2 * (half + BOX_WALL), "depth": BOX_DEPTH}


# ----------------------------------------------------------------- stand ----
TILT = 12.0       # degrees the plaque leans back
SLOT_DEPTH = 14.0
PLATE_EDGE = BASE_H + FRAME_RAISE   # plaque thickness at the frame
CLEARANCE = 0.6   # total slot slack


def make_foot(size):
    """One of two feet: a block with a tilted slot the plaque's bottom edge slides into.
    Returns (mesh, info). Print two. Profile is in YZ (Y = depth, Z up), extruded along X."""
    k = size / SIZE
    depth, width, height = 40 + 30 * k, 50 + 20 * k, SLOT_DEPTH + 8
    t = math.radians(TILT)
    w = PLATE_EDGE + CLEARANCE
    y0 = 12 + 8 * k   # slot top-centre, measured from the front of the foot
    half = w / (2 * math.cos(t))
    shift = SLOT_DEPTH * math.tan(t)
    slot = Polygon([(y0 - half, height), (y0 + half, height),
                    (y0 + half - shift, height - SLOT_DEPTH), (y0 - half - shift, height - SLOT_DEPTH)])
    profile = box(0, 0, depth, height).difference(slot)
    m = trimesh.creation.extrude_polygon(profile, width)  # profile x->Y (depth), y->Z (up), extrusion z->X (width)
    m.apply_transform([[0, 0, 1, -width / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    # stability: plaque centre of mass sits (size/2)*sin(tilt) behind the slot's bottom front edge
    com_back = size / 2 * math.sin(t)
    margin = depth - (y0 - shift) - com_back
    return m, {"depth": depth, "width": width, "height": height, "x": 0.27 * size, "margin": margin}


OPEN = 45.0       # degrees the easel leg opens from the plaque's back


def make_easel(size):
    """Folding easel leg like a photo frame: a bracket glued to the back (two ears) and a
    leg that pivots on an M3 bolt, folds flat and stops at OPEN degrees.
    Both parts are printed on their side (profile on the bed, hole vertical).
    Returns (bracket_mesh, leg_mesh, info, world polygons for the side view)."""
    k = size / SIZE
    t, th = math.radians(TILT), math.radians(OPEN)
    beta = th - t                       # leg angle from vertical
    vp, pad_t, bar, hole, boss = 9.0, 3.0, 4.0, 1.75, 5.0
    w_leg, ear, slack = 14 + 10 * k, 4.0, 0.6
    pad_l, pad_w = 36 * max(k, 0.7), w_leg + 2 * (slack + ear) + 8
    s = 0.62 * size                     # pivot line, measured up the plaque from its bottom edge
    q = (s * math.sin(t), s * math.cos(t))          # point on the back surface (world y, z)
    vx = (math.cos(t), -math.sin(t))                # out of the back
    ux = (-math.sin(t), -math.cos(t))               # down the plaque
    pivot = (q[0] + vp * vx[0], q[1] + vp * vx[1])
    tail = (vp - pad_t - bar / 2 * math.cos(th)) / math.sin(th)   # tail touches the pad at OPEN degrees

    def a_end(b):                       # leg end cut flat on the table
        return (pivot[1] + b * math.sin(beta)) / math.cos(beta)

    leg2d = Polygon([(-tail, -bar / 2), (a_end(-bar / 2), -bar / 2), (a_end(bar / 2), bar / 2), (-tail, bar / 2)])
    leg2d = leg2d.union(circle(0, 0, boss)).difference(circle(0, 0, hole))
    leg = trimesh.creation.extrude_polygon(leg2d, w_leg)

    pad2d = box(-pad_l / 2, 0, pad_l / 2, pad_t)
    ear2d = circle(0, vp, 6).union(box(-6, pad_t - 0.1, 6, vp)).difference(circle(0, vp, hole))
    zc = pad_w / 2
    parts = [trimesh.creation.extrude_polygon(pad2d, pad_w)]
    for z0 in (zc - w_leg / 2 - slack - ear, zc + w_leg / 2 + slack):
        e = trimesh.creation.extrude_polygon(ear2d, ear)
        e.apply_translation([0, 0, z0])
        parts.append(e)
    bracket = trimesh.util.concatenate(parts)

    length = a_end(0)
    foot_y = pivot[0] + length * math.sin(beta)
    com_y = size / 2 * math.sin(t)

    def world_uv(u, v):                 # (u,v) measured from q -> world (y,z)
        return (q[0] + u * ux[0] + v * vx[0], q[1] + u * ux[1] + v * vx[1])

    def leg_world(g):
        return Polygon([world_uv(a * math.cos(th) - b * math.sin(th), vp + a * math.sin(th) + b * math.cos(th))
                        for a, b in g.exterior.coords])

    world = {
        "plate": Polygon([world_uv(u, v) for u, v in [(s, 0), (s, -PLATE_EDGE), (-(size - s), -PLATE_EDGE), (-(size - s), 0)]]),
        "bracket": unary_union([Polygon([world_uv(u, v) for u, v in g.exterior.coords]) for g in (pad2d, ear2d)]),
        "leg": leg_world(leg2d),
    }
    info = {"length": length, "width": w_leg, "pad": (pad_l, pad_w), "pivot_from_bottom": s,
            "foot_y": foot_y, "margin": foot_y - com_y, "tail": tail}
    return bracket, leg, info, world


CLIP_OPEN = 30.0  # leg opens less than the glued easel so the folded leg barely overhangs the bottom edge
CLIP_PIVOT = 0.75  # pivot height as a fraction of the plaque, measured from the bottom edge


def make_clip_stand(size):
    """Side clip + folding leg. The C-shaped clip snaps onto the plaque's right edge (over the 12 mm
    frame band, 4.2 mm thick); two ears carry an M3 bolt; the leg folds flat along the back and stops
    at CLIP_OPEN degrees. Clip is printed with its C profile on the bed; the leg lies flat.
    Returns (clip_mesh, leg_mesh, info, world polygons for the side view)."""
    k = size / SIZE
    t, th = math.radians(TILT), math.radians(CLIP_OPEN)
    beta = th - t
    vp, jaw, bar, hole, boss = 8.0, 3.0, 3.5, 1.75, 4.0
    w_leg, ear, slack = 10.0, 3.0, 0.6
    gap = PLATE_EDGE + 0.3              # slot between the jaws
    front_t, clip_len = 1.6, 30.0
    xc = -4.0                           # leg centre across the band (edge at x=0, plate interior x<0)
    s = CLIP_PIVOT * size
    q = (s * math.sin(t), s * math.cos(t))
    vx = (math.cos(t), -math.sin(t))
    ux = (-math.sin(t), -math.cos(t))
    pivot = (q[0] + vp * vx[0], q[1] + vp * vx[1])
    tail = (vp - jaw - bar / 2 * math.cos(th)) / math.sin(th)

    def a_end(b):
        return (pivot[1] + b * math.sin(beta)) / math.cos(beta)

    leg2d = Polygon([(-tail, -bar / 2), (a_end(-bar / 2), -bar / 2), (a_end(bar / 2), bar / 2), (-tail, bar / 2)])
    leg2d = leg2d.union(circle(0, 0, boss)).difference(circle(0, 0, hole))
    leg = trimesh.creation.extrude_polygon(leg2d, w_leg)

    # clip, in (x across the plaque, y along the edge, v out of the back); built then permuted to print frame
    xmax = xc + w_leg / 2 + slack + ear
    profile = unary_union([
        box(-13, 0, xmax, jaw),                       # back jaw (covers the whole 12 mm band)
        box(-5, -gap - front_t, xmax, -gap),          # front lip
        box(0, -gap - front_t, xmax, jaw),            # spine
        box(-10.5, -0.25, -8.5, 0), box(-4, -gap, -2, -gap + 0.25)])  # grip ridges
    body = trimesh.creation.extrude_polygon(profile, clip_len)       # (x, v) extruded along +z' = y
    body.apply_translation([0, 0, -clip_len / 2])
    ear2d = circle(0, vp, 4.5).union(box(-4.5, jaw - 0.1, 4.5, vp)).difference(circle(0, vp, hole))
    parts = [body]
    for x0 in (xc - w_leg / 2 - slack - ear, xc + w_leg / 2 + slack):
        e = trimesh.creation.extrude_polygon(ear2d, ear)             # (y, v) extruded along z' = x
        e.apply_transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
        parts.append(e)
    # body is (X=x, Y=v, Z=y); bring the ears into the same frame: ears are (X=x, Y=v, Z=y)
    for e in parts[1:]:
        e.apply_transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
        e.invert()
    clip = trimesh.util.concatenate(parts)
    clip.apply_translation([-clip.bounds[0][0], -clip.bounds[0][1], -clip.bounds[0][2]])

    length = a_end(0)
    foot_y = pivot[0] + length * math.sin(beta)
    com_y = size / 2 * math.sin(t)

    def world_uv(u, v):
        return (q[0] + u * ux[0] + v * vx[0], q[1] + u * ux[1] + v * vx[1])

    def leg_world(g):
        return Polygon([world_uv(a * math.cos(th) - b * math.sin(th), vp + a * math.sin(th) + b * math.cos(th))
                        for a, b in g.exterior.coords])

    world = {
        "plate": Polygon([world_uv(u, v) for u, v in [(s, 0), (s, -PLATE_EDGE), (-(size - s), -PLATE_EDGE), (-(size - s), 0)]]),
        "bracket": unary_union([Polygon([world_uv(u, v) for u, v in g.exterior.coords])
                                for g in (box(-clip_len / 2, -gap - front_t, clip_len / 2, jaw), ear2d)]),
        "leg": leg_world(leg2d),
    }
    info = {"length": length, "width": w_leg, "clip": (clip_len, xmax + 13, jaw + gap + front_t),
            "pivot_from_bottom": s, "foot_y": foot_y, "margin": foot_y - com_y,
            "overhang": length + tail * 0 - s, "xc": xc, "tail": tail}
    return clip, leg, info, world


def easel_view(world, path, size):
    fig, ax = plt.subplots(figsize=(7, 7), dpi=100)
    for name, fc in (("plate", "#3e628a"), ("bracket", "#c8a078"), ("leg", "#d9808c")):
        g = world[name]
        ax.fill(*g.exterior.xy, fc=fc, ec="#222", lw=0.6)
    ax.axhline(0, color="#555", lw=1)
    ax.set_aspect("equal")
    ax.set_xlabel("mm (front -> back)")
    ax.set_title("side view: easel open")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- output ----
try:  # well-shaped triangles with interior points (viewers smooth normals across big triangles otherwise)
    import triangle  # noqa: F401
    TRI_KW = {"engine": "triangle", "triangle_args": "pa40"}
except ImportError:  # falls back to ear clipping: valid for printing, but long thin triangles
    TRI_KW = {}


def extrude(geom, z0, z1):
    polys = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    meshes = []
    for p in polys:
        if p.is_empty or p.area < 0.05:
            continue
        poly = p.simplify(0.02)
        try:
            m = trimesh.creation.extrude_polygon(poly, z1 - z0, **TRI_KW)
        except Exception:
            # near-tangent edges (e.g. cloud vs paw) can defeat the mesher: round off 0.03 mm slivers and retry
            clean = poly.buffer(-0.03).buffer(0.06).buffer(-0.03).simplify(0.02)
            try:
                m = trimesh.creation.extrude_polygon(clean, z1 - z0, **TRI_KW)
            except Exception:  # last resort: ear clipping always works
                m = trimesh.creation.extrude_polygon(poly, z1 - z0)
        m.apply_translation([0, 0, z0])
        meshes.append(m)
    return meshes


def to_mesh(items):
    by_z = {}
    for g, z0, z1 in items:
        by_z.setdefault((z0, z1), []).append(g)
    meshes = []
    for (z0, z1), gs in by_z.items():
        meshes += extrude(unary_union(gs), z0, z1)
    return trimesh.util.concatenate(meshes) if meshes else None


def preview(layers, theme, path, half=HALF):
    fig, ax = plt.subplots(figsize=(9, 9), dpi=110)
    levels = sorted({(z0, role) for role, its in layers.items() for _, z0, _ in its})
    for z0, role in sorted(levels):
        for g, a, _ in layers[role]:
            if a != z0:
                continue
            for p in (g.geoms if hasattr(g, "geoms") else [g]):
                if p.is_empty:
                    continue
                verts, codes = [], []
                for r in [p.exterior, *p.interiors]:
                    c = list(r.coords)
                    verts += c
                    codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
                ax.add_patch(PathPatch(MPath(verts, codes), fc=THEMES[theme][role], ec="none"))
    ax.set_xlim(-half - 5, half + 5)
    ax.set_ylim(-half - 5, half + 5)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, facecolor="#dddddd", bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--out", default="out/plaque")
    args = ap.parse_args()
    data = json.load(open(args.data, encoding="utf-8"))
    layers = build(data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    size = int(data.get("size", 300))
    stem = f"{Path(args.data).stem}_{size}"
    theme = data.get("theme", "blue")
    if data.get("lit"):
        stem += "_lit"
        theme = "lit"
    parts = []
    for slot, role in enumerate(("base", "main", "accent", "animal"), start=1):
        m = to_mesh(layers[role])
        if m is not None:
            m.export(out / f"{stem}_{role}.stl")
            print(f"{role}: {len(m.faces)} faces, volume {m.volume:.0f} mm^3")
            parts.append((role, m, slot))
    write_bambu_3mf(out / f"{stem}.3mf", parts, center=(162.5, 160.0), name=stem,
                    project_settings=(Path(__file__).parent / "config" / "bambu_project_settings.config").read_bytes())
    print("wrote", out / f"{stem}.3mf")
    preview(layers, theme, out / f"{stem}.png", size / 2)
    if data.get("lit"):
        box_mesh, info = make_lit_box(size)
        box_mesh.export(out / f"lit_box_{size}.stl")
        print(f"lit box: {info['outer']:.0f}x{info['outer']:.0f}x{info['depth']:.0f} mm; LED strip on its back panel, USB-C slot in the bottom wall")
    elif data.get("stand", "feet") == "clip":
        clip, leg, info, world = make_clip_stand(size)
        clip.export(out / f"clip_{size}.stl")
        leg.export(out / f"clip_leg_{size}.stl")
        easel_view(world, out / f"clip_side_{size}.png", size)
        print(f"clip stand: clip {info['clip'][0]:.0f}x{info['clip'][1]:.0f}x{info['clip'][2]:.0f} mm on the right edge, "
              f"pivot {info['pivot_from_bottom']:.0f} mm from the bottom; leg {info['length']:.0f}x{info['width']:.0f} mm "
              f"(folded it overhangs the bottom edge by {info['overhang']:.0f} mm); foot {info['foot_y']:.0f} mm behind, "
              f"stability margin {info['margin']:.0f} mm; needs an M3 bolt + nut")
    elif data.get("stand", "feet") == "feet":
        foot, info = make_foot(size)
        foot.export(out / f"stand_foot_{size}.stl")
        print(f"stand foot x2: {info['width']:.0f}x{info['depth']:.0f}x{info['height']:.0f} mm, "
              f"place at x=+/-{info['x']:.0f} mm, stability margin {info['margin']:.0f} mm")
    else:
        bracket, leg, info, world = make_easel(size)
        bracket.export(out / f"easel_bracket_{size}.stl")
        leg.export(out / f"easel_leg_{size}.stl")
        easel_view(world, out / f"easel_side_{size}.png", size)
        print(f"easel: leg {info['length']:.0f}x{info['width']:.0f} mm, bracket pad {info['pad'][0]:.0f}x{info['pad'][1]:.0f} mm "
              f"glued with pivot {info['pivot_from_bottom']:.0f} mm from the bottom edge; "
              f"foot {info['foot_y']:.0f} mm behind the plaque, stability margin {info['margin']:.0f} mm")
    print("wrote", out / f"{stem}.png")


if __name__ == "__main__":
    main()
