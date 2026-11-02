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
import numpy as np
import shapely

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage as ndi
import trimesh
import uharfbuzz as hb
from threemf import build_project_settings, write_bambu_3mf
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

SIZE = 300.0
HALF = SIZE / 2
BASE_H = 2.4          # cream base plate
RAISE = 1.2           # raised detail on the base
FRAME_RAISE = 1.8
CAP_OVERLAP = 0.4     # mm: each part rests on this much of base around its (smaller) opening
TOWER_LIMIT = 305.0   # mm: right-most x a prime tower can reach on the left nozzle (measured with the CLI)
LIT_BASE_H = 1.2      # thin translucent front plate of the backlit version
TOP = BASE_H + RAISE  # second-level detail (eyes, muzzle) sits on top of level-1 detail
FONT_DIR = Path(__file__).parent / "fonts"   # bundled, so it works on Windows/macOS/Linux
FONTS = {
    "ar": FONT_DIR / "NotoKufiArabic-Bold.ttf",
    "ar_label": FONT_DIR / "NotoKufiArabic-Regular.ttf",
    "ar_name": FONT_DIR / "BalooBhaijaan2-ExtraBold.ttf",   # rounded heavy face used for the child's name (kind "name")
    "en": FONT_DIR / "NotoSans-Bold.ttf",
    "en_label": FONT_DIR / "NotoSans-Regular.ttf",
}
FALLBACK_EN = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")  # only used if a bundled font is missing

# preview colours only -- the real filament is chosen in the slicer
# Slot colours (base, main, accent, animal) = what the stock filaments look like; used for the preview and as the
# filament colours inside the 3MF. THEME_FILAMENTS lists the real stock spools per slot (price type in the stock sheet).
THEMES = {
    "blue":      {"base": "#f2f0ea", "main": "#3e628a", "accent": "#f0c446", "animal": "#8a5a36"},
    "pink":      {"base": "#f2f0ea", "main": "#d9808c", "accent": "#f4c95d", "animal": "#8a5a36"},
    "green":     {"base": "#f2f0ea", "main": "#5b8a72", "accent": "#e58a2b", "animal": "#8a5a36"},
    "purple":    {"base": "#f2f0ea", "main": "#8e739f", "accent": "#e8c24a", "animal": "#9a6a3a"},
    "sky":       {"base": "#f2f0ea", "main": "#3aa8c8", "accent": "#f0c446", "animal": "#8c96a0"},
    "gold_dark": {"base": "#26262a", "main": "#d4af37", "accent": "#c98b7b", "animal": "#a0703a"},
    "boy":       {"base": "#f2f0ea", "main": "#3e628a", "accent": "#f0c446", "animal": "#8a5a36"},
    "girl":      {"base": "#f2f0ea", "main": "#d9808c", "accent": "#f4c95d", "animal": "#8a5a36"},
    "night":     {"base": "#1f3a6e", "main": "#f2f0ea", "accent": "#f0c446", "animal": "#e8b48c"},
    "train":     {"base": "#2a4f9e", "main": "#f2f2f0", "accent": "#f2c230", "animal": "#c9a06a"},
    "horse":     {"base": "#1f3a6e", "main": "#f6ecd2", "accent": "#2d78d7", "animal": "#f2c230"},
    "train_lit": {"base": "#6fa8dc", "main": "#fff3d6", "accent": "#ffd23a", "animal": "#ff9a2e"},   # simulated: sky-blue opaque + glowing parts
    "glow":      {"base": "#f5ecd7", "main": "#2f6bff", "accent": "#ffd23a", "animal": "#ff8a1f"},  # simulated glow
    "lit":       {"base": "#ffe9a8", "main": "#2b4666", "accent": "#d9a92e", "animal": "#7a5a3a"},  # simulated glow
}
THEME_FILAMENTS = {
    "blue":      ["PLA+ White", "PLA+ Blue", "PLA+ Yellow", "Walnut PLA"],
    "pink":      ["PLA+ White", "PLA+ Pink", "PLA+ Yellow", "Walnut PLA"],
    "green":     ["PLA+ White", "PLA+ Green", "PLA+ Orange", "Walnut PLA"],
    "purple":    ["PLA+ White", "PLA+ Purple", "Silk PLA Gold", "Silk PLA Bronze"],
    "sky":       ["PLA+ White", "PLA+ Cyan", "PLA+ Yellow", "PLA+ Grey"],
    "gold_dark": ["PLA+ Black", "Silk PLA Gold", "Silk PLA Rose Gold", "Silk PLA Bronze"],
    "night":     ["PLA+ Blue", "PLA+ White", "PLA+ Yellow", "Wood PLA"],
    "horse":     ["PLA+ Blue", "PLA+ White", "PLA+ Cyan", "PLA+ Yellow"],
    "train_lit": ["PETG Blue", "AD-PETG Translucent White", "AD-PETG Translucent Yellow", "AD-PETG Translucent Orange-Red"],
    "train":     ["PLA+ Blue", "PLA+ White", "PLA+ Yellow", "Wood PLA"],
}
THEME_FILAMENTS["boy"], THEME_FILAMENTS["girl"] = THEME_FILAMENTS["blue"], THEME_FILAMENTS["pink"]

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
    if kind == "name":
        return [(text, size, "ar_name", "Arab", "rtl")]
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


def only_polygons(g):
    """Drop stray lines/points that boolean operations can leave in a geometry collection."""
    polys = []
    def walk(x):
        if x.geom_type == "Polygon":
            polys.append(x)
        elif hasattr(x, "geoms"):
            for y in x.geoms:
                walk(y)
    walk(g)
    return unary_union(polys)


def add_ribs(poly, k, max_span=20.0, pitch=14.0, width=1.4):
    """Leave thin base ribs across an opening that is too wide to bridge cleanly (spans in final mm)."""
    if poly.area < 1 or 2 * shapely.maximum_inscribed_circle(poly, 0.05).length * k <= max_span:
        return poly
    minx, miny, maxx, maxy = poly.bounds
    p, w, ribs = pitch / k, width / k, []
    x = minx + p / 2
    while x < maxx:
        ribs.append(box(x - w / 2, miny - 1, x + w / 2, maxy + 1))
        x += p
    y = miny + p / 2
    while y < maxy:
        ribs.append(box(minx - 1, y - w / 2, maxx + 1, y + w / 2))
        y += p
    return poly.difference(unary_union(ribs))


def fix(g):
    """A valid polygon geometry (scaling and boolean operations can leave self-touching rings)."""
    return g if g.is_valid else only_polygons(shapely.make_valid(g))


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



