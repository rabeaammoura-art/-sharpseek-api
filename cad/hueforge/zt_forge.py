"""ZT-Forge: image -> layered filament painting (HueForge-style) for 3D ZT.

Model (verified by reverse-engineering the OWNROSE file):
  * height = base + luminance * (top - base), quantized to layers
  * filaments stacked dark -> light, swapped at chosen layers
  * colour seen = Beer-Lambert blend: a = 1 - 10^(-t / (TD * K))
    K ~ 0.2 fitted from the rose photo (TD as written on HueForge lists)
  * swap layers chosen automatically by minimizing colour error (Lab) vs the image
"""
import argparse, itertools, json, struct
import numpy as np
from PIL import Image

K_TD = 0.2  # fitted factor: effective decade-thickness = TD * K


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def to_lab(rgb):
    c = lin(np.clip(rgb, 0, 1))
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def simulate(H, filaments, starts, k=K_TD):
    """H: heights (mm). filaments: [(hex, TD)], starts: start height of each filament after the first."""
    out = np.zeros(H.shape + (3,)) + lin(hexrgb(filaments[0][0]))
    tops = list(starts[1:]) + [1e9]
    for (col, td), z0, z1 in zip(filaments[1:], starts, tops):
        t = np.clip(np.minimum(H, z1) - z0, 0, None)[..., None]
        a = 1 - 10 ** (-t / (td * k))
        out = out * (1 - a) + lin(hexrgb(col)) * a
    return srgb(out)


def layer_tops(first, lh, top):
    n = int(round((top - first) / lh)) + 1
    return first + lh * np.arange(n)  # top z of each layer


def make_heights(img_l, base, top, first, lh):
    H = base + img_l * (top - base)
    q = first + np.round((H - first) / lh) * lh
    return np.clip(q, first, top)


def choose_swaps(target_rgb, H, filaments, tops, lh):
    """Brute-force the swap layers (one per extra filament) that best match the image."""
    small = 120
    sH = np.asarray(Image.fromarray(H.astype(np.float32)).resize((small, small), Image.BILINEAR))
    sT = np.asarray(Image.fromarray((target_rgb * 255).astype(np.uint8)).resize((small, small))) / 255.0
    labT = to_lab(sT)
    cand = [z - lh for z in tops[1:]]  # a swap starts at the bottom of a layer
    best = (1e18, None)
    for combo in itertools.combinations(range(len(cand)), len(filaments) - 1):
        starts = [cand[i] for i in combo]
        err = np.linalg.norm(to_lab(simulate(sH, filaments, starts)) - labT, axis=-1).mean()
        if err < best[0]:
            best = (err, starts)
    return best


def level_colors(levels, filaments, starts):
    return simulate(levels[:, None], filaments, starts)[:, 0]


def color_match(target_rgb, filaments, levels, smooth=0.0):
    """Per-pixel: pick the layer height whose stacked colour is closest to the pixel (Lab).
    Searches swap layers too. Returns (err, starts, H)."""
    small = 120
    sT = np.asarray(Image.fromarray((target_rgb * 255).astype(np.uint8)).resize((small, small))) / 255.0
    labT = to_lab(sT).reshape(-1, 3)
    cand = list(levels[:-1])
    best = (1e18, None)
    for combo in itertools.combinations(range(len(cand)), len(filaments) - 1):
        starts = [cand[i] for i in combo]
        labL = to_lab(level_colors(levels, filaments, starts))
        d = np.linalg.norm(labT[:, None] - labL[None], axis=-1).min(1).mean()
        if d < best[0]:
            best = (d, starts)
    err, starts = best
    labL = to_lab(level_colors(levels, filaments, starts))
    labF = to_lab(target_rgb)
    idx = np.empty(labF.shape[:2], dtype=int)
    for r in range(labF.shape[0]):
        idx[r] = np.linalg.norm(labF[r][:, None] - labL[None], axis=-1).argmin(1)
    if smooth > 0:  # median filter removes speckle between near-equal levels
        from scipy import ndimage
        idx = ndimage.median_filter(idx, size=int(smooth))
    return err, starts, levels[idx]


