"""Mercedes W114/W115 wall art: photo of the render -> clean connected outline vector (px of a 4x crop, y up).
Pipeline: threshold -> simplify (close small gaps, fill small holes) -> hollow solid areas to an edge band ->
fix-ups (remove sill lines, square-grid radiator grille) -> connect loose islands -> potrace polygons."""
import pickle, sys
import cv2, numpy as np
from PIL import Image
from shapely import affinity
from shapely.geometry import LineString
from shapely.ops import nearest_points, unary_union
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from trace import mask_to_geom

SRC = sys.argv[1] if len(sys.argv) > 1 else "mb_source.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "mb_outline.pkl"
RAD = 11                         # edge band / line width in px (4x crop): 3.3 mm at 70 cm
k = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

im = np.array(Image.open(SRC).convert("L"))[150:402, 460:1070]
up = cv2.GaussianBlur(cv2.resize(im, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC), (0, 0), 2)
m = cv2.morphologyEx((up < 85).astype(np.uint8), cv2.MORPH_CLOSE, k(3))
n, lab, st, _ = cv2.connectedComponentsWithStats(1 - m, connectivity=4)
for i in range(1, n):
    if st[i, 4] < 900:
        m[lab == i] = 1
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k(3))
dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
h = ((m > 0) & ~(dt > RAD)).astype(np.uint8)

# 1) two sill lines that are not in the original drawing
h[745:800, 1280:1990] = 0
# 2) radiator grille: frame + crossing lines -> squares
x0, y0, x1, y1 = 248, 428, 608, 652
h[y0 - 12:y1 + 12, x0 - 12:x1 + 12] = 0
cv2.rectangle(h, (x0, y0), (x1, y1), 1, 12)
for i in range(1, 6):
    x = x0 + (x1 - x0) * i // 6; cv2.line(h, (x, y0), (x, y1), 1, 10)
for j in range(1, 4):
    y = y0 + (y1 - y0) * j // 4; cv2.line(h, (x0, y), (x1, y), 1, 10)

# 3) drop specks, bridge the remaining islands to the main body
n, lab, st, _ = cv2.connectedComponentsWithStats(h, connectivity=8)
for i in range(1, n):
    if st[i, 4] < 1500:
        h[lab == i] = 0
g = mask_to_geom(h.astype(bool), 1.0, h.shape[0])
parts = sorted(g.geoms if hasattr(g, "geoms") else [g], key=lambda p: -p.area)
main, bridges = parts[0], []
for p in parts[1:]:
    a, b = nearest_points(main, p)
    bridges.append(LineString([a, b]).buffer(6))
    main = unary_union([main, p, bridges[-1]])
g = affinity.translate(main, -main.bounds[0], -main.bounds[1]).simplify(1.0)
print("parts", len(g.geoms) if hasattr(g, "geoms") else 1, "bridges", len(bridges), "fill", round(g.area / (g.bounds[2] * g.bounds[3]), 3))
pickle.dump(g, open(OUT, "wb"))