def animal_baby(cx, cy, cover, girl=False):
    """A sleeping baby's head tucked in a blanket, peeking over the cloud. The face is the base colour
    (outline + features in the main colour), hair = animal colour, blanket = accent colour, girl's bow = main."""
    head = circle(cx, cy, 19)
    outline = ring(head, rw(1.6))
    ears = unary_union([ring(circle(cx + sx * 19.5, cy - 1, 4.2), rw(1.4)).difference(head) for sx in (-1, 1)])
    def lower_arc(x, y, r, w):
        return ring(circle(x, y, r), rw(w)).intersection(box(x - r - 1, y - r - 1, x + r + 1, y))
    eyes = unary_union([lower_arc(cx - 7, cy + 3, 3.6, 1.3), lower_arc(cx + 7, cy + 3, 3.6, 1.3)])
    nose = circle(cx, cy - 2.5, 1.2)
    mouth = lower_arc(cx, cy - 5.0, 2.8, 1.2)
    hair = unary_union([circle(cx, cy + 19.2, 3.4), circle(cx - 3.8, cy + 18.6, 2.7), circle(cx + 3.8, cy + 18.6, 2.7)])
    blanket = rrect(cx, 99.5, 46, 15, 7.5)
    main = unary_union([outline, ears, eyes, nose, mouth])
    if girl:
        bx, by = cx + 11, cy + 17
        bow = unary_union([Polygon([(bx, by), (bx + 8.5, by + 6.5), (bx + 8.5, by - 6.5)]),
                           Polygon([(bx, by), (bx - 8.5, by + 6.5), (bx - 8.5, by - 6.5)]), circle(bx, by, 2.4)])
        main = unary_union([main, bow])
    return {
        "main": [(main.difference(cover).difference(blanket), BASE_H, TOP)],
        "animal": [(hair.difference(cover), BASE_H, TOP)],
        "accent": [(blanket.difference(cover), BASE_H, TOP)],
        "_paws": Polygon(),
    }


ANIMALS = {"bear": animal_bear, "baby_boy": animal_baby, "baby_girl": lambda cx, cy, cover: animal_baby(cx, cy, cover, True)}




# ------------------------------------------------------- "night" layout ----
NIGHT_CENTER = (0.0, 10.0)
NIGHT_R = 140.0


def night_outline():
    """Round plaque (r 140) standing on a flat stadium-shaped pedestal; 300 x 300 overall, flat bottom edge."""
    shape = unary_union([circle(*NIGHT_CENTER, NIGHT_R), rrect(0, -128, 300, 44, 22)])
    return shape.buffer(16, 24).buffer(-16, 24)    # rounds the notch where the circle meets the pedestal


def tag_shape(cx, cy, w=33, h=50):
    """Hanging tag: rounded rectangle with a small peak on top where the string ties on."""
    peak = Polygon([(cx - 7, cy + h / 2 - 3), (cx, cy + h / 2 + 5), (cx + 7, cy + h / 2 - 3)]).buffer(1.5, 6)
    return unary_union([rrect(cx, cy, w, h, 11), peak])


def sleeping_baby(cx, cy):
    """Baby asleep in a night cap under a starry blanket, resting on the cloud row.
    Returns dict role -> [(geom, z0, z1)] (the blanket is drawn first, the head wins where they overlap)."""
    head = circle(cx, cy, 16)
    cap = unary_union([head.intersection(box(cx - 20, cy + 5, cx + 20, cy + 20)),
                       Polygon([(cx - 15, cy + 9), (cx + 14, cy + 9), (cx + 10, cy + 24), (cx - 4, cy + 30)]).buffer(1.5, 6)])
    cap_dots = unary_union([star(cx - 6, cy + 15, 2.6), star(cx + 5, cy + 20, 2.2)])
    pompom = circle(cx - 4, cy + 31, 4.2)
    blanket = rrect(cx + 44, cy - 3, 72, 32, 13)
    b_dots = unary_union([star(cx + 28 + 17 * i, cy - 3 + (4 if i % 2 else -4), 3.4) for i in range(3)])
    def lower_arc(x, y, r, w):
        return ring(circle(x, y, r), rw(w)).intersection(box(x - r - 1, y - r - 1, x + r + 1, y))
    eyes = unary_union([lower_arc(cx - 6.2, cy - 0.5, 3.2, 1.2), lower_arc(cx + 6.2, cy - 0.5, 3.2, 1.2)])
    face = unary_union([eyes, circle(cx, cy - 4, 1.1), lower_arc(cx, cy - 6.5, 2.6, 1.1)])
    hug_star = star(cx + 22, cy - 3, 8.5)
    skin = head.difference(cap)
    grow = lambda g: affinity.scale(g, 1.15, 1.15, origin=(cx, cy))
    return {
        "main": [(grow(ring(blanket, rw(1.2)).difference(head)), BASE_H, TOP),
                 (grow(b_dots.difference(head)), BASE_H, TOP),
                 (grow(cap.difference(cap_dots)), BASE_H, TOP)],
        "accent": [(grow(pompom), BASE_H, TOP), (grow(hug_star), TOP, TOP + 0.6)],
        "animal": [(grow(skin), BASE_H, TOP)],
        "base": [(grow(blanket.difference(head)), BASE_H, TOP), (grow(face.intersection(head)), TOP, TOP + 0.6)],
    }


def layout_night(data, add, layers, k, lang, rtl):
    outline = night_outline()
    inner = outline.buffer(-12)
    add("base", outline, 0, BASE_H)
    add("main", ring(outline, 12), BASE_H, BASE_H + FRAME_RAISE)

    def put(role, g, z0=BASE_H, z1=TOP):
        add(role, only_polygons(g.intersection(inner)), z0, z1)

    # crescent moon (accent), hugging the left edge
    moon = circle(-70, 50, 62).difference(circle(-46, 62, 52))
    put("accent", moon)

    # clouds standing on the pedestal (main), with the footprint area in them
    clouds = unary_union([circle(x, -97, r) for x, r in [(-100, 17), (-70, 22), (-35, 18), (0, 23), (35, 18), (70, 22), (105, 16)]]
                         + [box(-125, -140, 125, -97)]).intersection(box(-200, -118, 200, 0))
    pad = affinity.scale(circle(62, -99, 1), 40, 17, origin=(62, -99))
    put("main", clouds.difference(pad))
    put("base", pad)
    put("accent", ring(pad, rw(1.2)))
    put("accent", heart(62, -99, 11))

    # name cloud with the name
    banner = unary_union([rrect(42, 80, 120, 34, 17), circle(14, 98, 14), circle(46, 102, 19), circle(80, 96, 13)])
    put("base", banner)
    put("main", ring(banner, rw(1.4)))
    put("main", put_text([(data["name"], 22 if lang == "ar" else 19, "word")], lang, rtl, 42, 72, max_width=100), BASE_H, TOP + 0.4)

    # four hanging tags: weight, length, time, date (as in the reference picture, left to right)
    conv = (lambda s: s.translate(ARABIC_DIGITS)) if lang == "ar" else (lambda s: s)
    ampm = AMPM[lang][data.get("ampm", "AM").upper()]
    items = [("weight", [(conv(data["weight"]), 9, "num"), (UNITS[lang]["weight"], 5.5, "word")]),
             ("length", [(conv(data["length"]), 9, "num"), (UNITS[lang]["length"], 5.5, "word")]),
             ("time", [(conv(data["time"]), 8, "num"), (ampm, 5.5, "word")]),
             ("date", [(conv(data["date"]), 6, "num")])]
    label_font = "ar_label" if rtl else "en_label"
    for (key, vals), tx in zip(items, (-12, 24, 60, 96)):
        ty = 5
        tag = tag_shape(tx, ty)
        string = box(tx - 0.8, ty + 25, tx + 0.8, 78).difference(banner)
        put("main", string)
        put("base", tag)
        put("main", ring(tag, rw(1.2)))
        put("main", affinity.translate(ICONS[key](0.42), tx, ty + 12))
        if k >= 0.6:
            lab, _ = text_line([(LABELS[lang][key], 5.2, "word")], lang, rtl)
            lw = max(lab.bounds[2], 1)
            sc = min(1, 28 / lw)
            lab = affinity.scale(lab, sc, sc, origin=(0, 0))
            put("main", affinity.translate(lab, tx - lw * sc / 2 if not rtl else tx + lw * sc / 2 - lw * sc * 0 - lw * sc, ty - 1.5), BASE_H, TOP)
        put("main", put_text(vals, lang, rtl, tx, ty - 12.5, "center", 28), BASE_H, TOP)

    # stars
    for (x, y, r) in [(-5, 112, 6), (108, 52, 6), (32, -52, 7), (96, -50, 6.5), (66, -38, 4.5)]:
        put("accent", star(x, y, r))

    baby = sleeping_baby(-84, -60)
    for role, its in baby.items():
        for g, z0, z1 in its:
            put(role, g, z0, z1)


