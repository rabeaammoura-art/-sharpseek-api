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


def _back_plug(teddy, cx=X0, cz=57.5, half=11.0, step=0.25):
    """Solid that fills the cable tunnel at the back.  Its outer face is a polynomial fitted to the surrounding
    back surface, so the patch follows the curvature of the body instead of being a flat disc."""
    g = np.arange(-half, half + step / 2, step)
    GX, GZ = np.meshgrid(cx + g, cz + g, indexing="ij")
    o = np.c_[GX.ravel(), np.full(GX.size, 1000.0), GZ.ravel()]
    loc, ir, _ = teddy.ray.intersects_location(o, np.tile([0, -1.0, 0], (len(o), 1)), multiple_hits=False)
    yt = np.full(GX.size, np.nan)
    yt[ir] = loc[:, 1]
    yt = yt.reshape(GX.shape)
    r = np.hypot(GX - cx, GZ - cz)
    ok = np.isfinite(yt) & (yt > 905) & (r > 7.5) & (r < half)
    dx, dz = (GX - cx)[ok], (GZ - cz)[ok]
    terms = lambda a, b: np.stack([a ** i * b ** k for i in range(5) for k in range(5 - i)], -1)
    coef, *_ = np.linalg.lstsq(terms(dx, dz), yt[ok], rcond=None)
    fit = (terms(GX - cx, GZ - cz) @ coef)
    resid = np.abs(terms(dx, dz) @ coef - yt[ok]).max()
    w = np.clip((r - 8.6) / 1.4, 0, 1)
    w = w * w * (3 - 2 * w)
    true_ok = np.isfinite(yt) & (yt > 905)
    sink = 0.03 * np.clip((r - 6.0) / 2.0, 0, 1)                 # hidden below the true surface outside the hole
    top = np.where(true_ok, fit * (1 - w) + yt * w, fit) - sink
    n = len(g)
    idx = lambda a, b: a * n + b
    top_v = np.c_[GX.ravel(), top.ravel(), GZ.ravel()]
    bot_v = np.c_[GX.ravel(), np.full(GX.size, 872.0), GZ.ravel()]
    V = np.vstack([top_v, bot_v])
    off = n * n
    F = []
    for a in range(n - 1):
        for b in range(n - 1):
            p, q, rr, s_ = idx(a, b), idx(a + 1, b), idx(a + 1, b + 1), idx(a, b + 1)
            F += [[p, s_, rr], [p, rr, q]]                       # top faces point +y
            F += [[p + off, q + off, rr + off], [p + off, rr + off, s_ + off]]
    for a in range(n - 1):
        for edge in ((a, 0, a + 1, 0), (a, n - 1, a + 1, n - 1)):
            pass
    def wall(i0, i1):
        F.extend([[i0, i1, i1 + off], [i0, i1 + off, i0 + off]])
    for a in range(n - 1):
        wall(idx(a + 1, 0), idx(a, 0)); wall(idx(a, n - 1), idx(a + 1, n - 1))
        wall(idx(0, a), idx(0, a + 1)); wall(idx(n - 1, a + 1), idx(n - 1, a))
    m = trimesh.Trimesh(V, np.array(F), process=True)
    m.fix_normals()
    if m.volume < 0:
        m.invert()
    return m, resid


def retriangulate_back_patch(mesh, cx=X0, cz=57.5, r_cut=11.5, spacing=0.45):
    """Replace the boolean seam area on the back by a clean triangulation lying exactly on the fitted smooth surface.
    The boolean leaves sliver triangles (garbage normals -> a visible ring); here the patch is cut out and rebuilt."""
    from scipy.spatial import Delaunay
    from shapely.geometry import Polygon as _P, Point
    V, F = mesh.vertices, mesh.faces
    c = V[F].mean(1)
    rc = np.hypot(c[:, 0] - cx, c[:, 2] - cz)
    sel = (c[:, 1] > 908) & (rc < r_cut)
    # boundary loop of the selected patch
    e = np.sort(F[sel][:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
    u, cnt = np.unique(e, axis=0, return_counts=True)
    bedges = u[cnt == 1]
    nxt = {}
    for a, b in bedges:
        nxt.setdefault(a, []).append(b); nxt.setdefault(b, []).append(a)
    start = bedges[0][0]
    loop = [start]
    prev, cur = None, start
    while True:
        cand = [x for x in nxt[cur] if x != prev]
        nx = cand[0] if cand else None
        if nx is None or nx == start:
            break
        loop.append(nx); prev, cur = cur, nx
    if len(loop) != len(bedges):
        raise RuntimeError(f"back patch boundary is not a single loop ({len(loop)} of {len(bedges)})")
    loop = np.array(loop)
    bp = V[loop]
    poly = _P(bp[:, [0, 2]]).buffer(0)
    # smooth reference surface from the ring just outside the patch
    r = np.hypot(V[:, 0] - cx, V[:, 2] - cz)
    ref = (V[:, 1] > 908) & (r > r_cut + 1.0) & (r < r_cut + 12)
    terms = lambda a, b: np.stack([a ** i * b ** k for i in range(5) for k in range(5 - i)], -1)
    coef, *_ = np.linalg.lstsq(terms(V[ref, 0] - cx, V[ref, 2] - cz), V[ref, 1], rcond=None)
    gx = np.arange(cx - r_cut, cx + r_cut, spacing)
    gz = np.arange(cz - r_cut, cz + r_cut, spacing * np.sqrt(3) / 2)
    pts = []
    for k, z in enumerate(gz):
        for x in gx + (spacing / 2 if k % 2 else 0):
            pts.append((x, z))
    pts = np.array(pts)
    inner = poly.buffer(-0.35)
    keep = np.array([inner.contains(Point(p)) for p in pts])
    ip = pts[keep]
    iy = terms(ip[:, 0] - cx, ip[:, 1] - cz) @ coef
    new_v = np.c_[ip[:, 0], iy, ip[:, 1]]
    allv = np.vstack([V, new_v])
    idx_xz = np.vstack([bp[:, [0, 2]], ip])
    idx_id = np.r_[loop, len(V) + np.arange(len(ip))]
    import triangle
    nb = len(bp)
    seg = np.c_[np.arange(nb), (np.arange(nb) + 1) % nb]
    res = triangle.triangulate({"vertices": idx_xz, "segments": seg}, "p")      # constrained: keeps every boundary edge
    assert len(res["vertices"]) == len(idx_xz), "triangle added points"
    tri = res["triangles"]
    nf = idx_id[tri]
    # orient so normals point +y (away from the body)
    p0, p1, p2 = allv[nf[:, 0]], allv[nf[:, 1]], allv[nf[:, 2]]
    nrm = np.cross(p1 - p0, p2 - p0)
    flip = nrm[:, 1] < 0
    nf[flip] = nf[flip][:, ::-1]
    out = trimesh.Trimesh(allv, np.vstack([F[~sel], nf]), process=True)
    return out


def seal_back_and_bottom_channel(teddy):
    plug, resid = _back_plug(teddy)
    print('back plug fit residual (mm):', round(float(resid), 3), 'watertight', plug.is_watertight)
    t = retriangulate_back_patch(boolean("union", [teddy, plug]))
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
