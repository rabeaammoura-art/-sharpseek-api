"""Clearance test coupon: 5 half-lap + pin pairs (clearance 0.10..0.30 mm).
Each pair = A (tongue, printed FRONT FACE DOWN so the tongue sits on the bed) and B (ledge + pin, back down).
Dots (holes through the body): 1 dot = 0.10 ... 5 dots = 0.30.  python make_joint_test.py"""
import trimesh, numpy as np
from shapely.geometry import box, Point
from shapely.ops import unary_union
T, H, L, W = 3.0, 1.5, 8.0, 7.0
PD, PH, HD = 2.4, 1.0, 1.1        # pin dia, pin height, hole depth
CL = [0.10, 0.15, 0.20, 0.25, 0.30]
def ext(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0); m.apply_translation([0, 0, z0]); return m
def pair(c, n, y0):
    hw = W / 2
    # A (printed flipped: front down): body 0..T until x=0, tongue z 0..H for x 0..L, blind hole from top
    dots = [Point(-8.5 + 2.2 * i, 0).buffer(0.6, 16) for i in range(n)]
    body = box(-10, -hw, 0, hw).difference(unary_union(dots))
    parts = [ext(body, 0, T)]
    tongue = box(0, -hw, L, hw)
    hole = Point(L / 2, 0).buffer(PD / 2 + c, 24)
    parts.append(ext(tongue, 0, H - HD))              # skin 0..0.3 under the hole
    parts.append(ext(tongue.difference(hole), H - HD, H))    # 0.3..1.5 with the hole
    A = trimesh.boolean.union(parts, engine='manifold')
    # B (back down): upper part from x=L+c, ledge z 0..H from x=c, pin on the ledge
    Bup = box(L + c, -hw, L + c + 10, hw)
    Bl = box(c, -hw, L + c, hw)
    pin = Point(L / 2, 0).buffer(PD / 2, 24)
    B = trimesh.boolean.union([ext(Bup, 0, T), ext(Bl, 0, H), ext(pin, H, H + PH)], engine='manifold')
    A.apply_translation([-0, y0, 0]); B.apply_translation([26, y0, 0])
    return A, B
ms = []
for i, c in enumerate(CL):
    ms += list(pair(c, i + 1, i * 12))
mesh = trimesh.util.concatenate(ms)
mesh.apply_translation([-mesh.bounds[0][0], -mesh.bounds[0][1], 0])
mesh.export('joint_test/joint_clearance_test.stl')
print(mesh.extents.round(1), len(mesh.faces))
