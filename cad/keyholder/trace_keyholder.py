"""Trace the big colour shapes (red strip, silver car swoosh) from the reference picture by colour masks.
Output json stays LOCAL (picture of the owner, not committed). Usage: trace_keyholder.py ref.png out.json"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure
from shapely.geometry import Polygon

im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(int)
R, G, B = im[..., 0], im[..., 1], im[..., 2]
H, W = R.shape
yy, xx = np.mgrid[0:H, 0:W]

def comp(mask, roi, close=3, sigma=2.0):
    m = mask & roi
    m = ndi.binary_closing(m, iterations=close)
    m = ndi.binary_fill_holes(m)
    lab, n = ndi.label(m)
    if n == 0: return None
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    sm = ndi.gaussian_filter(m.astype(float), sigma)
    c = max(measure.find_contours(sm, 0.5), key=len)
    p = Polygon([(x, y) for y, x in c]).buffer(0).simplify(0.8)
    return [list(map(float, q)) for q in p.exterior.coords]

red = (R > 120) & (G < 80) & (B < 80) & (R - G > 80)
strip = comp(red, (xx > 530) & (yy > 440) & (yy < 660) & (xx < 1500), close=6, sigma=2.5)
# the red stripe on the wheel / seat stitching are outside the roi

silver = (R > 150) & (G > 150) & (B > 140) & (abs(R - B) < 60)
roi = (xx > 745) & (xx < 1320) & (yy > 165) & (yy < 300)
sw = comp(silver, roi, close=2, sigma=1.5)
json.dump({"strip": strip, "swoosh": sw}, open(sys.argv[2], "w"))
print(len(strip), len(sw))
