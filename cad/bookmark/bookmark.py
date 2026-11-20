"""Tatreez (cross-stitch) bookmark -> Bambu Studio 3MF with two swappable colour parts.

    python cad/bookmark/bookmark.py [--fabric "#F4EFE2"] [--thread "#A3162B"] [--out cad/out/bookmark]

Parts (each its own filament slot, re-assign freely in Bambu Studio):
  slot 1 "fabric"   : plate with the aida weave texture + tassel hole
  slot 2 "stitches" : raised X stitches (two rounded threads, the second one riding over the first)
Printed face up (back on the bed), no supports. Geometry is parametric (own pattern), nothing traced.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import contourpy
import trimesh
from shapely.geometry import Polygon, MultiPolygon, box, Point
from shapely.ops import unary_union
from shapely import affinity

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from threemf import build_project_settings, write_bambu_3mf  # noqa: E402

# ---- size and look --------------------------------------------------------------------------------------------------
W, H, P = 50.0, 170.0, 2.0      # mm, stitch pitch (25 x 85 cells)
CORNER = 3.0                    # plate corner radius
BASE = 1.2                      # plate thickness
FAB_T = 0.16                    # weave blocks height (2 layers of 0.08)
FAB_GAP = 0.6                   # groove between weave blocks (printable gap)
HOLE_R, HOLE_Y = 2.2, 6.0       # tassel hole radius, distance of its centre from the top edge
SR, SH = 0.48, 0.45             # thread half-width, thread height
LIFT = 0.25                     # the top thread rides this much over the bottom one at the crossing
MIN_W = 0.7                     # narrowest printable thread section
LAYER = 0.08                    # slicing of the thread relief into layers (matches a 0.08 mm print layer)
RES = 0.04                      # heightmap resolution for the thread contours
NC, NR = int(W / P), int(H / P)


def pattern():
    """set of (col, row) stitched cells; row 0 = top."""
    cells = set()

    def add(c, r):
        if 1 <= c < NC - 1 and 1 <= r < NR - 1:
            cells.add((c, r))
    for c in range(NC):                         # border band with a dotted middle row
        for r in range(NR):
            d = min(c, r, NC - 1 - c, NR - 1 - r)
            if 1 <= d <= 3 and not (d == 2 and (c + r) % 2 == 0):
                add(c, r)
    mid = NC // 2
    for r in range(5, 31):                      # chest panel (qabbeh), lattice, pointed bottom
        half = 7 - max(0, r - 24)
        for c in range(mid - half, mid + half + 1):
            if r <= 7 and abs(c - mid) <= 3:
                continue
            if abs(c - mid) == half or r == 5 or (c + r) % 2 == 0:
                add(c, r)
    for r in range(0, 9):                       # frame of the neck opening
        add(mid - 3, r); add(mid + 3, r)
    for c in range(mid - 3, mid + 4):
        add(c, 8)
    cells -= {(c, r) for c in range(mid - 2, mid + 3) for r in range(0, 8)}
    for r in range(42, 80):                     # two vertical stitch lines
        add(6, r); add(NC - 7, r)
    return cells


def thread_heightmap(cells):
    """height of the thread relief above the fabric (mm) on a RES grid; y measured from the bottom edge."""
    nx, ny = int(round(W / RES)), int(round(H / RES))
    x = np.arange(nx + 1) * RES
    y = np.arange(ny + 1) * RES
    X, Y = np.meshgrid(x, y)
    Yt = H - Y                                   # from the top, as the pattern rows
    u = (X % P) / P - 0.5
    v = (Yt % P) / P - 0.5
    c = np.clip(np.floor(X / P).astype(int), 0, NC - 1)
    r = np.clip(np.floor(Yt / P).astype(int), 0, NR - 1)
    mask = np.zeros(X.shape, bool)
    grid = np.zeros((NC, NR), bool)
    for cc, rr in cells:
        grid[cc, rr] = True
    mask = grid[c, r]
    s2 = np.sqrt(2)

    def strand(dp, al, lift):
        prof = np.clip(1 - np.abs(dp / SR) ** 4, 0, 1) ** 0.5   # flattish thread: crest stays printable
        end = np.clip((P * 0.62 - np.abs(al)) / 0.25, 0, 1)
        rise = lift * np.clip(1 - np.abs(al) / (P * 0.55), 0, 1)
        return np.where(prof > 0, (SH * prof + rise) * end, 0)
    hs = np.maximum(strand((u - v) * P / s2, (u + v) * P / s2, 0.0),
                    strand((u + v) * P / s2, (u - v) * P / s2, LIFT))
    return x, y, np.where(mask, hs, 0.0)


def contour_polys(x, y, z, level):
    """shapely (Multi)Polygon of the region z >= level."""
    gen = contourpy.contour_generator(x, y, z, fill_type=contourpy.FillType.OuterOffset)
    pts_list, offs_list = gen.filled(level, np.inf)
    polys = []
    for pts, offs in zip(pts_list, offs_list):
        rings = [pts[offs[i]:offs[i + 1]] for i in range(len(offs) - 1)]
        if len(rings[0]) >= 4:
            p = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
            if p.area > 0.02:
                polys.append(p)
    return unary_union(polys)


def extrude(geom, z0, z1):
    geoms = [geom] if isinstance(geom, Polygon) else list(getattr(geom, "geoms", []))
    out = []
    for g in geoms:
        if isinstance(g, Polygon) and g.area > 0.02:
            m = trimesh.creation.extrude_polygon(g.simplify(0.03), z1 - z0)
            m.apply_translation((0, 0, z0))
            out.append(m)
    return out


def union(meshes):
    meshes = [m for m in meshes if len(m.faces)]
    return trimesh.boolean.union(meshes, engine="manifold")


def build():
    cells = pattern()
    x, y, hs = thread_heightmap(cells)
    plate = box(0, 0, W, H).buffer(-CORNER).buffer(CORNER, resolution=16)
    hole = Point(W / 2, H - HOLE_Y).buffer(HOLE_R, resolution=48)
    plate = plate.difference(hole)

    # stitches: layer slabs of the thread relief, starting on top of the plate
    foot = contour_polys(x, y, hs, 0.02).intersection(plate)
    slabs, z = [], 0.0
    top = float(hs.max())
    while z < top - 1e-6:
        lvl = z + LAYER / 2
        g = foot if z == 0 else contour_polys(x, y, hs, min(lvl, top - 0.01)).intersection(plate)
        g = g.buffer(-MIN_W / 2).buffer(MIN_W / 2).intersection(g)   # drop crest slivers the nozzle cannot print
        slabs += extrude(g, BASE + z, BASE + min(z + LAYER, top))
        z += LAYER
    stitches = union(slabs)

    # fabric: plate + weave blocks (2 layers, the second one inset = soft edge) except under the stitches
    keep_out = foot.buffer(0.3)
    blocks1, blocks2 = [], []
    for c in range(NC):
        for r in range(NR):
            x0, y0 = c * P, H - (r + 1) * P
            b1 = box(x0 + FAB_GAP / 2, y0 + FAB_GAP / 2, x0 + P - FAB_GAP / 2, y0 + P - FAB_GAP / 2)
            blocks1.append(b1)
            blocks2.append(b1.buffer(-0.15, join_style=2))
    inner = plate.buffer(-0.8)
    w1 = unary_union(blocks1).intersection(inner).difference(keep_out)
    w2 = unary_union(blocks2).intersection(inner).difference(keep_out)
    w1, w2 = (g.buffer(-0.36).buffer(0.36).intersection(g) for g in (w1, w2))  # drop slivers < 0.7 mm
    fabric = union(extrude(plate, 0, BASE) + extrude(w1, BASE - 0.01, BASE + FAB_T / 2) +
                   extrude(w2, BASE + FAB_T / 2 - 0.01, BASE + FAB_T))
    for m in (fabric, stitches):
        m.apply_translation((-W / 2, -H / 2, 0))
    return fabric, stitches


def _settings(template, colours, tower):
    import json
    cfg = json.loads(build_project_settings(template, colours, tower))
    cfg["layer_height"] = "0.12"          # 0.12 = round threads in 1h14m; 0.08 = 1h34m, 0.16 = 54 min (coarser threads)
    return json.dumps(cfg, indent=4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fabric", default="#F4EFE2", help="slot 1 colour (only the default shown in Studio)")
    ap.add_argument("--thread", default="#A3162B", help="slot 2 colour")
    ap.add_argument("--material", default="pla", choices=["pla", "petg"])
    ap.add_argument("--out", default=str(HERE.parent / "out" / "bookmark"))
    ap.add_argument("--plate-x", type=float, default=128.0)
    ap.add_argument("--plate-y", type=float, default=160.0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    fabric, stitches = build()
    for n, m in (("fabric", fabric), ("stitches", stitches)):
        print(f"{n}: {len(m.faces)} faces, watertight {m.is_watertight}, volume {m.volume:.0f} mm^3, "
              f"z {m.bounds[0][2]:.2f}..{m.bounds[1][2]:.2f}")
        m.export(out / f"bookmark_{n}.stl")
    template = (HERE.parent / "config" / f"bambu_project_4fil_{a.material}.config").read_bytes()
    colours = [a.fabric, a.thread, "#000000", "#FFFFFF"]
    tower = (a.plate_x + W / 2 + 10, a.plate_y - 40, 20)
    write_bambu_3mf(out / "bookmark.3mf", [("fabric", fabric, 1), ("stitches", stitches, 2)],
                    center=(a.plate_x, a.plate_y), name="bookmark",
                    project_settings=_settings(template, colours, tower))
    print("wrote", out / "bookmark.3mf")


if __name__ == "__main__":
    main()
