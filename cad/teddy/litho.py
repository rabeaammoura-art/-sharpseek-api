"""Domed heart lithophane shell, relief taken from a photo.

Surface is parametrised radially (centre -> smooth heart outline), so the outline is one smooth curve and
there are no stair-steps at the edge.  Front (viewer side, -y) carries the relief; the back is a smooth dome.
Bright pixel = thin = lets light through.
"""
import numpy as np
import trimesh
from PIL import Image, ImageFilter, ImageOps
from scipy.ndimage import map_coordinates

from heart import polar_outline

Y_RIM = 782.0          # back-surface y at the outline
DOME_H = 24.0          # how far the back surface bulges toward the viewer at the centre
T_MIN, T_MAX = 0.6, 2.5  # relief thickness (mm, along y): white .. black
T_RIM = 3.0            # rigid rim
RIM_BAND = (0.6, 2.6)  # mm from outline over which thickness blends into the rim value


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def load_photo(path, crop_cx, crop_w, crop_cy, aspect):
    im = Image.open(path).convert("L")
    im = ImageOps.autocontrast(im, cutoff=1.5)
    h = crop_w / aspect
    box = (crop_cx - crop_w / 2, crop_cy - h / 2, crop_cx + crop_w / 2, crop_cy + h / 2)
    im = im.crop(tuple(int(round(v)) for v in box)).filter(ImageFilter.GaussianBlur(1.1))
    return np.asarray(im, dtype=float) / 255.0


def build(heart_poly, photo_path, c0, n_theta=1080, n_s=120, clearance=0.25, crop=(360, 700, 640), gamma=1.0):
    shell_poly = heart_poly.buffer(-clearance)
    B = polar_outline(shell_poly, c0, n_theta)                      # (n_theta, 2) world x,z
    minx, minz, maxx, maxz = shell_poly.bounds
    photo = load_photo(photo_path, crop[0], crop[1], crop[2], (maxx - minx) / (maxz - minz))
    ph, pw = photo.shape

    s = np.linspace(0, 1, n_s + 1)[:, None]                         # (n_s+1,1)
    X = c0[0] + s * (B[None, :, 0] - c0[0])
    Z = c0[1] + s * (B[None, :, 1] - c0[1])
    yb = Y_RIM - DOME_H * (1 - s ** 2) * np.ones_like(X)
    Pb = np.stack([X, yb, Z], -1)                                   # (n_s+1, n_theta, 3) back surface

    n = np.zeros_like(Pb); n[..., 1] = -1             # relief is cut straight toward the viewer: the outline stays put

    # photo sample -> thickness
    u = (X - minx) / (maxx - minx) * (pw - 1)
    v = (maxz - Z) / (maxz - minz) * (ph - 1)
    L = map_coordinates(photo, [v, u], order=1, mode="nearest")
    t = T_MIN + (1 - L) ** gamma * (T_MAX - T_MIN)
    edge_mm = (1 - s) * np.linalg.norm(B - np.array(c0), axis=1)[None, :]
    w = smoothstep(RIM_BAND[1], RIM_BAND[0], edge_mm)               # 1 at the rim
    t = t * (1 - w) + T_RIM * w
    Pf = Pb + n * t[..., None]

    # mesh: vertex 0 = back centre, 1 = front centre, then rings 1..n_s of back, then of front
    nr = n_s * n_theta
    ring_b = lambda k, j: 2 + (k - 1) * n_theta + (j % n_theta)
    ring_f = lambda k, j: 2 + nr + (k - 1) * n_theta + (j % n_theta)
    V = np.vstack([Pb[0, 0], Pf[0, 0], Pb[1:].reshape(-1, 3), Pf[1:].reshape(-1, 3)])
    F = []
    j = np.arange(n_theta)
    # centre fans
    F += list(np.c_[np.zeros(n_theta, int), ring_b(1, j + 1), ring_b(1, j)])          # back faces point +y
    F += list(np.c_[np.ones(n_theta, int), ring_f(1, j), ring_f(1, j + 1)])           # front faces point -y
    for k in range(1, n_s):
        a, b, c, d = ring_b(k, j), ring_b(k, j + 1), ring_b(k + 1, j + 1), ring_b(k + 1, j)
        F += list(np.c_[a, b, c]) + list(np.c_[a, c, d])
        a, b, c, d = ring_f(k, j), ring_f(k, j + 1), ring_f(k + 1, j + 1), ring_f(k + 1, j)
        F += list(np.c_[a, c, b]) + list(np.c_[a, d, c])
    # rim wall joining back and front at the outline
    a, b = ring_b(n_s, j), ring_b(n_s, j + 1)
    c, d = ring_f(n_s, j + 1), ring_f(n_s, j)
    F += list(np.c_[a, c, b]) + list(np.c_[a, d, c])
    m = trimesh.Trimesh(V, np.array(F), process=True)
    m.fix_normals()
    if m.volume < 0:
        m.invert()
    return m, shell_poly
