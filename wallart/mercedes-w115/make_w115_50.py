"""W115 50 cm wall art: number plate (separate insert, white floor + black raised digits) and glue-free half-lap joints.
  python make_w115_50.py [NUMBER]       (or env PLATE_NUMBER; default is a dummy so the public repo carries no real number)
Input : stl/mb_small_1x1.stl (front) and stl/mb_small_2x1.stl (rear)
Output: out_50/ (git-ignored)
  front_down.3mf     front piece, FRONT FACE DOWN, PETG, supports in PETG too (z gap 0.25) under the 3 ledges/pins
  rear.3mf           rear piece, FRONT FACE DOWN, PETG
  plate_insert.3mf   the number plate, printed alone, face up, black digits + white floor (PETG)
  (same parts as STL)
Joint = half-lap (8 mm) + 2.4 mm pin in a 2.6 mm hole (clearance 0.10 = the coupon pair with 1 dot that fitted).
The plate insert drops in from the back: a 0.7 mm flange sits in a pocket behind the 1.8 mm front frame.
"""
import sys, os, numpy as np, trimesh
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

NUMBER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('PLATE_NUMBER', '00-00000')
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, 'out_50'); os.makedirs(OUT, exist_ok=True)
T, H = 3.0, 1.5                     # thickness, half
C, L, PD, PH, HD = 0.10, 8.0, 2.4, 1.0, 1.1
SEAM = 250.0
JOINTS = [(30.0, 5.0), (126.0, 6.0), (167.2, 5.0)]     # (y, tongue width) chosen where both strokes cover the 8 mm lap
PLATE = dict(W=50.0, H=11.0, cx=68.0, cy=49.0, slope=-0.068, frame=1.8, floor=1.0, flange=0.7)

def section(name):
    m = trimesh.load(os.path.join(HERE, 'stl', name + '.stl'))
    s = m.section(plane_origin=[0, 0, 1.5], plane_normal=[0, 0, 1])
    p, _ = s.to_2D(to_2D=np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.5], [0, 0, 0, 1]]))
    return unary_union(list(p.polygons_full)).buffer(0)

def ext(g, z0, z1):
    out = []
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.is_empty or p.area < 1e-4: continue
        m = trimesh.creation.extrude_polygon(p, z1 - z0); m.apply_translation([0, 0, z0]); out.append(m)
    return out

def union(meshes):
    return trimesh.boolean.union(meshes, engine='manifold') if len(meshes) > 1 else meshes[0]

def text_geom(s, size, bold=True):
    tp = TextPath((0, 0), s, size=size, prop=FontProperties(family='DejaVu Sans', weight='bold' if bold else 'normal'))
    g = None
    from shapely.geometry import Polygon
    for ring in tp.to_polygons(closed_only=True):
        pg = Polygon(ring).buffer(0)
        g = pg if g is None else g.symmetric_difference(pg)
    return g

def place(g, P):   # plate-local (0..W,0..H) -> piece coordinates (shear follows the bumper slope)
    return affinity.affine_transform(g, [1, 0, P['slope'], 1, P['cx'] - P['W'] / 2, P['cy'] - P['H'] / 2 - P['slope'] * P['W'] / 2])

def fit(g, x0, y0, w=None, h=None):   # scale to width (and/or height) and put its lower-left at x0,y0
    b = g.bounds; sx = (w / (b[2] - b[0])) if w else 1.0; sy = (h / (b[3] - b[1])) if h else sx
    g = affinity.scale(g, sx, sy, origin=(b[0], b[1])); b = g.bounds
    return affinity.translate(g, x0 - b[0], y0 - b[1])

A = section('mb_small_1x1'); Bp = affinity.translate(section('mb_small_2x1'), SEAM, 0)   # rear in the front piece's coordinates

# ---------- plate: the front piece keeps only the frame + an opening; the number lives on a separate insert ----------
P = PLATE; W, Hh = P['W'], P['H']
outer = place(box(0, 0, W, Hh), P)
inner = place(box(P['frame'], P['frame'], W - P['frame'], Hh - P['frame']), P)      # opening / insert footprint
ring = outer.difference(inner)
digits = fit(text_geom(NUMBER, 6.0), W * 0.34, 0, w=W * 0.58)
digits = affinity.translate(digits, 0, (Hh - (digits.bounds[3] - digits.bounds[1])) / 2 - digits.bounds[1])
ar = fit(text_geom('الاردن', 2.4), 3.6, 5.2, w=6.6)
en = fit(text_geom('JORDAN', 1.5), 3.6, 3.0, w=6.6)
marks = unary_union([place(digits, P), place(ar, P), place(en, P)]).intersection(inner)
black_art = A.difference(outer).union(ring)
pocket_plate = inner.buffer(P['flange'] + C, join_style=2)            # back half: room for the insert's flange
flange = inner.buffer(P['flange'], join_style=2).difference(inner)

