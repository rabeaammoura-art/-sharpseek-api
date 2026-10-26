"""Edits to the teddy body mesh: new smooth heart frame, sealed back hole + bottom cable channel,
deeper smile, paw pads on the feet."""
import numpy as np
import trimesh
from shapely.geometry import Polygon

from heart import X0

FLOOR_Y = 786.0        # old pocket floor
WALL_FRONT_Y = 776.0   # front edge of the heart frame wall
WALL_T = 4.8           # frame wall thickness (outside the pocket outline)
CLEAR_T = 4.4          # old frame removed out to this offset
LEDGE_Y = 782.0        # shell rests on this ledge
LEDGE_W = 1.6          # how far the ledge sticks into the pocket


def boolean(op, meshes):
    return getattr(trimesh.boolean, op)(meshes, engine="manifold")


def prism_xz(poly: Polygon, y0, y1):
    """Extrude a polygon given in world (x, z) along +y from y0 to y1."""
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    v = m.vertices
    w = np.c_[v[:, 0], v[:, 2] + y0, v[:, 1]]
    out = trimesh.Trimesh(w, m.faces[:, ::-1], process=True)
    if out.volume < 0:
        out.invert()
    return out


def new_frame(teddy, heart: Polygon):
    cutter = prism_xz(heart.buffer(CLEAR_T, resolution=32), 764.0, FLOOR_Y)
    wall = prism_xz(heart.buffer(WALL_T, resolution=32).difference(heart), WALL_FRONT_Y, FLOOR_Y + 1.5)
    ledge = prism_xz(heart.buffer(0.4).difference(heart.buffer(-LEDGE_W)), LEDGE_Y, FLOOR_Y + 1.0)
    return boolean("union", [boolean("difference", [teddy, cutter]), wall, ledge])


def seal_back_and_bottom_channel(teddy):
    box = trimesh.creation.box(bounds=[[846, 885, 44], [877, 925, 70]])
    patch = boolean("intersection", [teddy, box])
    plug = patch.convex_hull
    t = boolean("union", [teddy, plug])
    chan = trimesh.creation.cylinder(radius=4.0, height=62.0, sections=64,
                                     transform=trimesh.transformations.translation_matrix([X0, 847.0, 29.0]))
    return boolean("difference", [t, chan])


def _sd_ellipse(px, pz, cx, cz, rx, rz, ang=0.0, n=2.6):
    """Soft 0..1 field for a (super)ellipse: 1 inside, falls to 0 at the edge."""
    c, s = np.cos(ang), np.sin(ang)
    dx, dz = px - cx, pz - cz
    u = (dx * c + dz * s) / rx
    v = (-dx * s + dz * c) / rz
    r = (np.abs(u) ** n + np.abs(v) ** n) ** (1 / n)
    return r


def _pillow(r, edge=0.22):
    """height profile: flat-topped soft pad, r=1 is the outline."""
    t = np.clip((1 - r) / edge, 0, 1)
    return t * t * (3 - 2 * t)


def _dist_to_polyline(px, pz, pts):
    best = np.full(px.shape, 1e9)
    tpar = np.zeros(px.shape)
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        l2 = ab @ ab
        t = np.clip(((px - a[0]) * ab[0] + (pz - a[1]) * ab[1]) / l2, 0, 1)
        d = np.hypot(px - (a[0] + t * ab[0]), pz - (a[1] + t * ab[1]))
        m = d < best
        best[m] = d[m]
        tpar[m] = (L[i] + t[m] * np.sqrt(l2)) / L[-1]
    return best, tpar


def smile_height(px, pz):
    """Positive = cut into the surface (mm)."""
    cut = np.zeros(px.shape)
    # smile arc, same centre as the original, wider and with curled-up ends
    dx = np.linspace(-21, 21, 160)
    ex = np.clip(np.abs(dx) - 17.5, 0, None)
    z = 107.3 + 0.0147 * dx ** 2 + 0.16 * ex ** 2
    arc = np.c_[X0 + dx, z]
    d, t = _dist_to_polyline(px, pz, arc)
    taper = np.sin(np.clip(t, 0, 1) * np.pi) ** 0.6          # shallow at both ends
    w = 1.5
    prof = np.clip(1 - (d / w) ** 2, 0, 1) ** 1.5
    cut = np.maximum(cut, 1.15 * taper * prof)
    # philtrum line from the nose down to the smile
    line = np.c_[[X0, X0], [118.5, 107.5]]
    d2, t2 = _dist_to_polyline(px, pz, line)
    prof2 = np.clip(1 - (d2 / 0.95) ** 2, 0, 1) ** 1.5
    cut = np.maximum(cut, 0.8 * prof2)
    return cut


