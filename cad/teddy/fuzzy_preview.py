"""Simulate the slicer's fuzzy-skin on the teddy body (preview only): random normal jitter, spatial scale ~0.8 mm."""
import sys; sys.path.insert(0,'.')
import numpy as np, trimesh
from refine import refine_zone

def value_noise(p, scale, seed=1):
    g = p / scale
    i = np.floor(g).astype(np.int64); f = g - i
    f = f * f * (3 - 2 * f)
    def h(ix, iy, iz):
        k = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
        k = (k ^ (k >> 13)) * 1274126177
        k = (k ^ (k >> 16)) & 0xFFFF
        return k / 65535.0
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + w * h(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out * 2 - 1

def mask_smooth(p):
    """1 = keep smooth: muzzle/face features, paws, heart ring, base."""
    x, y, z = p[:, 0], p[:, 1], p[:, 2]
    d = lambda cx, cz, rx, rz: np.hypot((x - cx) / rx, (z - cz) / rz)
    face = d(861.4, 126, 30, 28) < 1                       # eyes, nose, smile
    heart = d(861.4, 56, 52, 46) < 1
    feet = (z < 55) & (np.abs(x - 861.4) > 35) & (y < 800)
    return (face | heart | feet)

def apply(mesh, amp=0.3, scale=0.8):
    V = mesh.vertices.copy(); n = mesh.vertex_normals
    noise = value_noise(V, scale)
    w = 1 - mask_smooth(V).astype(float)
    # soft edge of the mask
    V += n * (noise * amp / 2 * w)[:, None]
    return trimesh.Trimesh(V, mesh.faces, process=False)

if __name__ == '__main__':
    T = trimesh.load('out/teddy_rear_heart_LED_v3.stl')
    z = lambda c: (c[:, 1] < 830) & (c[:, 2] > 20)
    R = refine_zone(T, z, 0.55, iters=4)
    print('faces', len(R.faces))
    F = apply(R)
    F.export('/tmp/claude-0/-home-user--sharpseek-api/c69ab67c-81c4-5df2-a89e-e3b545ae3b81/scratchpad/out/teddy_fuzzy_preview.stl')
