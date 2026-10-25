"""Line-art PNG (black lines on transparent/white) -> connected vector -> tiled STL wall-art pieces.
    python mb_wallart.py art.png OUTDIR            # sizes small/medium/large (width mm 500/700/940)"""
import math, sys, pathlib
import cv2, numpy as np, trimesh
import manifold3d as m3
from PIL import Image
from shapely import affinity
from shapely.geometry import LineString, box
from shapely.ops import nearest_points, unary_union
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from trace import mask_to_geom

SIZES = {"small": 500, "medium": 700, "large": 940}   # width mm
THICK = 3.0
BED = 320                                             # usable piece size mm (H2D bed 325 x 320)

im = Image.open(sys.argv[1]).convert("RGBA")
a = np.array(im)
dark = (a[..., 3] > 128) & (a[..., :3].max(-1) < 128) if a[..., 3].min() < 255 else a[..., :3].max(-1) < 128
m = cv2.resize(dark.astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
m = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2) > 0.5).astype(np.uint8)
g = mask_to_geom(m.astype(bool), 1.0, m.shape[0])
parts = sorted(g.geoms if hasattr(g, "geoms") else [g], key=lambda p: -p.area)
main = parts[0]
for p in parts[1:]:
    if p.area < 150:
        continue
    pa, pb = nearest_points(main, p)
    main = unary_union([main, p, LineString([pa, pb]).buffer(4)])
g = affinity.translate(main, -main.bounds[0], -main.bounds[1]).simplify(0.8)
W, H = g.bounds[2], g.bounds[3]
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for name, wmm in SIZES.items():
    s = wmm / W; gg = affinity.scale(g, s, s, origin=(0, 0)); hh = H * s
    nx, ny = math.ceil(wmm / BED), math.ceil(hh / BED)
    print(f"{name}: {wmm:.0f} x {hh:.0f} mm, {nx}x{ny} = {nx * ny} pieces, {gg.area * THICK * 1.24 / 1000:.0f} g solid")
    for j in range(ny):
        for i in range(nx):
            t = gg.intersection(box(i * wmm / nx, j * hh / ny, (i + 1) * wmm / nx, (j + 1) * hh / ny))
            polys = [p for p in (t.geoms if hasattr(t, "geoms") else [t]) if p.geom_type == "Polygon" and p.area > 2]
            if not polys:
                continue
            sol = m3.Manifold.batch_boolean([m3.Manifold.extrude(m3.CrossSection(
                [list(map(tuple, p.exterior.coords))] + [list(map(tuple, r.coords)) for r in p.interiors], m3.FillRule.EvenOdd), THICK)
                for p in polys], m3.OpType.Add).translate([-i * wmm / nx, -j * hh / ny, 0])
            ms = sol.to_mesh()
            trimesh.Trimesh(ms.vert_properties[:, :3], ms.tri_verts).export(out / f"mb_{name}_{i + 1}x{j + 1}.stl")
