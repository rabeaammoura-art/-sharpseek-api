"""Seam test coupons for the 45 degree scarf joint (both pieces printed FRONT FACE DOWN, no supports).
 pair A: scarf alone   |   pair B: scarf + 2 holes in the back for a splice plate (plate printed flat with 2 pins)
 python make_scarf_test.py  -> out_50/test_scarf.3mf (git-ignored)
Real strokes of the 50 cm art around y 22-70 of the seam (x=250)."""
import os, sys, json, numpy as np, trimesh
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely import affinity
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out_50'); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'cad'))
from threemf import build_project_settings, write_bambu_3mf
T, LAYER, G = 3.0, 0.2, 0.10            # thickness, layer height, seam gap (measured in x)
RUN, TIP = 0.8, 0.4                       # half run of the sloped face (rise 2.2 over run 1.6 = 36 deg from vertical: safer than 45), flat tip at both ends
XS = 250.0; Y0, Y1 = 22.0, 70.0; W = 20.0 # window of the seam used for the coupon
HOLE, HOLE_D, HOLE_Z, PIN_D, PIN_H, PLATE_T = 2.6, 2.6, 1.5, 2.4, 1.2, 1.2
PINS_X, PIN_Y = (-4.5, 4.5), 30.0         # splice holes: 4.5 mm each side of the seam, on the 5 mm stroke at y=30

def section(name):
    m = trimesh.load(os.path.join(HERE, 'stl', name + '.stl'))
    s = m.section(plane_origin=[0, 0, 1.5], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.5], [0, 0, 0, 1]]))
    return unary_union(list(p.polygons_full)).buffer(0)
A = section('mb_small_1x1'); B = affinity.translate(section('mb_small_2x1'), XS, 0)

def wedge(front):
    """cutting solid: the 45 degree scarf profile (x, z) extruded along y.  z=0 back face, z=3 front face."""
    from shapely.geometry import Polygon
    if front:   # front piece: ends further right at the front face
        prof = [(XS - W - 2, 0), (XS - RUN, 0), (XS - RUN, TIP), (XS + RUN, T - TIP), (XS + RUN, T), (XS - W - 2, T)]
    else:       # rear piece: mirrored profile plus the seam gap
        prof = [(XS - RUN + G, 0), (XS + W + 2, 0), (XS + W + 2, T), (XS + RUN + G, T), (XS + RUN + G, T - TIP), (XS - RUN + G, TIP)]
    m = trimesh.creation.extrude_polygon(Polygon(prof), Y1 - Y0)
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, Y0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    if m.volume < 0: m.invert()
    return m

def build(piece, front, holes):
    win = box(XS - W - 2, Y0, XS + W + 2, Y1)
    solids = []
    for q in (lambda g: g.geoms if hasattr(g, 'geoms') else [g])(piece.intersection(win)):
        if q.area > 1e-3: solids.append(trimesh.creation.extrude_polygon(q, T))
    body = trimesh.boolean.union(solids, engine='manifold')
    body = trimesh.boolean.intersection([body, wedge(front)], engine='manifold')
    if holes:
        cyl = []
        for px in PINS_X:
            c = trimesh.creation.cylinder(radius=HOLE_D / 2, height=HOLE_Z, sections=32); c.apply_translation([XS + px, PIN_Y, HOLE_Z / 2 - 0.0]); cyl.append(c)
        body = trimesh.boolean.difference([body] + cyl, engine='manifold')
    return body

def print_pose(m, x, y):          # front face down: turn over about y, then put the lower-left corner at (x, y)
    m = m.copy(); m.apply_transform(np.diag([-1.0, 1.0, -1.0, 1.0])); m.apply_translation([0, 0, T])
    b = m.bounds; m.apply_translation([x - b[0][0], y - Y0, 0]); return m   # common y shift keeps both halves aligned

parts = []
for tag, holes, y in (('A_scarf', False, 0.0), ('B_scarf_holes', True, 58.0)):
    rear = print_pose(build(B, False, holes), 0.0, y); front = print_pose(build(A, True, holes), rear.bounds[1][0] + 12.0, y)
    parts += [(tag + '_rear', rear, 1), (tag + '_front', front, 1)]
# splice plate (printed flat, pins up)
plate = trimesh.creation.box([18.0, 5.5, PLATE_T]); plate.apply_translation([9.0, 2.75, PLATE_T / 2])
pins = [trimesh.creation.cylinder(radius=PIN_D / 2, height=PIN_H, sections=24) for _ in PINS_X]
for p, px in zip(pins, PINS_X): p.apply_translation([9.0 + px, 2.75, PLATE_T + PIN_H / 2 - 0.01])
plate = trimesh.boolean.union([plate] + pins, engine='manifold'); plate.apply_translation([60.0, 58.0, 0])
parts.append(('splice_plate', plate, 1))
allm = trimesh.util.concatenate([m for _, m, _ in parts]); c = allm.bounds.mean(axis=0); ext = allm.extents
for n, m, _ in parts: m.export(os.path.join(OUT, 'test_' + n + '.stl'))
cen = [(n, (lambda mm: (mm.apply_translation([-c[0], -c[1], 0]), mm)[1])(m.copy()), s) for n, m, s in parts]
petg = json.dumps(json.loads(open(os.path.join(HERE, '..', '..', 'cad', 'config', 'bambu_project_4fil_petg.config'), 'rb').read())).encode()
write_bambu_3mf(os.path.join(OUT, 'test_scarf.3mf'), cen, center=(160.0, 160.0), name='W115_scarf_test',
                project_settings=build_project_settings(petg, ['#000000'] * 4, None))
print('extents', ext.round(1), [(n, m.extents.round(1).tolist()) for n, m, _ in parts])