# ---------- joints ----------
ledges, pins, pockets, holes = [], [], [], []
for yc, w in JOINTS:
    f = Bp.intersection(box(SEAM, yc - w / 2, SEAM + L, yc + w / 2))
    ledges.append(f)
    pockets.append(f.buffer(C, join_style=2).intersection(box(SEAM, -1e3, 1e3, 1e3)))
    pins.append(Point(SEAM + L / 2, yc).buffer(PD / 2, 24))
    holes.append(Point(SEAM + L / 2, yc).buffer(PD / 2 + C, 24))
ledge = unary_union(ledges); pocket = unary_union(pockets)

# ---------- front piece (assembled: back z=0, front z=3), then turned over: FRONT FACE DOWN ----------
front = union(ext(black_art, H, T) + ext(black_art.difference(pocket_plate), 0, H) + ext(ledge.difference(black_art), 0, H)
              + [m for g in pins for m in ext(g, H, H + PH)])
insert_white = union(ext(inner, 0, P['floor']) + ext(flange, 0, H))                # floor 1 mm + flange (back half)
insert_black = union(ext(marks, P['floor'], T))                                    # raised digits to 3 mm
front_print = front.copy(); front_print.apply_transform(np.diag([-1.0, 1.0, -1.0, 1.0])); front_print.apply_translation([front.bounds[1][0], 0, T])
# ---------- rear piece: assembled (back z=0), then flipped so the FRONT face is on the bed ----------
back_half = ext(Bp.difference(pocket), 0, H)
front_low = ext(Bp.difference(unary_union(holes)), H, H + HD)
front_up = ext(Bp, H + HD, T)
rear = union(back_half + front_low + front_up)
rear.apply_transform(np.diag([-1.0, 1.0, -1.0, 1.0]))   # turn the part over (180 deg about y): front face down
rear.apply_translation([2 * SEAM, 0, T])               # back to x 0..250, z 0..3
for n, m in (('front_down', front_print), ('plate_white', insert_white), ('plate_black', insert_black), ('rear', rear)):
    m.export(os.path.join(OUT, n + '.stl'))
    print(n, m.extents.round(1), 'watertight', m.is_watertight, 'z', round(m.bounds[0][2], 2), round(m.bounds[1][2], 2))

# ---------- 3MF (Bambu Studio, H2D) ----------
import json
sys.path.insert(0, os.path.join(HERE, '..', '..', 'cad'))
from threemf import build_project_settings, write_bambu_3mf
from pathlib import Path
CFG = Path(HERE) / '..' / '..' / 'cad' / 'config'
petg = json.loads((CFG / 'bambu_project_4fil_petg.config').read_bytes()); pla = json.loads((CFG / 'bambu_project_4fil_pla.config').read_bytes())
def with_pla_slot2():
    """PETG in slot 1, PLA in slot 2 (the support material): copy the PLA values of every per-filament setting into slot 2."""
    cfg = json.loads(json.dumps(petg))
    for k, v in cfg.items():
        if isinstance(v, list) and len(v) == 4 and isinstance(pla.get(k), list) and len(pla[k]) == 4:
            cfg[k][1] = pla[k][1]
    return json.dumps(cfg).encode()
def centred(m):
    m = m.copy(); c = m.bounds.mean(axis=0); m.apply_translation([-c[0], -c[1], 0]); return m, c
X0, Y0 = 4.0, 160.0
fp, c = centred(front_print)
ps = json.loads(build_project_settings(json.dumps(petg).encode(), ['#000000'] * 4, None))        # one material: PETG supports too (no PETG/PLA swaps)
ps.update(enable_support='1', support_type='normal(auto)', support_on_build_plate_only='1', support_filament='0',
          support_interface_filament='0', support_top_z_distance='0.25')
write_bambu_3mf(os.path.join(OUT, 'front_down.3mf'), [('front', fp, 1)], center=(X0 + front_print.extents[0] / 2, Y0), name='W115_front_50', project_settings=json.dumps(ps))
rr, _ = centred(rear)
write_bambu_3mf(os.path.join(OUT, 'rear.3mf'), [('rear', rr, 1)], center=(4 + rear.extents[0] / 2, Y0), name='W115_rear_50',
                project_settings=build_project_settings(petg and json.dumps(petg).encode(), ['#000000'] * 4, None))
cb, c3 = centred(insert_black); cw = insert_white.copy(); cw.apply_translation([-c3[0], -c3[1], 0])
write_bambu_3mf(os.path.join(OUT, 'plate_insert.3mf'), [('digits_black', cb, 1), ('floor_white', cw, 2)], center=(100.0, 160.0), name='W115_plate_insert',
                project_settings=build_project_settings(json.dumps(petg).encode(), ['#000000', '#FFFFFF', '#000000', '#000000'], (140.0, 120, 14)))
print('3mf written')