# ------------------------------------------------------- "train" layout ----
def layout_train_drawn(data, add, layers, k, lang, rtl):
    """Wide plaque (about 300 x 190 design units): a steam engine pulling four wagons that carry the weight, length, time
    and date cards, a dome behind them with the name, a sleeping bear on the dome, a moon and stars. Flat shapes only."""
    put = lambda role, g, z0=BASE_H, z1=TOP: add(role, only_polygons(g), z0, z1)

    def disc_ring(cx, cy, r, w):
        return ring(circle(cx, cy, r), w)

    # --- body parts (all navy = the base plate silhouette) ---
    slab = rrect(0, -80, 300, 20, 10)
    dome = affinity.scale(circle(0, 0, 1), 78, 56, origin=(0, 0))
    dome = affinity.translate(dome, 72, 30).intersection(box(-200, 30, 300, 200))
    wagons = rrect(64, -3, 176, 66, 10)
    boiler = rrect(-100, -4, 100, 52, 14)
    chimney = unary_union([box(-128, 20, -108, 60), rrect(-118, 60, 30, 9, 4)])
    cab = unary_union([rrect(-43, 6, 40, 64, 5), rrect(-43, 40, 48, 11, 4)])
    smoke = unary_union([circle(-140, 76, 10), circle(-124, 82, 12), circle(-107, 77, 10), circle(-94, 71, 8),
                         rrect(-116, 72, 50, 10, 5)])
    cow = Polygon([(-152, -48), (-122, -30), (-122, -72), (-148, -72)]).buffer(1.5, 6)
    wheels = [(-80, -54, 18), (-118, -60, 13), (0, -57, 13.5), (43, -57, 13.5), (86, -57, 13.5), (129, -57, 13.5)]
    bear_sil = affinity.scale(unary_union([circle(40, 84, 19), circle(25, 99, 8), circle(55, 99, 8),
                                          affinity.translate(affinity.scale(circle(0, 0, 1), 8.5, 6.5), 28, 67),
                                          affinity.translate(affinity.scale(circle(0, 0, 1), 8.5, 6.5), 52, 67)]),
                              1.15, 1.15, origin=(40, 84))
    body = unary_union([bear_sil.buffer(3, 12), slab, dome, wagons, boiler, chimney, cab, cow, smoke.buffer(3, 12)] +
                       [circle(x, y, r + 1) for x, y, r in wheels])
    outline = body.buffer(2, 12).buffer(-2, 12)
    add("base", outline, 0, BASE_H)
    add("main", ring(outline, 2.6), BASE_H, BASE_H + FRAME_RAISE)

    # --- cream (main) details ---
    texts = []        # recessed: the navy plate shows through
    label_font = "ar_label" if rtl else "en_label"
    conv = (lambda t: t.translate(ARABIC_DIGITS)) if lang == "ar" else (lambda t: t)
    ampm = AMPM[lang][data.get("ampm", "AM").upper()]
    items = {"weight": [(conv(data["weight"]), 9, "num"), (UNITS[lang]["weight"], 6, "word")],
             "length": [(conv(data["length"]), 9, "num"), (UNITS[lang]["length"], 6, "word")],
             "time": [(conv(data["time"]), 8, "num"), (ampm, 6, "word")],
             "date": [(conv(data["date"]), 6.4, "num")]}
    order = ["date", "time", "length", "weight"] if rtl else ["weight", "length", "time", "date"]
    cards, card_marks = [], []
    for key, cx in zip(order, (0, 43, 86, 129)):
        card = rrect(cx, -3, 37, 52, 8)
        cards.append(card)
        mark = [affinity.translate(ICONS[key](0.5), cx, 10)]
        if k >= 0.6:
            lab, _ = text_line([(LABELS[lang][key], 5.4, "word")], lang, rtl)
            lw = max(lab.bounds[2], 1)
            sc = min(1, 30 / lw)
            lab = affinity.scale(lab, sc, sc, origin=(0, 0))
            mark.append(affinity.translate(lab, cx - lw * sc / 2 + (0 if not rtl else 0), -6))
        mark.append(put_text(items[key], lang, rtl, cx, -19, "center", 32))
        card_marks += mark
    dome_cream = affinity.translate(affinity.scale(circle(0, 0, 1), 52, 34, origin=(0, 0)), 62, 30).intersection(box(-200, 30, 300, 200))
    name = put_text([(data["name"], 19 if lang == "ar" else 16, "word")], lang, rtl, 62, 38, max_width=70)
    window = rrect(-43, 10, 17, 26, 3)
    stripes = unary_union([box(x, -80, x + 3, -20) for x in (-146, -140, -134, -128)]).intersection(cow.buffer(-1.5))
    marks = unary_union(card_marks + [name])
    put("main", unary_union(cards + [dome_cream, smoke, window]).difference(marks))
    put("main", stripes)

    # --- yellow (accent) ---
    moon = circle(121, 56, 17).difference(circle(128, 60, 14))
    stars = [star(8, 50, 7), star(100, 78, 6), star(138, 36, 5), star(14, 72, 4.5)]
    front = circle(-130, -6, 19)
    put("accent", unary_union([moon] + stars))
    put("accent", front.difference(star(-130, -6, 10.5)))
    put("accent", unary_union([box(-128, 36, -108, 42), box(-65, 38, -21, 42)]))
    for x, y, r in wheels:
        put("accent", disc_ring(x, y, r * 0.8, r * 0.3))

    # --- the bear (animal colour), resting on the dome ---
    hx, hy = 40, 84
    head = circle(hx, hy, 19)
    ears = unary_union([circle(hx - 15, hy + 15, 8), circle(hx + 15, hy + 15, 8)])
    inner = unary_union([circle(hx - 15, hy + 15, 4), circle(hx + 15, hy + 15, 4)])
    paws = unary_union([affinity.scale(circle(hx - 12, hy - 17, 1), 8.5, 6.5, origin=(hx - 12, hy - 17)),
                        affinity.scale(circle(hx + 12, hy - 17, 1), 8.5, 6.5, origin=(hx + 12, hy - 17))])
    def lower_arc(x, y, r, w):
        return ring(circle(x, y, r), rw(w)).intersection(box(x - r - 1, y - r - 1, x + r + 1, y))
    feat = unary_union([lower_arc(hx - 7.5, hy + 3, 3.8, 1.5), lower_arc(hx + 7.5, hy + 3, 3.8, 1.5),
                        affinity.scale(circle(hx, hy - 3.5, 1), 3.2, 2.3, origin=(hx, hy - 3.5)),
                        box(hx - 0.7, hy - 8.5, hx + 0.7, hy - 4), lower_arc(hx - 2.8, hy - 8, 2.8, 1.2), lower_arc(hx + 2.8, hy - 8, 2.8, 1.2)])
    grow = lambda g: affinity.scale(g, 1.15, 1.15, origin=(hx, hy))
    bear = grow(unary_union([head, ears, paws]))
    put("animal", bear.difference(grow(feat)).difference(grow(inner)))
    put("main", grow(inner))
    return outline


