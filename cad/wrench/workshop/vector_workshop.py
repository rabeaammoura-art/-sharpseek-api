"""Clean vector workshop (flat 2D, 3 colours) for the wrench key holder.
Layout (positions) is measured on the reference picture (2000-px-wide view, y down); shapes are drawn cleanly instead of traced,
except the two lifts and the house outline, which the owner approved from the traced version.
build(S) -> dict colour -> shapely geometry (view units), colours: 'black' (panel base), 'white', 'orange'.
S = vertical stretch of the layout (round things - gear, lettering, disc, car, heads - are never distorted).
Run: python cad/wrench/workshop/vector_workshop.py <reference.jpg> <out_dir> [S]   -> preview PNGs (flat + overlay on the reference)"""
import json, math, sys
from pathlib import Path
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
YREF = 296.0
FONT = str(HERE.parent.parent / "fonts" / "NotoSans-Bold.ttf")
TRACE = json.loads((HERE / "workshop_trace.json").read_text())
K = TRACE["K"]


def tr_poly(r):  # traced ring (orig px) -> view units
    return Polygon([(x / K, y / K) for x, y in r["outer"]], [[(x / K, y / K) for x, y in h] for h in r["holes"]]).buffer(0)


def rrect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 12)


def build(S=1.5, car_trace=None):
    sy = lambda y: YREF - (YREF - y) * S                      # stretch a y coordinate
    stretch = lambda g: affinity.scale(g, 1, S, origin=(0, YREF))
    sq = S ** 0.5
    W, O, Bk = [], [], []                                     # white, orange, black cut-outs (removed from white/orange)

    # ---- house silhouette (traced, approved) --------------------------------------------------------
    HOUSE = [(590, 92), (1037, -14), (1474, 92), (1474, 128), (1432, 128), (1432, 296), (655, 296), (655, 128), (590, 128)]
    SHELF = [(526, 122), (655, 122), (655, 268), (526, 268)]
    house = unary_union([stretch(Polygon(HOUSE)), stretch(Polygon(SHELF))])
    # roof: white band of constant width under a thin dark edge, plus the two white posts
    edge = [(590, 92), (1037, -14), (1474, 92)]
    band = LineString([(x, y + 10) for x, y in edge]).buffer(7.5, cap_style=2, join_style=2)
    W.append(stretch(band).intersection(house))
    W.append(stretch(box(655, 108, 672, 292))); W.append(stretch(box(1409, 108, 1426, 292)))

    # ---- gear, lettering, stripes (round / fixed shape, only moved) -------------------------------
    dy = sy(52) - 52
    gear = [Point(1037, 52).buffer(31, 48)]
    for i in range(8):
        a = i * math.pi / 4
        tooth = Polygon([(-6.5, 27), (6.5, 27), (5, 41), (-5, 41)])
        gear.append(affinity.translate(affinity.rotate(tooth, math.degrees(a), origin=(0, 0)), 1037, 52))
    gear = unary_union(gear).difference(Point(1037, 52).buffer(12.5, 32))
    W.append(affinity.translate(gear, 0, dy))
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    tp = TextPath((0, 0), "WORKSHOP", size=100, prop=FontProperties(fname=FONT))
    rings = [Polygon(p) for p in tp.to_polygons() if len(p) > 3]
    rings.sort(key=lambda p: -p.area); letters = []
    for p in rings:
        for i, q in enumerate(letters):
            if q.contains(p): letters[i] = q.difference(p); break
        else: letters.append(p)
    txt = unary_union(letters); minx, miny, maxx, maxy = txt.bounds
    k = 306.0 / (maxx - minx)
    txt = affinity.scale(txt, k, -k, origin=(0, 0)); minx, miny, maxx, maxy = txt.bounds
    ty = sy(104)
    W.append(affinity.translate(txt, 1037 - (minx + maxx) / 2, ty - (miny + maxy) / 2))
    for i, y in enumerate((82, 97, 112)):
        d = i * 12
        left = Polygon([(765 + d, y), (872, y), (872, y + 9), (765 + d + 8, y + 9)])
        right = Polygon([(1202, y), (1308 - d, y), (1308 - d - 8, y + 9), (1202, y + 9)])
        O.append(affinity.translate(left, 0, sy(100) - 100)); O.append(affinity.translate(right, 0, sy(100) - 100))

    # ---- left shelf: jerry cans (clear shape: handle hole, spout, chamfer, label) -------------------
    def can(x0, ybot, orange_body):
        w, h = 38, 46 * sq
        y0 = ybot - h
        body = Polygon([(x0, y0 + 10), (x0 + 8, y0 + 10), (x0 + 8, y0 + 2), (x0 + 22, y0 + 2), (x0 + 22, y0 + 12), (x0 + w, y0 + 12), (x0 + w, ybot - 4),
                        (x0 + w - 4, ybot), (x0 + 4, ybot), (x0, ybot - 4)])
        spout = rrect(x0 + 9, y0 - 3, x0 + 17, y0 + 4, 1.5)
        handle = rrect(x0 + 26, y0 + 15, x0 + 34, y0 + 24, 2)       # handle opening (cut)
        label = rrect(x0 + 7, y0 + 27, x0 + 31, ybot - 8, 2)
        if orange_body:
            O.append(body.difference(handle)); W.append(spout)
        else:
            W.append(body.difference(handle).difference(label)); O.append(label); O.append(spout)
    for x0 in (556, 601):
        can(x0, sy(175), True); can(x0, sy(259), False)
    for y in (176, 260):
        W.append(box(545, sy(y), 652, sy(y) + 6))

    # ---- six spanners (open jaw on top, ring at the bottom) ----------------------------------------
    yh, yr = sy(143), sy(212)
    for i in range(6):
        x = 702 + i * 24
        shaft = box(x - 4, yh, x + 4, yr)
        head = Point(x, yh).buffer(10, 24).difference(box(x - 3.2, yh - 14, x + 3.2, yh + 2))
        ring = Point(x, yr).buffer(8.5, 24).difference(Point(x, yr).buffer(3.6, 16))
        W.append(unary_union([shaft, head, ring]))

    # ---- tool cabinet: orange, 2 drawers, white handles, white worktop ----------------------------
    ctop, cbot = sy(290) - 58 * sq, sy(290)
    cab = box(697, ctop, 823, cbot)
    gaps = [box(697, ctop + (cbot - ctop) * 0.40, 823, ctop + (cbot - ctop) * 0.40 + 4), box(758.5, ctop + (cbot - ctop) * 0.40, 762.5, cbot),
            box(697, ctop + (cbot - ctop) * 0.72, 823, ctop + (cbot - ctop) * 0.72 + 4)]
    O.append(cab.difference(unary_union(gaps)))
    W.append(box(693, ctop - 7, 827, ctop))
    for x0, x1 in ((712, 744), (777, 809)):
        for f in (0.20, 0.56, 0.86):
            yy = ctop + (cbot - ctop) * f; W.append(box(x0, yy, x1, yy + 3.5))

    # ---- lifts (traced, approved) --------------------------------------------------------------------
    for r in TRACE["house_orange"]:
        p = tr_poly(r); b = p.bounds
        if p.area > 2500 and b[2] < 1230 and b[0] > 800:
            O.append(stretch(p))

    # ---- car: white body, black windscreen/grille/intake cut-outs, orange headlights ---------------
    cx, cb = 1036, sy(268)
    if car_trace:                                              # car traced from the owner's second picture (local json)
        ct = json.loads(Path(car_trace).read_text()); x0, y0, x1, y1 = ct["bounds"]; kk = 222.0 / (x1 - x0)
        for r in ct["polys"]:
            f = lambda q: (cx + (q[0] - (x0 + x1) / 2) * kk, cb + (q[1] - y1) * kk)
            W.append(Polygon([f(q) for q in r["outer"]], [[f(q) for q in h] for h in r["holes"]]).buffer(0))
    else:
        def car(parts):
            return [affinity.translate(g, cx - 1036, cb - 268) for g in parts]
        body = unary_union([rrect(925, 207, 1147, 268, 20), Polygon([(950, 212), (972, 162), (1100, 162), (1122, 212)]).buffer(6, join_style=1)])
        ws = Polygon([(966, 206), (984, 170), (1088, 170), (1106, 206)])
        grille = rrect(990, 236, 1082, 254, 6)
        intake = Polygon([(1000, 258), (1072, 258), (1066, 267), (1006, 267)])
        hl_l = Polygon([(931, 214), (978, 220), (980, 230), (934, 229)]); hl_r = Polygon([(1141, 214), (1094, 220), (1092, 230), (1138, 229)])
        mirrors = [rrect(915, 198, 930, 207, 3), rrect(1142, 198, 1157, 207, 3)]
        slats = [box(996, 241.5, 1076, 245), box(996, 247.5, 1076, 251)]
        W.extend(car([body.difference(unary_union([ws, grille, intake, hl_l, hl_r])).union(unary_union(mirrors)).union(unary_union([s.intersection(grille) for s in slats]))]))
        O.extend(car([hl_l, hl_r]))

    # ---- ceiling lamp (white shade, orange bulb) hanging between the lettering and the car roof ------
    ly = (sy(104) + 28 + (cb - 107)) / 2 - 8
    W.append(Polygon([(1012, ly + 12), (1024, ly), (1050, ly), (1062, ly + 12)])); O.append(Point(1037, ly + 16).buffer(5.5, 20))
    W.append(box(1035.5, ly - 7, 1038.5, ly))

    # ---- right shelf: frame + 4 oil bottles/filters ------------------------------------------------
    top, bot = sy(135), sy(183)
    W.append(box(1245, top, 1385, top + 5)); W.append(box(1245, top, 1250, bot)); W.append(box(1380, top, 1385, bot)); W.append(box(1245, sy(177), 1385, bot))
    for x0, h in ((1257, 28), (1283, 34), (1309, 26), (1335, 32)):
        hh = h * sq; yb = sy(177)
        W.append(rrect(x0, yb - hh, x0 + 18, yb, 3)); O.append(box(x0 + 3, yb - hh - 5, x0 + 15, yb - hh))

    # ---- brake disc (round, fixed place): rotor 14 holes, hub with 5 bolts, orange caliper ----------
    c = Point(1330, 268); R = 102.0
    rotor = c.buffer(R * 0.94, 64).difference(c.buffer(R * 0.52, 64))
    holes = [Point(1330 + R * 0.73 * math.cos(2 * math.pi * i / 14), 268 + R * 0.73 * math.sin(2 * math.pi * i / 14)).buffer(R * 0.075, 14) for i in range(14)]
    hub = c.buffer(R * 0.42, 48).difference(c.buffer(R * 0.14, 32))
    bolts = [Point(1330 + R * 0.28 * math.cos(2 * math.pi * i / 5 + 0.3), 268 + R * 0.28 * math.sin(2 * math.pi * i / 5 + 0.3)).buffer(R * 0.055, 12) for i in range(5)]
    disc_w = rotor.difference(unary_union(holes)).union(hub.difference(unary_union(bolts)))
    cal = c.buffer(R * 1.0, 64).difference(c.buffer(R * 0.60, 64)).intersection(box(1330 + R * 0.20, 268 - R * 0.85, 1330 + R * 1.2, 268 + R * 0.80))
    cal = cal.buffer(-3).buffer(3)
    slit = box(1330 + R * 0.20, 268 - 1.6, 1330 + R * 1.2, 268 + 1.6)
    cal_o = cal.difference(slit)
    W.append(disc_w.difference(cal.buffer(2.5))); O.append(cal_o)
    disc_base = c.buffer(R * 1.02, 64)

    white = unary_union(W); orange = unary_union(O)
    black_panel = unary_union([house, disc_base])
    return {"house": house, "disc_base": disc_base, "white": white.difference(orange), "orange": orange, "panel": black_panel}


