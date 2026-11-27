"""Line-art coasters from a picture of several round coasters (owner 2026-11-27: 9 whirling dervishes, 3 x 3 photo).

    python cad/coaster/coaster_lineart.py PICTURE OUT_DIR --settings PREPARED.3mf [--preview PNG]

Each coaster: ring found by a circle fit, lines = pixels darker than the local surface (inside the ring), red fez = red
pixels, the ring itself redrawn as a clean circle. Our coaster spec: Ø95 x 3, TPU 0.4 (face, on the plate) | inlay 0.6 |
TPU 2.0, rounded edges, mirrored. Slots: 1 clear TPU (nozzle 2), 2 line colour, 3 red (nozzle 1).
--settings: a 3-filament 3MF already run through bambu_slice.py + clear_tpu_settings.py; its project settings are reused.
The picture stays out of git.
"""
import argparse, json, sys, zipfile
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from scipy.ndimage import median_filter
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import coaster, coaster_text as ct     # noqa: E402
from threemf import write_bambu_3mf    # noqa: E402

RING_R, RING_W = 41.5, 1.4             # mm: redrawn ring (TPU edge outside it ~5 mm)
ROWS = [("green", "#5E7A2E"), ("gold", "#C79A5B"), ("grey", "#7A7A7A")]   # line colour per picture row
RED = "#C8102E"
GUESS = [(x, y) for y in (207, 600, 1000) for x in (240, 625, 1010)]


def chaikin(geom, n=3):
    """corner cutting on every ring: smooth curves instead of pixel steps"""
    from shapely.geometry import Polygon, MultiPolygon

    def cut(c):
        c = np.asarray(c)[:-1]
        for _ in range(n):
            q = 0.75 * c + 0.25 * np.roll(c, -1, 0); r = 0.25 * c + 0.75 * np.roll(c, -1, 0)
            c = np.empty((2 * len(q), 2)); c[0::2] = q; c[1::2] = r
        return c
    out = []
    for p in getattr(geom, "geoms", [geom]):
        if p.geom_type != "Polygon" or p.area < 0.05:
            continue
        out.append(Polygon(cut(p.exterior.coords), [cut(h.coords) for h in p.interiors if Polygon(h).area > 0.05]).buffer(0))
    return unary_union(out)