# ------------------------------------------------------ traced layouts ----
def layout_horse(data, add, layers, k, lang, rtl):
    """Rocking horse traced from a picture (cad/trace_layers.py -> cad/plaque/horse_layers.json): navy plate = the
    silhouette, cream / blue / yellow raised on it. The name on the saddle and the four info columns on the rocker are
    re-drawn with the real fonts (the traced ones are cut out first)."""
    from shapely.geometry import shape
    d = json.load(open(Path(__file__).parent / "plaque" / "horse_layers.json"))
    geo = {r: only_polygons(shape(d[r])) for r in ("base", "main", "accent", "animal")}
    add("base", geo["base"], 0, BASE_H)
    zones = [box(-118, -135, 118, -52), box(-26, -16, 54, 30)]   # where the traced text / icons are
    for role in ("main", "accent", "animal"):
        g = geo[role]
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            if p.area < 25 or (role == "main" and p.area < 700 and any(p.within(z) for z in zones)):
                continue      # glow specks and the traced letters / icons
            if role == "animal" and p.area < 60 and p.centroid.y < -50:
                continue
            add(role, p, BASE_H, TOP)
    add("main", put_text([(data["name"], 30 if lang == "ar" else 24, "word")], lang, rtl, 14, -2, max_width=58), BASE_H, TOP)
    conv = (lambda t: t.translate(ARABIC_DIGITS)) if lang == "ar" else (lambda t: t)
    ampm = AMPM[lang][data.get("ampm", "AM").upper()]
    items = {"weight": [(conv(data["weight"]), 8, "num"), (UNITS[lang]["weight"], 5.5, "word")],
             "length": [(conv(data["length"]), 8, "num"), (UNITS[lang]["length"], 5.5, "word")],
             "time": [(conv(data["time"]), 7.5, "num"), (ampm, 5.5, "word")],
             "date": [(conv(data["date"]), 6.2, "num")]}
    order = ["date", "time", "length", "weight"] if rtl else ["weight", "length", "time", "date"]
    for key, cx in zip(order, (-78, -26, 26, 78)):
        add("main", affinity.translate(ICONS[key](0.36), cx, -66), BASE_H, TOP)
        if k >= 0.6:
            lab, _ = text_line([(LABELS[lang][key], 5.0, "word")], lang, rtl)
            lw = max(lab.bounds[2], 1)
            sc = min(1, 36 / lw)
            add("main", affinity.translate(affinity.scale(lab, sc, sc, origin=(0, 0)), cx - lw * sc / 2, -77), BASE_H, TOP)
        add("main", put_text(items[key], lang, rtl, cx, -89, "center", 40), BASE_H, TOP)
    for x in (-52, 0, 52):
        add("main", box(x - 0.6, -95, x + 0.6, -64), BASE_H, TOP)


def layout_train(data, add, layers, k, lang, rtl):
    """Train traced from the owner's flat picture (cad/trace_layers.py -> cad/plaque/train_layers.json, options in
    train_trace_opts.json). Name and the four values are cut out of the cream and re-drawn with the real fonts
    (recessed, like the picture); labels and icons stay as traced."""
    from shapely.geometry import shape
    d = json.load(open(Path(__file__).parent / "plaque" / "train_layers.json"))
    m = d["meta"]
    S_, CX, CY = m["s"], m["cx"], m["cy"]
    to_d = lambda px, py: ((px - CX) * S_, -(py - CY) * S_)
    def pxbox(x0, y0, x1, y1):
        a, b = to_d(x0, y0)
        c, e = to_d(x1, y1)
        return box(min(a, c), min(b, e), max(a, c), max(b, e))
    def specks_out(g, min_area=4.0):      # tiny islands from the tracing are not printable
        return unary_union([p for p in (g.geoms if hasattr(g, "geoms") else [g]) if p.area >= min_area])
    geo = {r: specks_out(only_polygons(shape(d[r])), 0 if r == "base" else 4.0) for r in ("base", "main", "accent", "animal", "animal2")}
    # text areas (pixels of the original 2576 x 1438 picture): name (+ the hamza above it) and the four values
    areas = [pxbox(1090, 554, 1860, 805), pxbox(1661, 457, 1800, 567), pxbox(900, 1060, 1260, 1178),
             pxbox(1340, 1060, 1625, 1178), pxbox(1750, 1060, 2000, 1178), pxbox(2130, 1060, 2410, 1178)]
    cream = only_polygons(geo["main"].union(unary_union(areas)))
    conv = (lambda t: t.translate(ARABIC_DIGITS)) if lang == "ar" else (lambda t: t)
    ampm = AMPM[lang][data.get("ampm", "AM").upper()]
    vals = {"date": ([(conv(data["date"]), 13, "num")], to_d(1082, 1159)[0], 38),
            "time": ([(conv(data["time"]), 17, "num"), (ampm, 11, "word")], to_d(1481, 1159)[0], 38),
            "length": ([(conv(data["length"]), 17, "num"), (UNITS[lang]["length"], 11, "word")], to_d(1874, 1159)[0], 32),
            "weight": ([(conv(data["weight"]), 17, "num"), (UNITS[lang]["weight"], 11, "word")], to_d(2269, 1159)[0], 38)}
    marks = [put_text([(data["name"], 46 if lang == "ar" else 38, "name")], lang, rtl, to_d(1468, 773)[0], to_d(1468, 773)[1], max_width=82)]
    vy = to_d(0, 1159)[1]
    for key, (segs, cx, mw) in vals.items():
        marks.append(put_text(segs, lang, rtl, cx, vy, "center", mw))
    cream = only_polygons(cream.difference(unary_union(marks)))
    # a flat track strip under the wheels (as on the product photo): the plaque gets a flat bottom edge that the feet / the
    # light tray can hold, and the wheels sit on something
    bx0, by0, bx1, by1 = geo["base"].bounds
    track = rrect((bx0 + bx1) / 2, by0 + 1.0, (bx1 - bx0) - 14, 9.0, 4.0)
    add("base", unary_union([geo["base"], track]), 0, BASE_H)
    add("main", cream, BASE_H, TOP)
    add("accent", geo["accent"], BASE_H, TOP)
    add("animal", geo["animal"], BASE_H, TOP + 0.6)      # the bear stands a little proud of the rest
    add("animal", only_polygons(geo["animal2"].buffer(0.08)), BASE_H, TOP)           # its darker details (inner ears, toes) are lower

