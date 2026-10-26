"""Smooth heart outline for the teddy pocket / lithophane window.

The outline is recovered from the pocket in the existing teddy STL (section at y=782), low-pass filtered
so every edge is one smooth curve, then made left/right symmetric.  Coordinates are world (x, z) in mm.
"""
import numpy as np
import trimesh
from shapely.affinity import scale
from shapely.geometry import Polygon

X0 = 861.43          # teddy centre line (x)
POCKET_Y = 782.0     # y plane where the old pocket is a clean heart hole
HARMONICS = 22


def _resample(pts, n):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n, endpoint=False)
    return np.c_[np.interp(t, d, pts[:, 0]), np.interp(t, d, pts[:, 1])]


def heart_from_teddy(teddy: trimesh.Trimesh) -> Polygon:
    sec = teddy.section(plane_origin=[0, POCKET_Y, 0], plane_normal=[0, 1, 0])
    best = None
    for loop in sec.discrete:
        w = np.ptp(loop[:, 0])
        if 70 < w < 80 and np.ptp(loop[:, 2]) > 60:      # the heart hole, not the body outline
            best = loop[:, [0, 2]]
    if best is None:
        raise RuntimeError("pocket heart not found in teddy section")
    p = _resample(np.vstack([best, best[:1]]), 2048)
    z = p[:, 0] + 1j * p[:, 1]
    f = np.fft.fft(z)
    k = np.fft.fftfreq(len(z), 1 / len(z))
    f[np.abs(k) > HARMONICS] = 0
    s = np.fft.ifft(f)
    poly = Polygon(np.c_[s.real, s.imag]).buffer(0)
    mirror = scale(poly, xfact=-1, origin=(X0, 0))
    sym = poly.intersection(mirror)
    # re-centre exactly on the teddy axis
    minx, _, maxx, _ = sym.bounds
    return sym.simplify(0.01)


def polar_outline(poly: Polygon, c0, n=1080):
    """Radius of the outline as a function of angle around c0 (heart is star-shaped about c0)."""
    ring = np.array(poly.exterior.coords)[:-1]
    ring = _resample(np.vstack([ring, ring[:1]]), 4096)
    a = np.unwrap(np.arctan2(ring[:, 1] - c0[1], ring[:, 0] - c0[0]))
    if a[-1] < a[0]:                                    # make counter-clockwise
        ring, a = ring[::-1], np.unwrap(np.arctan2(ring[::-1, 1] - c0[1], ring[::-1, 0] - c0[0]))
    a0 = a.min()
    order = np.argsort(a)
    a, ring = a[order], ring[order]
    th = np.linspace(a0, a0 + 2 * np.pi, n, endpoint=False)
    aa = np.r_[a - 2 * np.pi, a, a + 2 * np.pi]
    xx = np.r_[ring[:, 0], ring[:, 0], ring[:, 0]]
    zz = np.r_[ring[:, 1], ring[:, 1], ring[:, 1]]
    bx = np.interp(th, aa, xx)
    bz = np.interp(th, aa, zz)
    return np.c_[bx, bz]
