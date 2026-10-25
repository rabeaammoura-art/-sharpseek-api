"""Text -> shapely polygons (mm) straight from the font outlines (fontTools); no rasterising."""
from functools import lru_cache
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

FONTS = Path(__file__).parent / "fonts"
BOLD = FONTS / "Poppins-Bold.ttf"
EXTRABOLD = FONTS / "Poppins-ExtraBold.ttf"


class _Pen(BasePen):
    def __init__(self, gs, steps=12):
        super().__init__(gs)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps; a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2: self.contours.append(self.cur)
        self.cur = []
    _endPath = _closePath


@lru_cache(maxsize=4)
def _font(path):
    f = TTFont(str(path))
    return f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm


def text_geom(text, size_mm, font=BOLD, tracking=0.0):
    """Polygons for `text`; size_mm = cap height (digits/capitals).  Baseline at y=0, starts at x=0."""
    f, gs, cmap, upm = _font(font)
    cap = f["OS/2"].sCapHeight or 0.7 * upm
    k = size_mm / cap
    x, shapes = 0.0, []
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            raise ValueError(f"font has no glyph for {ch!r}")
        pen = _Pen(gs); gs[g].draw(pen)
        poly = Polygon()
        for c in pen.contours:
            poly = poly.symmetric_difference(Polygon(c).buffer(0))
        if not poly.is_empty:
            shapes.append(affinity.translate(poly, x, 0))
        x += gs[g].width + tracking * upm
    geom = unary_union(shapes) if shapes else Polygon()
    return affinity.scale(geom, k, k, origin=(0, 0))