# --------------------------------------------------------------- layout ----
def build(data):
    global _K, BASE_H, TOP
    size = float(data.get("size", 300))
    _K = k = size / SIZE
    lit = bool(data.get("lit"))
    glow = bool(data.get("glow"))
    boxes = data.get("boxes", True)      # False: no outline rectangles around the badges and the footprint pad
    BASE_H = float(data["base_h"]) if "base_h" in data else (LIT_BASE_H if lit else 2.4)
    TOP = BASE_H + RAISE
    lang = data.get("lang", "ar")
    rtl = lang == "ar"
    layers = {"base": [], "main": [], "accent": [], "animal": []}

    def add(role, geom, z0=BASE_H, z1=TOP):
        if geom is not None and not geom.is_empty:
            layers[role].append((geom, z0, z1))

    if data.get("layout") == "night":
        layout_night(data, add, layers, k, lang, rtl)
    elif data.get("layout") == "horse":
        layout_horse(data, add, layers, k, lang, rtl)
    elif data.get("layout") == "train":
        layout_train(data, add, layers, k, lang, rtl)
    else:
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
            if boxes:
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
        if boxes:
            add("main", ring(pad, rw(1.2)), BASE_H, TOP)
        add("accent", heart(0, -97, 12), BASE_H, TOP)
    if data.get("stand") == "rails" and data.get("layout") not in ("night", "train", "horse"):
        # T-shaped rails recessed in the two side frame bands (see STANDS.md): cut the base and the frame ring
        opening, cavity = rail_cutters(size)
        (plate0, p0, p1), (ring0, r0, r1) = layers["base"][0], layers["main"][0]
        layers["base"][0:1] = [(plate0.difference(opening), p0, RAIL_OPEN_H), (plate0.difference(cavity), RAIL_OPEN_H, p1)]
        layers["main"][0:1] = [(ring0.difference(cavity), r0, RAIL_CAV_TOP), (ring0, RAIL_CAV_TOP, r1)]
    if data.get("glow_cap"):
        # backlit, cheap in colour changes: the opaque base (one colour) only gets openings; each translucent part
        # is printed on top of its opening, resting on the rim of the base around it. The frame band stays
        # a plain raised band (nothing could hold it up over an opening).
        plate_g = layers["base"][0][0]
        openings = []
        for role in ("main", "accent", "animal"):
            capped = []
            for i, (g, z0, z1) in enumerate(layers[role]):
                if role == "main" and i == 0 and data.get("layout") not in ("train", "horse"):
                    capped.append((g, z0, z1))
                elif abs(z0 - BASE_H) < 1e-6:
                    hole = g.buffer(-CAP_OVERLAP / k, join_style=1)   # opening a bit smaller than the part itself
                    for part in (hole.geoms if hasattr(hole, "geoms") else [hole]):
                        if not part.is_empty:
                            openings.append(add_ribs(part, k))
                    capped.append((g, z0, z1))
                else:
                    capped.append((g, z0, z1))
            layers[role] = capped
        layers["base"][0] = (only_polygons(plate_g.difference(unary_union(openings))), 0, BASE_H)
    if glow:
        # backlit coloured glass: opaque base, every coloured part flush with it and through its full thickness
        plate_g = layers["base"][0][0]                 # the first base item is the plate itself
        ontop = unary_union([g for r in layers for g, z0, _ in layers[r] if z0 >= TOP - 1e-6])
        flush = {r: [] for r in layers}
        for role, its in layers.items():
            for g, z0, z1 in its:
                if g is plate_g:
                    continue
                if z0 >= TOP - 1e-6:                   # eyes, nose, muzzle, inner ears
                    flush[role].append((g, 0, BASE_H))
                elif z0 >= BASE_H - 1e-6:              # raised parts become flush inlays
                    if role == "base":
                        continue                       # the raised cream cloud fill is not needed
                    flush[role].append((only_polygons(g.difference(ontop)) if role == "animal" else g, 0, BASE_H))
        holes = unary_union([g for its in flush.values() for g, _, _ in its])
        flush["base"].insert(0, (only_polygons(plate_g.difference(holes)), 0, BASE_H))
        layers = flush
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
    return {role: [(fix(affinity.scale(g, k, k, origin=(0, 0))), z0, z1) for g, z0, z1 in its]
            for role, its in layers.items()}



# ------------------------------------------------------- rocker runner ----
RUNNER_DEPTH = 50.0    # mm, front-to-back width of the runner (stability sideways)
RUNNER_BELOW = 14.0    # mm of runner under the plate's bottom edge
RUNNER_GRIP = 8.0      # mm of the plate that sits inside the slot


def make_rocker_runner(base_mm, plate_thick, half_span=110.0, clearance=0.6):
    """A curved runner (a banana seen from the side) with a slot along its top; the plaque's curved bottom edge slides into the slot
    and the whole thing rocks like a rocking horse. base_mm: the plaque silhouette in mm. Printed lying on its side (arc flat on the bed).
    Returns (mesh, polygon_in_plaque_coordinates, info)."""
    xs = np.arange(-half_span, half_span + 0.1, 2.0)
    low = []
    for x in xs:
        ys = base_mm.intersection(LineString([(x, -1000), (x, 1000)]))
        low.append(ys.bounds[1] if not ys.is_empty else np.nan)
    low = np.array(low)
    low = ndi.gaussian_filter1d(low, 1.5, mode="nearest")
    top = [(x, y + RUNNER_GRIP) for x, y in zip(xs, low)]
    bot = [(x, y - RUNNER_BELOW) for x, y in zip(xs, low)]
    region = Polygon(top + bot[::-1]).buffer(3, 8).buffer(-3, 8)      # rounded ends
    slot_xy = only_polygons(base_mm.intersection(region))
    w = plate_thick + clearance
    mid = RUNNER_DEPTH / 2
    parts = []
    parts += extrude(region, 0, mid - w / 2)
    parts += extrude(region, mid + w / 2, RUNNER_DEPTH)
    floor = only_polygons(region.difference(slot_xy.buffer(0.01)))
    parts += extrude(floor, mid - w / 2, mid + w / 2)
    mesh = merge_solids(parts)
    length = xs[-1] - xs[0]
    return mesh, region, {"length": length, "depth": RUNNER_DEPTH, "slot": w}

# ------------------------------------------------------------ lit box ----
BOX_DEPTH, BOX_WALL, BOX_BACK = 25.0, 2.6, 1.2