def write_stl(path, H, px):
    """Watertight binary STL of a height field (top surface + flat bottom + 4 walls)."""
    ny, nx = H.shape
    xs = np.arange(nx) * px
    ys = (ny - 1 - np.arange(ny)) * px
    X, Y = np.meshgrid(xs, ys)
    top = np.stack([X, Y, H], -1)
    bot = np.stack([X, Y, np.zeros_like(H)], -1)
    tris = []
    a, b, c, d = top[:-1, :-1], top[:-1, 1:], top[1:, :-1], top[1:, 1:]
    tris += [np.stack([a, c, b], -2).reshape(-1, 3, 3), np.stack([b, c, d], -2).reshape(-1, 3, 3)]
    a, b, c, d = bot[:-1, :-1], bot[:-1, 1:], bot[1:, :-1], bot[1:, 1:]
    tris += [np.stack([a, b, c], -2).reshape(-1, 3, 3), np.stack([b, d, c], -2).reshape(-1, 3, 3)]

    def wall(t, bt, flip):
        p0, p1, q0, q1 = t[:-1], t[1:], bt[:-1], bt[1:]
        w1, w2 = np.stack([p0, q0, p1], 1), np.stack([p1, q0, q1], 1)
        if flip: w1, w2 = w1[:, ::-1], w2[:, ::-1]
        return [w1, w2]
    tris += wall(top[0], bot[0], True)          # back edge (max Y)
    tris += wall(top[-1], bot[-1], False)       # front edge (min Y)
    tris += wall(top[:, 0], bot[:, 0], False)   # left edge
    tris += wall(top[:, -1], bot[:, -1], True)  # right edge
    T = np.concatenate(tris).astype(np.float32)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(T), dtype=[('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')])
    rec['n'], rec['v'] = n, T
    with open(path, 'wb') as f:
        f.write(b'ZT-Forge'.ljust(80, b' ')); f.write(struct.pack('<I', len(T))); f.write(rec.tobytes())
    return T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image'); ap.add_argument('out')
    ap.add_argument('--width', type=float, default=200, help='mm (longest side)')
    ap.add_argument('--px', type=float, default=0.25, help='mm per pixel in the STL')
    ap.add_argument('--base', type=float, default=1.28, help='thinnest point mm (black only)')
    ap.add_argument('--top', type=float, default=3.0)
    ap.add_argument('--first', type=float, default=0.16)
    ap.add_argument('--lh', type=float, default=0.08)
    ap.add_argument('--filaments', default='[["#000000",0.4],["#DE4343",5],["#FCDE83",5],["#FFFFFF",5]]')
    ap.add_argument('--mode', choices=['luma', 'color'], default='luma')
    ap.add_argument('--smooth', type=float, default=3)
    a = ap.parse_args()
    fil = json.loads(a.filaments)
    im = Image.open(a.image).convert('RGB')
    s = a.width / max(im.size)
    nx, ny = int(round(im.width * s / a.px)), int(round(im.height * s / a.px))
    rgb = np.asarray(im.resize((nx, ny), Image.LANCZOS)) / 255.0
    L = to_lab(rgb)[..., 0] / 100.0
    L = (L - np.percentile(L, 0.5)) / (np.percentile(L, 99.5) - np.percentile(L, 0.5))
    tops = layer_tops(a.first, a.lh, a.top)
    if a.mode == 'color':
        levels = tops[tops >= a.base - 1e-6]
        err, starts, H = color_match(rgb, fil, levels, a.smooth)
    else:
        H = make_heights(np.clip(L, 0, 1), a.base, a.top, a.first, a.lh)
        err, starts = choose_swaps(rgb, H, fil, tops, a.lh)
    prev = simulate(H, fil, starts)
    Image.fromarray((np.clip(prev, 0, 1) * 255).astype(np.uint8)).save(a.out + '_preview.png')
    T = write_stl(a.out + '.stl', H, a.px)
    lines = [f'Size: {nx * a.px:.1f} x {ny * a.px:.1f} mm, height {H.min():.2f}-{H.max():.2f} mm',
             f'Layer height {a.lh} mm, first layer {a.first} mm, infill 100%, do NOT scale Z',
             f'Start with {fil[0][0]}']
    for (col, td), z in zip(fil[1:], starts):
        layer = int(round((z - a.first) / a.lh)) + 2
        lines.append(f'At layer #{layer} (top z {z + a.lh:.2f} mm) swap to {col}')
    lines.append(f'Mean colour error (Lab dE): {err:.1f}')
    open(a.out + '_swaps.txt', 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines)); print('triangles', len(T))


if __name__ == '__main__':
    main()
