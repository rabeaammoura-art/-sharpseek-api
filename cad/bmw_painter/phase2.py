"""BMW painter openwork wall art - PHASE 2 (CAD): masks.npz from phase1.py -> 5 mm solids, STL, 3MF (2 colours), STEP.
usage: python phase2.py <phase1_out_dir> <out_dir> [--depth 5]"""
import sys, os, json, argparse
from pathlib import Path
import numpy as np, cv2, trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from threemf import build_project_settings, write_bambu_3mf

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--depth", type=float, default=5.0); a = ap.parse_args()
PPM = 10.0; OUT = Path(a.out); (OUT / "stl").mkdir(parents=True, exist_ok=True)
d = np.load(Path(a.src) / "masks.npz"); black_m, blue_m = d["black"], d["blue"]; H = black_m.shape[0] / PPM

def polys(mask, eps=0.5):
    cs, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]; out = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1 or len(c) < 4: continue          # outer contours only
        ring = lambda cc: [(p[0][0]/PPM, H - p[0][1]/PPM) for p in cv2.approxPolyDP(cc, eps, True)]
        holes = []; j = hier[i][2]
        while j != -1:
            if len(cs[j]) >= 4: holes.append(ring(cs[j]))
            j = hier[j][0]
        pg = Polygon(ring(c), [h for h in holes if len(h) >= 3])
        if not pg.is_valid: pg = pg.buffer(0)
        if pg.area > 0.05: out.append(pg)
    return unary_union(out)

def clean(g):      # seal pinch points / hairline slivers so every extrusion is a manifold solid
    return g.buffer(0.03, join_style=2).buffer(-0.03, join_style=2).simplify(0.015)
black, blue = clean(polys(black_m)), clean(polys(blue_m))
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
# drop blue slivers (<2 mm2: they are just anti-aliasing leftovers, they become black again)
blue = unary_union([g for g in (blue.geoms if hasattr(blue, "geoms") else [blue]) if g.area >= 2.0])
# bridge every island of the footprint to the main body with a 2 mm bar (vector level, so the 3D part is ONE piece)
for _ in range(5):
    uu = unary_union([black, blue]); pcs = sorted(uu.geoms, key=lambda g: -g.area) if hasattr(uu, "geoms") else [uu]
    if len(pcs) == 1: break
    main = pcs[0]
    if all(g.area <= 0.5 for g in pcs[1:]): break
    for isl in [g for g in pcs[1:] if g.area > 0.5]:
        p, q = nearest_points(isl, main); print("bridge island area %.1f mm2 at (%.1f, %.1f), gap %.2f mm" % (isl.area, p.x, p.y, p.distance(q)))
        black = unary_union([black, (LineString([p, q]).buffer(1.0) if p.distance(q) > 0.05 else Point(p.x, p.y).buffer(1.0))])
def opened(g, r=0.03):      # opening: removes zero-width pinch points (two outlines touching in one vertex)
    return g.buffer(-r, join_style=2).buffer(r, join_style=2)
union = opened(unary_union([black, blue]), 0.08)
blue_f = opened(blue.buffer(0.12).intersection(union), 0.08)     # blue grows 0.12 mm into black: no gap, no overlap
black_f = union.difference(blue_f)
def big(g, amin=0.5):
    return unary_union([x for x in (g.geoms if hasattr(g, "geoms") else [g]) if x.area >= amin])
blue_f, black_f = big(blue_f), big(black_f)
union = unary_union([black_f, blue_f])

def solid(geom, h):
    """exact manifold extrusion (manifold3d): rings with even-odd fill -> watertight solid"""
    import manifold3d as m3
    rings = []
    for pg in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if pg.area < 0.05: continue
        rings.append(np.array(pg.exterior.coords)[:-1]); rings += [np.array(i.coords)[:-1] for i in pg.interiors]
    cs = m3.CrossSection(rings, m3.FillRule.EvenOdd)
    cs = cs.offset(-0.04, m3.JoinType.Round, 2.0, 16).offset(0.04, m3.JoinType.Round, 2.0, 16)   # kills one-vertex touches
    mf = m3.Manifold.extrude(cs, h)
    mesh = mf.to_mesh()
    return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3], np.array(mesh.tri_verts), process=False)