def make_lit_box(size, glow=False):
    """Shallow white tray behind the backlit plate: LED strip stuck on its back panel, USB-C slot in the
    bottom wall, 12 small ledges hold the plate whose front face ends flush with the rim.
    Printed back panel down. Returns (mesh, info)."""
    k = size / SIZE
    depth = 14.0 if glow else BOX_DEPTH            # glow: opaque base hides uneven light, so a shallow tray is enough
    back = 1.0 if glow else BOX_BACK
    half = size / 2 + 0.2                     # plate half-size + clearance
    r = 30 * k + 0.2
    outer = rrect(0, 0, 2 * (half + BOX_WALL), 2 * (half + BOX_WALL), r + BOX_WALL)
    ring = outer.difference(rrect(0, 0, 2 * half, 2 * half, r))
    plate_t = 2.4 if glow else LIT_BASE_H + FRAME_RAISE
    ledge_top = depth - plate_t
    slot = box(-5, -half - BOX_WALL - 1, 5, -half + 1)
    z0, z1 = (4.0, 8.5) if glow else (10.0, 14.5)   # USB-C slot height band
    tabs = unary_union([t for off in (-0.33 * size, 0, 0.33 * size) for t in (
        box(off - 15, -half - 0.1, off + 15, -half + 2.5), box(off - 15, half - 2.5, off + 15, half + 0.1),
        box(-half - 0.1, off - 15, -half + 2.5, off + 15), box(half - 2.5, off - 15, half + 0.1, off + 15))])
    cuts = sorted({0, back, z0, z1, ledge_top - 2.0, ledge_top, depth})
    meshes = []
    for a, b in zip(cuts, cuts[1:]):       # one extrusion per slab, so no part overlaps another
        mid = (a + b) / 2
        g = outer if mid < back else (ring.difference(slot) if z0 < mid < z1 else ring)
        if ledge_top - 2.0 < mid < ledge_top:
            g = g.union(tabs)
        meshes += extrude(g, a, b)
    mesh = merge_solids(meshes)
    return mesh, {"outer": 2 * (half + BOX_WALL), "depth": depth}



def make_lit_tray(outline_mm, glow=True, key_x=60.0):
    """Light tray that follows the plaque outline (for traced layouts): back panel for the LED strip, a wall around the plaque, a ledge the
    plaque rests on, flush front, USB-C slot in the lowest wall. Printed back panel down. Returns (mesh, info)."""
    depth, back, wall, c = 14.0, 1.2, 2.0, 0.3     # slim walls and an open back with LED bars = much less plastic and print time
    inner = outline_mm.buffer(c, 12)
    outer = inner.buffer(wall, 12)
    walls = outer.difference(inner)
    ledge = inner.difference(inner.buffer(-2.5, 12))
    plate_t = 2.4
    ledge_top = depth - plate_t
    x_low = outer.bounds[1]
    # the lowest point of the outer wall: put the cable slot where the wall is flat (the track strip)
    cx = (outer.bounds[0] + outer.bounds[2]) / 2
    slot = box(cx - 5, x_low - 1, cx + 5, x_low + wall + 1)
    z0, z1 = 4.0, 8.5
    x0, y0, x1, y1 = outer.bounds
    KEY_X, KEY_W = key_x, 6.6     # base pegs enter these holes in the lowest wall (depth middle)
    key_holes = unary_union([box(cx0 - KEY_W / 2, y0 - 1, cx0 + KEY_W / 2, y0 + wall + 1) for cx0 in (cx - KEY_X, cx + KEY_X)])
    k0, k1 = depth / 2 - KEY_W / 2, depth / 2 + KEY_W / 2
    bars = unary_union([box(x0 - 1, y0 + f * (y1 - y0) - 8, x1 + 1, y0 + f * (y1 - y0) + 8) for f in (0.2, 0.5, 0.8)])
    back_panel = only_polygons(outer.difference(inner.buffer(-1.5, 8).difference(bars)))   # LED strips stick on the three bars, the rest of the back is open
    cuts = sorted({0, back, z0, z1, k0, k1, ledge_top - 2.0, ledge_top, depth})
    meshes = []
    for a, b in zip(cuts, cuts[1:]):
        mid = (a + b) / 2
        g = back_panel if mid < back else (walls.difference(slot) if z0 < mid < z1 else walls)
        if k0 < mid < k1 and mid >= back:
            g = g.difference(key_holes)
        if ledge_top - 2.0 < mid < ledge_top:
            g = g.union(ledge)
        meshes += extrude(only_polygons(g), a, b)
    return merge_solids(meshes), {"outer": outer.bounds, "depth": depth}

# ----------------------------------------------------------------- stand ----
TILT = 12.0       # degrees the plaque leans back
SLOT_DEPTH = 14.0
PLATE_EDGE = BASE_H + FRAME_RAISE   # plaque thickness at the frame
CLEARANCE = 0.6   # total slot slack