def paw_height(px, pz):
    """Positive = raised (mm).  Pads on both feet (left built, right mirrored)."""
    h = np.zeros(px.shape)
    cxL, czL = 809.8, 21.5
    for mirror in (False, True):
        x = (2 * X0 - px) if mirror else px
        # main pad: three soft lobes
        lobes = [(cxL, czL - 3.2, 11.4, 7.6), (cxL - 4.2, czL + 1.2, 6.6, 5.4), (cxL + 4.2, czL + 1.2, 6.6, 5.4)]
        rs = np.array([_sd_ellipse(x, pz, cx, cz, rx, rz, 0, 2.0) for cx, cz, rx, rz in lobes])
        r = -np.log(np.exp(-9.0 * rs).sum(0)) / 9.0                  # soft union of the lobes
        h = np.maximum(h, 1.3 * _pillow(r, 0.30))
        for a in np.radians([-42, -14, 14, 42]):
            cx = cxL + 14.5 * np.sin(a)
            cz = czL + 5.5 + 13.2 * np.cos(a)
            toe = _pillow(_sd_ellipse(x, pz, cx, cz, 3.9, 4.9, -a, 2.0), 0.34)
            h = np.maximum(h, 1.3 * toe)
    return h


def carve_details(teddy, max_edge=0.42):
    from refine import refine_zone
    def zone(c):
        x, y, z = c[:, 0], c[:, 1], c[:, 2]
        face = (x > 838) & (x < 885) & (z > 102) & (z < 122) & (y < 800)
        feet = (z > 6) & (z < 46) & (y < 790) & (((x > 795) & (x < 834)) | ((x > 889) & (x < 928)))
        return face | feet
    m = refine_zone(teddy, zone, max_edge)
    nrm = m.vertex_normals
    v = m.vertices.copy()
    px, py, pz = v[:, 0], v[:, 1], v[:, 2]
    wgt = np.clip((-nrm[:, 1] - 0.05) / 0.3, 0, 1) * (py < 800)      # front-facing weight, fades on steep sides
    dy = np.zeros(len(v))                     # + moves toward the viewer (-y)
    face_zone = (wgt > 0) & (px > 835) & (px < 888) & (pz > 100) & (pz < 125)
    dy[face_zone] = -smile_height(px[face_zone], pz[face_zone]) * wgt[face_zone]
    foot_zone = (wgt > 0) & (pz < 52) & ((px < 840) | (px > 883))
    dy[foot_zone] = paw_height(px[foot_zone], pz[foot_zone]) * wgt[foot_zone]
    v[:, 1] -= dy
    return trimesh.Trimesh(v, m.faces, process=True)


def ring_fillet(teddy, outline: Polygon, y_chest=786.0, radius=4.5, dphi=1.2):
    """Concave fillet blending the raised heart ring into the chest, arms and feet (also closes the tiny
    crevices where the ring meets them).  Thin stacked layers placed at equal angles around the fillet arc."""
    yc = y_chest - radius
    phis = np.radians(np.arange(0, 90 + dphi, dphi))
    layers = []
    for a, b in zip(phis[:-1], phis[1:]):
        y0, y1 = yc + radius * np.sin(a), yc + radius * np.sin(b)
        w = radius * (1 - np.cos((a + b) / 2))
        band = outline.buffer(max(w, 0.01), resolution=24).difference(outline.buffer(-0.4, resolution=24))
        layers.append(prism_xz(band, y0, min(y1, y_chest + 0.3) + (0.3 if b >= phis[-1] else 0.0)))
    return boolean("union", [teddy] + layers)
