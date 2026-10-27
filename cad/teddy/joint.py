"""v4: removable lithophane joint (labyrinth flange + C-lip + snap tabs), finger notch, slit fill.

All shapes are described in the world (x, z) plane and extruded along y.  y grows toward the back of the bear.
Layout across the rim (section, x = outward->inward, y grows to the back):

    ring lip (teddy, y 774..)      lithophane tongue (y 774..778.75) in the notch
    teddy FLANGE   y 779..783, 7.5 mm long, 4 mm thick, runs all around inside the pocket wall
    litho BRIDGE   y 775.2..778.75 over the flange, litho SKIRT wraps the flange end down to y 785.6
    snap tabs      4 cantilevers cut into the skirt, barbs hook behind the flange rear face (y 783)
"""
import numpy as np
import trimesh
from shapely.affinity import rotate
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely.ops import unary_union

from teddy_edit import prism_xz, boolean

C = 0.25                 # radial / axial clearance
FL_Y0, FL_Y1 = 779.0, 783.0
FL_LEN = 7.5             # flange length measured inward from the pocket wall
SK_GAP = 0.30            # gap between flange end and skirt
SK_T = 2.3
BR_Y0, BR_Y1 = 775.2, 779.0 - C
SK_Y1 = 785.6
LIP_FRONT_Y = 774.0


def pocket_polys(teddy):
    """H0 = pocket inner wall (y>=779), P_notch = lip inner outline (y 774..779)."""
    from heart import heart_from_teddy
    H0 = heart_from_teddy(teddy)
    s = teddy.section(plane_origin=[0, 776.4, 0], plane_normal=[0, 1, 0])
    cand = [Polygon(l[:, [0, 2]]).buffer(0) for l in s.discrete if len(l) > 20]
    cand = [p for p in cand if 70 < (p.bounds[2] - p.bounds[0]) < 85 and 60 < (p.bounds[3] - p.bounds[1]) < 75]
    P = max(cand, key=lambda p: p.area) if cand else None
    return H0, P


def flange_solid(H0):
    ring = H0.buffer(0.6, resolution=32).difference(H0.buffer(-FL_LEN, resolution=32))
    return prism_xz(ring, FL_Y0, FL_Y1)


def notch_cutter(P_notch, x0=861.43, r=4.0):
    zc = max(c[1] for c in P_notch.exterior.coords if abs(c[0] - x0) < 0.3) + 1.2
    cyl = trimesh.creation.cylinder(radius=r, height=4.4, sections=48)
    # cylinder axis along z by default -> rotate to y
    cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    cyl.apply_translation([x0, LIP_FRONT_Y - 0.4 + 2.2, zc])
    return cyl, zc


def litho_joint_parts(H0, P_notch):
    """Polygons for the new litho rim: tongue (outer ring), bridge, skirt."""
    tongue_out = P_notch.buffer(-C, resolution=32)
    tongue = tongue_out.difference(H0)
    sk_in = H0.buffer(-(FL_LEN + SK_GAP), resolution=32)
    sk_out = H0.buffer(-(FL_LEN + SK_GAP + SK_T), resolution=32)
    bridge = H0.buffer(0.02, resolution=32).difference(sk_out)
    skirt = sk_in.difference(sk_out)
    return tongue, bridge, skirt, sk_in, sk_out


def _frame(poly_line, theta_deg, c0):
    """Point on `poly_line` (closed LineString) along the ray from c0 at angle theta -> (point, tangent, outward-normal)."""
    th = np.radians(theta_deg)
    far = (c0[0] + 200 * np.cos(th), c0[1] + 200 * np.sin(th))
    inter = poly_line.intersection(LineString([c0, far]))
    pts = [inter] if inter.geom_type == 'Point' else list(inter.geoms)
    p = max(pts, key=lambda q: np.hypot(q.x - c0[0], q.y - c0[1]))
    d = poly_line.project(p)
    a = poly_line.interpolate(max(d - 0.8, 0))
    b = poly_line.interpolate(d + 0.8)
    t = np.array([b.x - a.x, b.y - a.y]); t /= np.linalg.norm(t)
    n = np.array([t[1], -t[0]])
    if np.dot(n, [p.x - c0[0], p.y - c0[1]]) < 0:
        n = -n
    return (p.x, p.y), t, n


def local_prism(poly_yr, u0, u1, origin, t, n):
    """Extrude polygon given in (y, r) over u in [u0, u1]; map to world: x = ox+u*tx+r*nx, z = oz+u*tz+r*nz."""
    m = trimesh.creation.extrude_polygon(Polygon(poly_yr), u1 - u0)     # local: X=y, Y=r, Z=u
    v = m.vertices
    u = v[:, 2] + u0
    r = v[:, 1]
    y = v[:, 0]
    w = np.c_[origin[0] + u * t[0] + r * n[0], y, origin[1] + u * t[1] + r * n[1]]
    out = trimesh.Trimesh(w, m.faces, process=True)
    out.fix_normals()
    if out.volume < 0:
        out.invert()
    return out


TAB_ANGLES = (0.0, 180.0, 58.0, 122.0)       # right flank, left flank, upper lobes (about the heart centre)
TAB_HALF = 6.0                               # half width of a tab
SLOT_W = 1.2


def snap_tabs(skirt_mid_line, c0):
    """Returns (cutters, barbs): slots + thinning cut out of the skirt, wedge barbs added on its outer face."""
    cut, add = [], []
    for ang in TAB_ANGLES:
        p, t, n = _frame(skirt_mid_line, ang, c0)          # n points outward = toward the pocket wall
        # slots either side of the tab, through the whole skirt thickness, from y=776.2 to the rear end
        for s in (-1, 1):
            u0 = s * TAB_HALF if s > 0 else -TAB_HALF - SLOT_W
            u1 = u0 + SLOT_W
            cut.append(local_prism([(776.2, -3.2), (786.5, -3.2), (786.5, 3.2), (776.2, 3.2)], u0, u1, p, t, n))
        # thin the tab from the inside (leave 1.4 mm) so it can flex
        cut.append(local_prism([(777.0, -1.4), (786.5, -1.4), (786.5, -SK_T / 2 + 0.9), (777.0, -SK_T / 2 + 0.9)],
                               -TAB_HALF, TAB_HALF, p, t, n))
        # wedge barb on the outer face, behind the flange rear face (y = 783)
        ro = SK_T / 2
        add.append(local_prism([(783.05, ro - 0.05), (783.75, ro + 0.7), (785.2, ro + 0.7), (785.6, ro - 0.05)],
                               -TAB_HALF + 0.6, TAB_HALF - 0.6, p, t, n))
    return cut, add