def make_foot(size, thickness=None, length=None, plate_h=None, arches=False, key_x=60.0, sleepers=False):
    """One of two feet: a block with a tilted slot the plaque's bottom edge slides into.
    Returns (mesh, info). Print two. Profile is in YZ (Y = depth, Z up), extruded along X."""
    k = size / SIZE
    depth, width, height = 40 + 30 * k, 50 + 20 * k, SLOT_DEPTH + 8
    t = math.radians(TILT)
    if length:        # one long base instead of two feet: as shallow as the plaque's own height allows (stability margin >= 20 mm)
        width = length
        depth = max(45.0, (12 + 8 * k) - SLOT_DEPTH * math.tan(t) + (plate_h or size) / 2 * math.sin(t) + 20.0)
    w = (thickness or PLATE_EDGE) + CLEARANCE
    y0 = 12 + 8 * k   # slot top-centre, measured from the front of the foot
    half = w / (2 * math.cos(t))
    shift = SLOT_DEPTH * math.tan(t)
    slot = Polygon([(y0 - half, height), (y0 + half, height),
                    (y0 + half - shift, height - SLOT_DEPTH), (y0 - half - shift, height - SLOT_DEPTH)])
    profile = box(0, 0, depth, height).difference(slot)
    m = trimesh.creation.extrude_polygon(profile, width)  # profile x->Y (depth), y->Z (up), extrusion z->X (width)
    m.apply_transform([[0, 0, 1, -width / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    if length:        # railway track: sleepers (cross grooves) on the whole top and two rails on the rear deck; two pegs for the tray's holes
        tx = np.arange(-width / 2 + 10, width / 2 - 8, 14.0)
        grooves = [trimesh.creation.box(extents=[4.0, depth + 2, 1.6], transform=trimesh.transformations.translation_matrix([x, depth / 2, height - 0.8 + 0.01])) for x in tx]
        for gm in (grooves if sleepers else []):
            m = trimesh.boolean.difference([m, gm], engine="manifold")
        for ry in (depth - 8.0, depth - 21.0):
            rail = trimesh.creation.box(extents=[width - 6, 5.0, 2.0], transform=trimesh.transformations.translation_matrix([0, ry, height + 0.99]))
            m = trimesh.boolean.union([m, rail], engine="manifold")
        keyx = key_x
        for sx in (-1, 1):
            peg = trimesh.creation.box(extents=[6.0, 6.0, 3.0])
            peg.apply_transform(trimesh.transformations.rotation_matrix(-t, [1, 0, 0]))
            fy, fz = y0 - shift, height - SLOT_DEPTH                    # centre of the slot floor
            peg.apply_translation([sx * keyx, fy + 1.0 * math.sin(t), fz + 1.0 * math.cos(t)])
            m = trimesh.boolean.union([m, peg], engine="manifold")
    if length and arches:   # (measured: saves only ~4 g and costs +7 min, so off by default) lightening arches behind the slot: trapezoid windows open to the rear face, 45 degree sides (printable without supports)
        wy0 = y0 + half + 6.0
        n_win = max(2, int(width // 75))
        pitch = width / (n_win + 1) if False else (width - 36) / n_win
        for i in range(n_win):
            cx = -width / 2 + 18 + pitch * (i + 0.5)
            hh = height - 6.0
            tri = Polygon([(cx - pitch / 2 + 9, 0), (cx + pitch / 2 - 9, 0), (cx + pitch / 2 - 9 - hh, hh), (cx - pitch / 2 + 9 + hh, hh)])
            if tri.area < 10:
                continue
            w = trimesh.creation.extrude_polygon(tri, depth - wy0 + 1.0)       # u->X, v->Z, extrusion -> Y
            w.apply_transform([[1, 0, 0, 0], [0, 0, 1, wy0], [0, 1, 0, 0], [0, 0, 0, 1]])
            if w.volume < 0:
                w.invert()
            m = trimesh.boolean.difference([m, w], engine="manifold")
    # stability: plaque centre of mass sits (size/2)*sin(tilt) behind the slot's bottom front edge
    com_back = (plate_h or size) / 2 * math.sin(t)
    margin = depth - (y0 - shift) - com_back
    return m, {"depth": depth, "width": width, "height": height, "x": 0.27 * size, "margin": margin}


OPEN = 45.0       # degrees the easel leg opens from the plaque's back


def make_easel(size, open_deg=None, pivot_frac=0.62):
    """Folding easel leg like a photo frame: a bracket glued to the back (two ears) and a
    leg that pivots on an M3 bolt, folds flat and stops at OPEN degrees.
    Both parts are printed on their side (profile on the bed, hole vertical).
    Returns (bracket_mesh, leg_mesh, info, world polygons for the side view)."""
    k = size / SIZE
    t, th = math.radians(TILT), math.radians(OPEN if open_deg is None else open_deg)
    beta = th - t                       # leg angle from vertical
    vp, pad_t, bar, hole, boss = 9.0, 3.0, 4.0, 1.75, 5.0
    w_leg, ear, slack = 14 + 10 * k, 4.0, 0.6
    pad_l, pad_w = 36 * max(k, 0.7), w_leg + 2 * (slack + ear) + 8
    s = pivot_frac * size               # pivot line, measured up the plaque from its bottom edge
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


# ------------------------------------------------------------- rails ----
# Two T-shaped rails recessed in the frame bands (open at the bottom end) take the ends of a separate bridge that
# carries a folding leg in the middle. The frame band is 4.2 mm thick: opening 5 mm for z 0-1.0 (back face on the bed),
# cavity 8 mm for z 1.0-2.8, 1.4 mm ceiling skin. RAIL_TOL is the clearance per side: change it after the first print.
RAIL_TOL = 0.2
RAIL_X = 144.0                 # rail centre line (middle of the 12 mm band)
RAIL_OPEN_W, RAIL_OPEN_H = 5.0, 1.0
RAIL_CAV_W, RAIL_CAV_TOP = 8.0, 2.8
RAIL_PIVOT = 0.75              # bridge (hinge) height as a fraction of the plaque, from the bottom edge
TAB_LEN = 14.0                 # = bridge height, so the tabs reach down to the bed when printed standing on its edge


def rail_cutters(size):
    """(opening, cavity) polygons of the two rails, in the plaque's design space (it is scaled by size/300 afterwards).
    Positions scale with the plaque; widths and clearances stay in real millimetres."""
    k = size / SIZE
    if 12 * k < 10.9:
        raise ValueError("rails need a frame band of at least ~11 mm, i.e. a plaque of 275 mm or more")
    y_top = -SIZE / 2 + RAIL_PIVOT * SIZE + (TAB_LEN / 2 + 0.3) / k
    def rails(width):
        w = width / k
        return unary_union([box(sx * RAIL_X - w / 2, -SIZE, sx * RAIL_X + w / 2, y_top) for sx in (-1, 1)])
    return rails(RAIL_OPEN_W), rails(RAIL_CAV_W)


def make_bridge(size):
    """Bridge with a T-tab at each end (slides up the rails from the bottom) and the hinge ears of a folding leg
    in the middle. Printed standing on its 3 mm edge (no overhangs, no supports). Returns (bridge, leg, info, world)."""
    rail_cutters(size)  # size check
    k = size / SIZE
    rail_x = RAIL_X * k
    _, leg, info, world = make_easel(size, CLIP_OPEN, RAIL_PIVOT)
    vp, jaw, hole = 9.0, 3.0, 1.75
    half_u = 7.0
    neck_w, neck_h = RAIL_OPEN_W - 2 * RAIL_TOL, RAIL_OPEN_H + RAIL_TOL
    head_w, head_top = RAIL_CAV_W - 2 * RAIL_TOL, RAIL_CAV_TOP - RAIL_TOL
    zc = half_u                                   # print frame: X across, Y out of the back (tabs are -Y), Z = u + 7

    def block(sx, sy, sz, cx, cy):
        return trimesh.creation.box((sx, sy, sz), transform=trimesh.transformations.translation_matrix((cx, cy, zc)))

    parts = [block(2 * rail_x + 6, jaw, 2 * half_u, 0, jaw / 2)]
    for sx in (-1, 1):
        parts.append(block(neck_w, neck_h, TAB_LEN, sx * rail_x, -neck_h / 2))
        parts.append(block(head_w, head_top - neck_h, TAB_LEN, sx * rail_x, -(neck_h + head_top) / 2))
    ear2d = circle(0, vp, 6).union(box(-half_u, jaw - 0.1, half_u, vp)).difference(circle(0, vp, hole))   # reaches the bed
    w_leg, ear, slack = info["width"], 3.0, 0.6
    for x0 in (-(w_leg / 2 + slack + ear), w_leg / 2 + slack):
        e = merge_solids(extrude(ear2d, 0, ear))                       # (u, v) extruded along z' = x
        e.apply_transform([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, zc], [0, 0, 0, 1]])
        if e.volume < 0:                                               # the axis swap flips the winding
            e.invert()
        parts.append(e)
    bridge = merge_solids(parts)
    info = dict(info, tab_clearance=RAIL_TOL, bridge=(2 * rail_x + 6, 2 * half_u, jaw))
    return bridge, leg, info, world


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
    TRI_KW = {"engine": "triangle", "triangle_args": "pYa40"}
except ImportError:  # falls back to ear clipping: valid for printing, but long thin triangles
    TRI_KW = {}


def merge_solids(meshes):
    """One closed solid from stacked/touching extrusions (needs manifold3d; otherwise plain concatenation,
    which slices fine but leaves shared edges that some viewers flag as non-manifold)."""
    if len(meshes) == 1:
        return meshes[0]
    try:
        return trimesh.boolean.union(meshes, engine="manifold")
    except Exception:
        return trimesh.util.concatenate(meshes)


def _extrude_gridded(poly, height, spacing=8.0):
    """Extrude a large polygon with a regular grid of interior points, so no triangle is long and thin."""
    import numpy as np
    verts, segs, holes = [], [], []

    def add_ring(coords):
        pts = list(coords)[:-1]
        start = len(verts)
        verts.extend(pts)
        segs.extend((start + i, start + (i + 1) % len(pts)) for i in range(len(pts)))

    add_ring(poly.exterior.coords)
    for r in poly.interiors:
        add_ring(r.coords)
        holes.append(shapely.Polygon(r).representative_point().coords[0])
    inner = poly.buffer(-spacing / 4)
    minx, miny, maxx, maxy = poly.bounds
    for x in np.arange(minx + spacing / 2, maxx, spacing):
        for y in np.arange(miny + spacing / 2, maxy, spacing):
            if inner.contains(shapely.Point(x, y)):
                verts.append((x, y))
    spec = {"vertices": np.array(verts), "segments": np.array(segs)}
    if holes:
        spec["holes"] = np.array(holes)
    import triangle as _tr
    t = _tr.triangulate(spec, "p")
    return trimesh.creation.extrude_triangulation(t["vertices"], t["triangles"], height)


def extrude(geom, z0, z1):
    polys = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    meshes = []
    for p in polys:
        if p.is_empty or p.area < 0.05:
            continue
        # split long edges first and forbid new points on the boundary, so side walls and caps share vertices
        poly = shapely.segmentize(p.simplify(0.02), 8.0)
        try:
            if TRI_KW and poly.area > 400:
                m = _extrude_gridded(poly, z1 - z0)
                if not m.is_watertight or abs(m.volume - poly.area * (z1 - z0)) > 0.01 * poly.area * (z1 - z0):
                    raise ValueError("gridded mesh not valid")
            else:
                m = trimesh.creation.extrude_polygon(poly, z1 - z0, **TRI_KW)
        except Exception:
            # near-tangent edges (e.g. cloud vs paw) can defeat the mesher: round off 0.03 mm slivers and retry
            clean = shapely.segmentize(poly.buffer(-0.03).buffer(0.06).buffer(-0.03).simplify(0.02), 8.0)
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
    return merge_solids(meshes) if meshes else None


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
    if data.get("layout") in ("night", "train", "horse") and data.get("stand") == "rails":
        print("NOTE: this layout has no straight side bands, so the rails stand is not possible; using feet")
        data["stand"] = "feet"
    layers = build(data)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    size = int(data.get("size", 300))
    stem = f"{Path(args.data).stem}_{size}"
    theme = data.get("theme", "blue")
    if data.get("lit"):
        stem += "_lit"
        theme = "lit"
    elif data.get("glow") or data.get("glow_cap"):
        stem += "_glow" if data.get("glow") else "_glowcap"
        theme = theme if theme == "train_lit" else "glow"
    parts = []
    for slot, role in enumerate(("base", "main", "accent", "animal"), start=1):
        m = to_mesh(layers[role])
        if m is not None:
            m.export(out / f"{stem}_{role}.stl")
            print(f"{role}: {len(m.faces)} faces, volume {m.volume:.0f} mm^3")
            parts.append((role, m, slot))
    plate_x = data.get("plate_x", 4 + size / 2)
    material = data.get("material", "petg" if (data.get("lit") or data.get("glow") or data.get("glow_cap")) else "pla")
    template = (Path(__file__).parent / "config" / f"bambu_project_4fil_{material}.config").read_bytes()
    colours = [THEMES[theme][r].upper() for r in ("base", "main", "accent", "animal")]
    # prime tower right of the plaque: it must end before x ~305 (reach of one nozzle, see PRINTING_NOTES.md), so it gets
    # as wide as the room allows (8-14 mm). Above ~290 mm there is no room for a coloured plaque.
    right = plate_x + size / 2
    tower_x = data.get("tower_x", round(right + 3, 1))
    tower_w = data.get("tower_w", max(min(14, round(TOWER_LIMIT - tower_x, 1)), 0))
    if tower_x + tower_w > TOWER_LIMIT + 0.01 or tower_w < 8:
        print(f"WARNING: no room for the prime tower next to a {size:.0f} mm plaque (max about 290 mm for 4 colours)")
    tower = (tower_x, 120, tower_w)
    write_bambu_3mf(out / f"{stem}.3mf", parts, center=(plate_x, data.get("plate_y", 160.0)), name=stem,
                    project_settings=build_project_settings(template, colours, tower))
    print("wrote", out / f"{stem}.3mf")
    preview(layers, theme, out / f"{stem}.png", size / 2)
    if data.get("layout") == "horse":
        runner, region, info = make_rocker_runner(layers["base"][0][0], BASE_H + RAISE)
        runner.export(out / f"rocker_runner_{size}.stl")
        THEMES["horse_runner"] = {**THEMES["horse"], "animal": "#9a9a9a"}   # runner drawn grey (animal role) behind the plaque
        layers_view = {r: list(v) for r, v in layers.items()}
        layers_view["animal"] = [(region, -1, -0.5)] + layers["animal"]
        preview(layers_view, "horse_runner", out / f"{stem}_with_runner.png", size / 2)
        print(f"rocker runner: {info['length']:.0f} mm long x {info['depth']:.0f} mm deep, slot {info['slot']:.1f} mm; "
              f"print lying on its side (the arc flat on the bed); the plaque slides into the slot and rocks")
    elif data.get("lit") or data.get("glow") or data.get("glow_cap"):
        is_glow = bool(data.get("glow") or data.get("glow_cap"))
        if data.get("layout") in ("train", "horse"):
            allg = unary_union([g for its in layers.values() for g, _, _ in its])      # the plaque's full silhouette (the base has openings)
            sil = unary_union([Polygon(pp.exterior) for pp in (allg.geoms if hasattr(allg, "geoms") else [allg])])
            kx = round(60.0 * size / 280.0, 1)
            tray, info = make_lit_tray(sil, key_x=kx)
            tray.export(out / f"light_tray_{size}.stl")
            bx0, by0, bx1, by1 = info["outer"]
            foot, finfo = make_foot(size, thickness=info["depth"], length=0.6 * (bx1 - bx0), plate_h=by1 - by0, key_x=kx)
            foot.export(out / f"stand_base_{size}.stl")
            print(f"light tray: {bx1 - bx0:.0f}x{by1 - by0:.0f}x{info['depth']:.0f} mm, follows the plaque outline; LED strip on its back panel, "
                  f"USB-C slot in the bottom wall; ONE long base {finfo['width']:.0f}x{finfo['depth']:.0f}x{finfo['height']:.0f} mm "
                  f"(slot for the {info['depth']:.0f} mm tray), stability margin {finfo['margin']:.0f} mm")
        else:
            box_mesh, info = make_lit_box(size, glow=is_glow)
            box_mesh.export(out / (f"glow_box_{size}.stl" if is_glow else f"lit_box_{size}.stl"))
            print(f"lit box: {info['outer']:.0f}x{info['outer']:.0f}x{info['depth']:.0f} mm; LED strip on its back panel, USB-C slot in the bottom wall")
    elif data.get("stand") == "rails":
        bridge, leg, info, world = make_bridge(size)
        bridge.export(out / f"bridge_{size}.stl")
        leg.export(out / f"bridge_leg_{size}.stl")
        easel_view(world, out / f"bridge_side_{size}.png", size)
        print(f"rails: bridge {info['bridge'][0]:.0f}x{info['bridge'][1]:.0f}x{info['bridge'][2]:.0f} mm (print standing on its edge), "
              f"leg {info['length']:.0f}x{info['width']:.0f} mm, hinge {info['pivot_from_bottom']:.0f} mm above the bottom edge, "
              f"foot {info['foot_y']:.0f} mm behind, stability margin {info['margin']:.0f} mm, tab clearance {info['tab_clearance']} mm; "
              f"needs an M3 bolt + nut")
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