def fit_ring(dark, cx, cy, r0=172.0):
    for _ in range(6):
        y0, x0 = max(0, int(cy - r0 - 40)), max(0, int(cx - r0 - 40))
        ys, xs = np.nonzero(dark[y0:int(cy + r0 + 40), x0:int(cx + r0 + 40)])
        xs, ys = xs + x0, ys + y0
        k = np.abs(np.hypot(xs - cx, ys - cy) - r0) < 18
        x, y = xs[k].astype(float), ys[k].astype(float)
        s = np.linalg.lstsq(np.c_[2 * x, 2 * y, np.ones_like(x)], x * x + y * y, rcond=None)[0]
        cx, cy = s[0], s[1]; r0 = np.sqrt(s[2] + cx * cx + cy * cy)
    return cx, cy, r0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture"); ap.add_argument("out"); ap.add_argument("--settings", required=True)
    ap.add_argument("--preview"); ap.add_argument("--stl", action="store_true")
    ap.add_argument("--groove", type=float, default=0.8, help="engraved: open groove depth above the colour (owner 2026-11-27: 0.8)")
    ap.add_argument("--engraved", action="store_true", help="owner 2026-11-27: lines ENGRAVED in the top face, colour at the "
                    "bottom of the groove (TPU 0-2.2 | colour 2.2-2.6 | open groove 2.6-3.0), printed FACE UP, not mirrored")
    a = ap.parse_args()
    im = np.array(Image.open(a.picture).convert("RGB")).astype(float)
    L = im.mean(2)
    red = (im[..., 0] > 150) & (im[..., 1] < 90) & (im[..., 2] < 90)
    dark = (L < median_filter(L, size=31) - 28) & ~red
    yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    cfg0 = json.loads(zipfile.ZipFile(a.settings).read("Metadata/project_settings.config"))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    disc_ring = Point(0, 0).buffer(RING_R + RING_W / 2, 256).difference(Point(0, 0).buffer(RING_R - RING_W / 2, 256))
    previews = []
    for i, (gx, gy) in enumerate(GUESS):
        cx, cy, r0 = fit_ring(dark, gx, gy)
        rpx = r0 * ct.D / 2 / RING_R                      # r0 px -> RING_R mm
        inside = (xx - cx) ** 2 + (yy - cy) ** 2 < (r0 - 9) ** 2
        lines = coaster.mask_to_mm(dark & inside, cx, cy, rpx, up=3, smooth=2.6, clean=False)   # strong blur: the render's lines have rough edges
        fez = coaster.mask_to_mm(red & inside, cx, cy, rpx, up=3, smooth=0.8, clean=False)
        lines = unary_union([q for q in getattr(lines, "geoms", [lines]) if q.area > 0.4])
        thin = lines.difference(lines.buffer(-0.35, 8).buffer(0.35, 8))
        lines = lines.union(thin.buffer(0.2, 8))                                          # thin strokes -> ~0.7 mm
        # owner 2026-11-27: saw-tooth edges (pixel burrs show in the engraved walls): close + open 0.3 mm kills burrs < 0.6 mm,
        # then corner cutting makes the edges true curves
        lines = lines.buffer(0.3, 16).buffer(-0.3, 16).buffer(-0.3, 16).buffer(0.3, 16)
        lines = chaikin(lines.simplify(0.15), 4).simplify(0.01)                         # drop wiggles < 0.15 mm, then true curves
        # fez: shaded in the picture -> holes; keep the outline only, smoothed
        from shapely.geometry import Polygon as _P
        fez = unary_union([_P(q.exterior) for q in getattr(fez, "geoms", [fez]) if q.geom_type == "Polygon" and q.area > 1])
        fez = max(getattr(fez, "geoms", [fez]), key=lambda q: q.area).convex_hull      # a fez is a truncated cone: clean hull
        fez = chaikin(fez.buffer(-0.3, 16).buffer(0.3, 16).simplify(0.05), 2)
        lines = lines.difference(fez.buffer(0.35)).buffer(-0.2, 8).buffer(0.2, 8)      # no line-colour rim round the fez
        near = fez.buffer(2.5)                                                            # owner mark: stray bits by the fez
        lines = unary_union([q for q in getattr(lines, "geoms", [lines])
                             if q.area > 3.0 or (q.area > 1.0 and not q.intersects(near))])
        fez = fez.buffer(0.1, 8).buffer(-0.1, 8)
        lines = unary_union([lines, disc_ring]).difference(fez.buffer(0.01))
        name, colour = ROWS[i // 3]
        z1 = ct.T - a.groove; z0 = z1 - 0.4                    # colour 0.4 mm at the bottom of an open groove
        z0, z1 = (z0, z1) if a.engraved else (ct.Z0, ct.Z1)
        ink_l = coaster.extrude(lines.buffer(0), z0, z1); ink_r = coaster.extrude(fez.buffer(0), z0, z1)
        for m in (ink_l, ink_r):
            if not m.is_volume:
                m.merge_vertices(); m.update_faces(m.nondegenerate_faces()); m.fix_normals()
        allink = trimesh.boolean.union([ink_l, ink_r], engine="manifold")
        cut = [allink]
        if a.engraved:   # open groove above the colour, through the rounded top edge
            cut.append(coaster.extrude(unary_union([lines, fez]).buffer(0), z1 - 0.01, ct.T + 1.0))
        tpu = trimesh.boolean.difference([ct.rounded_disc()] + cut, engine="manifold")
        flip = (lambda m: m) if a.engraved else coaster.mirror_x
        parts = [(n, flip(m), s) for n, m, s in [("clear_tpu", tpu, 1), (name, ink_l, 2), ("red_fez", ink_r, 3)]]
        cfg = dict(cfg0); cfg["filament_colour"] = ["#E8F1F5", colour, RED]
        f = out / f"coaster_dervish_{i + 1}_{name}{'_engraved' if a.engraved else ''}.3mf"
        write_bambu_3mf(f, parts, (175.0, 160.0), f.stem, json.dumps(cfg, indent=4))
        if a.stl:
            for n, m, _ in parts:
                m.export(out / f"{f.stem}_{n}.stl")
        t = lines.difference(lines.buffer(-0.35).buffer(0.35))
        print(f"{i + 1} {name}: ring r {r0:.0f} px, lines {lines.area:.0f} mm2 (under 0.7: {t.area:.1f}), fez {fez.area:.0f} mm2, "
              f"watertight {all(m.is_watertight for _, m, _ in parts)} -> {f.name}")
        previews.append((lines, fez, colour))
    if a.preview:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, PathPatch
        from matplotlib.path import Path as MPath
        from shapely.geometry.polygon import orient

        def patch(p, c):     # polygon with holes as one path (holes must not paint over other shapes)
            p = orient(p); rings = [p.exterior] + list(p.interiors)
            v = np.concatenate([np.asarray(r.coords) for r in rings])
            codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r.coords) - 2) + [MPath.CLOSEPOLY] for r in rings])
            return PathPatch(MPath(v, codes), fc=c, ec="none")
        fig, axs = plt.subplots(3, 3, figsize=(12, 12), dpi=110); fig.patch.set_facecolor("#EDE6DA")
        for ax, (ln, fz, col) in zip(axs.ravel(), previews):
            ax.add_patch(Circle((0, 0), 47.5, fc="#F7F4EE", ec="#C9C2B6", lw=1.5))
            for g, c in ((ln, col), (fz, RED)):
                for p in getattr(g, "geoms", [g]):
                    if p.geom_type == "Polygon":
                        ax.add_patch(patch(p, c))
            ax.set_xlim(-49, 49); ax.set_ylim(-49, 49); ax.set_aspect("equal"); ax.axis("off")
        fig.tight_layout(); fig.savefig(a.preview, facecolor=fig.get_facecolor())


if __name__ == "__main__":
    main()