def preview(geoms, ref_img, out, S):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    def patch(g, **kw):
        for p in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
            if p.geom_type != "Polygon" or p.is_empty: continue
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                xy = list(ring.coords); verts += xy; codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
            yield PathPatch(MPath(verts, codes), **kw)
    fig, ax = plt.subplots(figsize=(14, 6.2)); ax.set_facecolor("#cfcfd2")
    for p in patch(geoms["panel"], fc="#26262a", ec="none"): ax.add_patch(p)
    for p in patch(geoms["white"], fc="#f4f4f4", ec="none"): ax.add_patch(p)
    for p in patch(geoms["orange"], fc="#ff7a00", ec="none"): ax.add_patch(p)
    ax.set_xlim(500, 1500); ax.set_ylim(400, -150 if S > 1.2 else -40); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(out, dpi=110, bbox_inches="tight"); plt.close(fig)
    if ref_img is not None:  # overlay on the reference (only meaningful at S=1)
        im = Image.open(ref_img).convert("RGB"); kk = im.size[0] / 2000
        fig, ax = plt.subplots(figsize=(14, 6.2)); ax.imshow(im, extent=(0, im.size[0] / kk, im.size[1] / kk, 0), alpha=1.0)
        for p in patch(geoms["white"], fc="none", ec="cyan", lw=0.8): ax.add_patch(p)
        for p in patch(geoms["orange"], fc="none", ec="lime", lw=0.8): ax.add_patch(p)
        ax.set_xlim(500, 1500); ax.set_ylim(400, -40); ax.set_aspect("equal"); ax.axis("off")
        fig.savefig(str(out).replace(".png", "_overlay.png"), dpi=110, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    ref, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    S = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5
    g = build(S, sys.argv[4] if len(sys.argv) > 4 else None); preview(g, ref if S == 1.0 else None, out / f"vector_S{S}.png", S); print("ok", S)
