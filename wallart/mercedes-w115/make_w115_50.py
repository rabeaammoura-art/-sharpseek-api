"""W115 50 cm wall art: adds the number plate (white floor + black raised digits) and the glue-free half-lap joints.
  python make_w115_50.py [10-38709]          (or env PLATE_NUMBER; default is a dummy so the public repo carries no real number)
Input : stl/mb_small_1x1.stl (front, has the plate) and stl/mb_small_2x1.stl (rear)
Output: out_50/ (git-ignored):
  front_black.stl   art + plate frame + digits + ledges + pins  -> print FRONT FACE UP (as is)
  front_white.stl   plate floor 1 mm                            -> same position, 2nd colour (white)
  rear.stl          rear piece, already flipped                 -> print FRONT FACE DOWN (as is)
Joint = half-lap (8 mm) + 2.4 mm pin in a 2.6 mm hole (clearance 0.10 = the coupon pair with 1 dot that fitted).
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
PLATE = dict(W=50.0, H=11.0, cx=68.0, cy=49.0, slope=-0.068, frame=1.2, floor=1.0)

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

# ---------- plate ----------
P = PLATE; W, Hh = P['W'], P['H']
outer = place(box(0, 0, W, Hh), P)
inner = place(box(P['frame'], P['frame'], W - P['frame'], Hh - P['frame']), P)
ring = outer.difference(inner)
digits = fit(text_geom(NUMBER, 6.0), W * 0.36, 0, w=W * 0.58)
digits = affinity.translate(digits, 0, (Hh - (digits.bounds[3] - digits.bounds[1])) / 2 - digits.bounds[1])
ar = fit(text_geom('الاردن', 2.6), 3.0, 5.4, w=7.0)
en = fit(text_geom('JORDAN', 1.6), 3.0, 2.2, w=7.0)
marks = unary_union([place(digits, P), place(ar, P), place(en, P)]).intersection(inner)
black_art = A.difference(outer).union(ring)

# ---------- joints ----------
ledges, pins, pockets, holes = [], [], [], []
for yc, w in JOINTS:
    f = Bp.intersection(box(SEAM, yc - w / 2, SEAM + L, yc + w / 2))
    ledges.append(f)
    pockets.append(f.buffer(C, join_style=2).intersection(box(SEAM, -1e3, 1e3, 1e3)))
    pins.append(Point(SEAM + L / 2, yc).buffer(PD / 2, 24))
    holes.append(Point(SEAM + L / 2, yc).buffer(PD / 2 + C, 24))
ledge = unary_union(ledges); pocket = unary_union(pockets)

# ---------- front piece (print front face up) ----------
front = union(ext(black_art, 0, T) + ext(marks, P['floor'], T) + ext(ledge.difference(black_art), 0, H)
              + [m for g in pins for m in ext(g, H, H + PH)])
white = union(ext(inner, 0, P['floor']))
# ---------- rear piece: assembled (back z=0), then flipped so the FRONT face is on the bed ----------
back_half = ext(Bp.difference(pocket), 0, H)
front_low = ext(Bp.difference(unary_union(holes)), H, H + HD)
front_up = ext(Bp, H + HD, T)
rear = union(back_half + front_low + front_up)
rear.apply_transform(np.diag([-1.0, 1.0, -1.0, 1.0]))   # turn the part over (180 deg about y): front face down
rear.apply_translation([2 * SEAM, 0, T])               # back to x 0..250, z 0..3
for n, m in (('front_black', front), ('front_white', white), ('rear', rear)):
    m.export(os.path.join(OUT, n + '.stl'))
    print(n, m.extents.round(1), 'watertight', m.is_watertight, 'z', round(m.bounds[0][2], 2), round(m.bounds[1][2], 2))