from collections import Counter
def bad_points(m):
    r = trimesh.load(trimesh.util.wrap_as_stream(m.export(file_type="stl")), file_type="stl")
    c = Counter(map(tuple, r.edges_sorted)); pts = {(round(r.vertices[i][0], 1), round(r.vertices[i][1], 1)) for k, v in c.items() if v != 2 for i in k}
    return list(pts)
for it in range(4):                  # patch one-vertex pinch points with a tiny disc until the exported STL is manifold
    mb = solid(black_f, a.depth); mu = solid(blue_f, a.depth)
    bp = bad_points(mb) + bad_points(mu)
    if not bp: break
    print("patching pinch points", bp)
    dab = unary_union([Point(x, y).buffer(0.7) for x, y in bp])
    black_f = unary_union([black_f, dab.difference(blue_f)])
union = unary_union([black_f, blue_f]); whole = solid(union, a.depth)      # one fused watertight solid (for the single STL)
mb.export(OUT / "stl" / "bmw_painter__black.stl"); mu.export(OUT / "stl" / "bmw_painter__blue.stl"); whole.export(OUT / "bmw_painter_298x105.stl")

# ---- validation ----
rep = {}
for n, m in (("black", mb), ("blue", mu), ("all", whole)):
    rep[n] = dict(watertight=bool(m.is_watertight), volume_mm3=round(float(m.volume), 1), triangles=len(m.faces))
rep["bounds_mm"] = (whole.bounds[1] - whole.bounds[0]).round(2).tolist()
rep["z_min_max"] = [round(float(whole.bounds[0][2]), 3), round(float(whole.bounds[1][2]), 3)]
# connectivity of the footprint (shapely): number of separate pieces after union
u2 = unary_union([black_f, blue_f])
rep["footprint_pieces"] = len(u2.geoms) if hasattr(u2, "geoms") else 1
rep["bodies_black"] = len(mb.split(only_watertight=False)); rep["bodies_blue"] = len(mu.split(only_watertight=False))
rep["watertight_parts_black"] = sum(p.is_watertight for p in mb.split(only_watertight=False))
rep["grams_pla_est"] = round(float(whole.volume)*1.24/1000*0.9, 1)
# thin-feature audit on the footprint: area that disappears when opened with a 0.7 / 1.0 / 1.2 mm wide tool
fp = unary_union([black_f, blue_f])
for w in (0.7, 1.0, 1.2):
    op = fp.buffer(-w/2, join_style=1).buffer(w/2, join_style=1)
    rep[f"area_pct_thinner_than_{w}mm"] = round(100*(fp.area-op.area)/fp.area, 2)
json.dump(rep, open(OUT / "validation.json", "w"), indent=1); print(json.dumps(rep, indent=1))

# ---- 3MF (slot 1 black, slot 2 blue) ----
b = whole.bounds; mid = ((b[0][0]+b[1][0])/2, (b[0][1]+b[1][1])/2)
mb3, mu3 = mb.copy(), mu.copy()
for m in (mb3, mu3): m.apply_translation([-mid[0], -mid[1], 0])
tpl = (Path(__file__).resolve().parents[1] / "config" / "bambu_project_4fil_pla.config").read_bytes()
write_bambu_3mf(str(OUT / "bmw_painter_298x105.3mf"), [("black", mb3, 1), ("blue", mu3, 2)], center=(162.5, 110.0), name="bmw_painter",
                project_settings=build_project_settings(tpl, ["#141414", "#1535C8", "#1A1A1A", "#1A1A1A"], (150.0, 235.0, 30.0)))
print("3mf ok")

# ---- STEP (editable CAD) ----
try:
    from build123d import Wire, Face, extrude, Compound, export_step, Vector
    def step_of(geom, path):
        solids = []
        for pg in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            ring = lambda c: Wire.make_polygon([Vector(x, y, 0) for x, y in list(c.coords)[:-1]])
            solids.append(extrude(Face(ring(pg.exterior), [ring(h) for h in pg.interiors]), a.depth))
        export_step(Compound(solids), str(path))
    step_of(black_f, OUT / "bmw_painter_black.step"); step_of(blue_f, OUT / "bmw_painter_blue.step"); print("step ok")
except Exception as e:
    print("STEP skipped:", repr(e)[:300])
