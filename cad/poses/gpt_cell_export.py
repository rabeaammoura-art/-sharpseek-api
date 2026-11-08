"""Trace ONE plaque of the owner's GPT sheet faithfully (everything except the text) into a vector asset for the layout "gpt".
Usage: python cad/poses/gpt_cell_export.py <sheet.png> <x0 y0 x1 y1 of the plate frame> <out.json>
Traced from the picture: frame, bear + cloud, blue star, the 4 info-box outlines, the 4 icons (all 'main' colour) and the yellow moon / stars / heart
('accent'). Text (name, labels, values) is NOT traced: its boxes (bbox + calibrated font size) are stored so the generator re-typesets it with the
real font at the same place and size. Dark navy features of the bear: nose + mouth (inside the muzzle) are added to 'main'; the closed eyes become
cream cut-outs (dilated a little so they print). Units = plaque design units (300 = plate width, y up, origin = plate centre)."""
import json
import sys
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import newborn_plaque as n  # noqa: E402

sheet = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
x0, y0, x1, y1 = map(int, sys.argv[2:6])
out = Path(sys.argv[6])
NOBEAR = len(sys.argv) > 7 and sys.argv[7] == 'nobear'        # the picture shows the cloud WITHOUT a bear (our own bear is placed by the generator)
cx, cy, u = (x0 + x1) / 2, (y0 + y1) / 2, 300.0 / (x1 - x0)
v = 300.0 / (y1 - y0)                                       # the GPT plate is ~2 % wider than tall: stretch y a little to fit our square plate
H, W, _ = sheet.shape
body_blue = sheet[(y0 + y1) // 2, x0 + 8]                  # the frame colour = the main colour of the plaque
blue = np.linalg.norm(sheet - body_blue, axis=2) < 88
d_blue = np.linalg.norm(sheet - body_blue, axis=2)
alpha_blue = np.clip(1 - d_blue / 275.0, 0, 1)              # 1 on the bear colour, 0 on the paper, 0.5 on an anti-aliased edge
yel_proto = np.array([253.0, 189.0, 3.0])
alpha_yel = np.clip(1 - np.linalg.norm(sheet - yel_proto, axis=2) / 250.0, 0, 1)
yellow = (sheet[..., 0] > 225) & (sheet[..., 1] > 160) & (sheet[..., 2] < 110)
navy = np.linalg.norm(sheet - np.array([16.0, 22.0, 28.0]), axis=2) < 75
cell = np.zeros((H, W), bool); cell[y0:y1 + 2, x0:x1 + 2] = True


def to_units(g):
    from shapely import affinity
    return affinity.translate(affinity.scale(affinity.translate(g, -cx, -cy), u, -u, origin=(0, 0)), 0, 0)


def polys(mask, sigma=0.8, min_area=12, simp=0.3):
    f = ndi.gaussian_filter(mask.astype(float), sigma)
    gen = contourpy.contour_generator(z=f, fill_type=contourpy.FillType.OuterOffset)
    pts, offs = gen.filled(0.5, 1.5)
    res = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        if len(rings[0]) < 4:
            continue
        pg = Polygon(rings[0], [r for r in rings[1:] if len(r) >= 4]).buffer(0)
        if pg.area >= min_area:
            res.append(pg.simplify(simp))
    return unary_union(res) if res else Polygon()


def ser(g):
    res = []
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        rings = [list(p.exterior.coords)] + [list(r.coords) for r in p.interiors]
        res.append([[(round(x, 2), round(y, 2)) for x, y in r] for r in rings])
    return res


lab, nl = ndi.label(blue & cell, structure=np.ones((3, 3)))
comps = []
for i, sl in enumerate(ndi.find_objects(lab), 1):
    ar = int((lab[sl] == i).sum())
    if ar >= 6:                                      # also the small dots of the Arabic letters and the colon
        comps.append((i, ar, sl[1].start, sl[1].stop, sl[0].start, sl[0].stop))
rel = lambda c: (c[2] - x0, c[3] - x0, c[4] - y0, c[5] - y0)         # bbox relative to the plate frame

# info boxes (big outlines) + their icons; name zone; everything else inside those is text
boxes = [c for c in comps if 230 < c[3] - c[2] < 275 and 80 < c[5] - c[4] < 100]
assert len(boxes) == 4, len(boxes)
def key_of(c):
    right = (c[2] + c[3]) / 2 > (x0 + x1) / 2
    top = (c[4] + c[5]) / 2 < y0 + 0.68 * (y1 - y0)
    return {(True, True): "weight", (False, True): "length", (True, False): "date", (False, False): "time"}[(right, top)]
box_of = {key_of(c): c for c in boxes}
NAME = (x0 + 150, y0 + 175, x1 - 140, y0 + 290)
keep, text = set(), {"name": [], **{k: {"label": [], "value": []} for k in box_of}}
icon_w = 80
for c in comps:
    i, ar, bx0, bx1, by0, by1 = c
    if bx1 - bx0 > 570:
        continue                                       # the frame: rebuilt as a clean rounded ring by the generator
    if ar > 20000:
        keep.add(i); continue
    if c in boxes:
        keep.add(i); continue
    if bx0 >= NAME[0] and bx1 <= NAME[2] and by0 >= NAME[1] and by1 <= NAME[3]:
        text["name"].append(c); continue
    placed = False
    for k, b in box_of.items():
        if bx0 >= b[2] and bx1 <= b[3] and by0 >= b[4] and by1 <= b[5]:
            # icon = everything at the left end of the box (rtl layout: icon at the left end), the rest is text
            if bx1 <= b[2] + 92:
                keep.add(i)
            elif (by0 + by1) / 2 < b[4] + 0.42 * (b[5] - b[4]):
                text[k]["label"].append(c)
            else:
                text[k]["value"].append(c)
            placed = True
            break
    if not placed and ar >= 40:
        keep.add(i)                                    # frame, bear/cloud outline parts, blue star ...
main_mask = np.isin(lab, list(keep))
# nose + mouth (dark, inside the cream muzzle) printed in the bear colour; closed eyes (dark, outside the muzzle) cut out, a little thicker
yy, xx = np.mgrid[0:H, 0:W]
muzzle = ((xx - (x0 + 291)) ** 2 + (yy - (y0 + 134)) ** 2) < 32 ** 2
bear_zone = (xx > x0 + 180) & (xx < x0 + 420) & (yy > y0 + 20) & (yy < y0 + 200)
main_mask |= navy & muzzle & cell
lum = 0.3 * sheet[..., 0] + 0.59 * sheet[..., 1] + 0.11 * sheet[..., 2]
# ---- the bear, rebuilt from clean pieces of the picture -------------------------------------------------------------------------------
if NOBEAR:
    sil = np.zeros((H, W), bool); details = sil; eyes = sil
    alpha_rest = alpha_blue * ndi.binary_dilation(main_mask, iterations=3)
    alpha_main = alpha_rest
else:
    bzone = (xx > x0 + 172) & (xx < x0 + 440) & (yy > y0 + 22) & (yy < y0 + 222)
    # ---- the bear taken as it is: every pixel gets the nearest of the 4 colours of the picture (paper / body blue / cream / navy) -------------
    protos = np.array([[250.0, 249.0, 246.0], body_blue, [253.0, 243.0, 219.0], [16.0, 22.0, 28.0], [3.0, 45.0, 112.0]])
    cls = np.argmin(((sheet[:, :, None, :] - protos[None, None]) ** 2).sum(3), axis=2)          # 0 paper, 1 body, 2 cream, 3 navy, 4 dark blue (outlines of paws / arm)
    cls_f = ndi.median_filter(cls, size=5)                                                       # removes speckle, keeps every shape
    solid = (cls_f != 0) & bzone
    solid = ndi.binary_fill_holes(solid)
    lab_s, ns = ndi.label(solid)
    cid = lab_s[100 + y0, 330 + x0]
    sil = lab_s == (cid if cid else 1 + int(np.argmax(ndi.sum(solid, lab_s, range(1, ns + 1)))))
    body_m = sil & (cls_f == 1)
    cream_m = sil & (cls_f == 2)
    inner_zone = ndi.binary_erosion(sil, iterations=5) & ~ndi.binary_dilation(cream_m, iterations=4)
    navy_m = sil & ((cls_f == 3) | ((cls_f == 4) & inner_zone))       # navy features + the dark-blue paw / arm outlines inside the silhouette (not its rim)
    bear_main = sil & ~cream_m & ~navy_m
    details = navy_m
    alpha_bear = ndi.gaussian_filter(bear_main.astype(float), 0.9)
    rest = main_mask & ~ndi.binary_dilation(sil, iterations=5)
    alpha_rest = alpha_blue * ndi.binary_dilation(rest, iterations=3) * (~ndi.binary_dilation(sil, iterations=2))
    alpha_main = np.maximum(alpha_rest, alpha_bear)
    eyes = navy_m
navy_g = polys(ndi.gaussian_filter(details.astype(float), 0.8), sigma=0.4, min_area=3, simp=0.2)
main_g = polys(ndi.gaussian_filter(alpha_main, 0.4), sigma=0.5, simp=0.3)
nobear_g = polys(ndi.gaussian_filter(alpha_rest, 0.4), sigma=0.5, simp=0.3)      # cloud outline, boxes, icons, star: without the GPT bear (our own bear is placed instead)
# text = everything blue inside the name zone and the text zone of each box (rectangles, so even the tiny dots of the letters are caught)
yy2, xx2 = np.mgrid[0:H, 0:W]
zones = (xx2 >= NAME[0]) & (xx2 <= NAME[2]) & (yy2 >= NAME[1]) & (yy2 <= NAME[3])
for b in box_of.values():
    zones |= (xx2 >= b[2] + 92) & (xx2 <= b[3] - 7) & (yy2 >= b[4] + 7) & (yy2 <= b[5] - 7)
text_near = zones
text_g = polys(np.clip(alpha_blue * 1.6, 0, 1) * text_near, sigma=0.4, min_area=4, simp=0.2)     # boosted alpha keeps the tiny dots of the letters
yel_g = polys(alpha_yel * ndi.binary_dilation(yellow & cell, iterations=3), sigma=0.55, simp=0.3)
from shapely import affinity
main_u = affinity.scale(affinity.translate(main_g, -cx, -cy), u, -v, origin=(0, 0))
nobear_u = affinity.scale(affinity.translate(nobear_g, -cx, -cy), u, -v, origin=(0, 0))
navy_u = affinity.scale(affinity.translate(navy_g, -cx, -cy), u, -v, origin=(0, 0))
text_u = affinity.scale(affinity.translate(text_g, -cx, -cy), u, -v, origin=(0, 0))
yel_u = affinity.scale(affinity.translate(yel_g, -cx, -cy), u, -v, origin=(0, 0))


def bbox_units(cs):
    bx0 = min(c[2] for c in cs); bx1 = max(c[3] for c in cs); by0 = min(c[4] for c in cs); by1 = max(c[5] for c in cs)
    return [round((bx0 - cx) * u, 2), round((cy - by1) * v, 2), round((bx1 - cx) * u, 2), round((cy - by0) * v, 2)]   # x0, y0, x1, y1 (y up)


tb = {"name": bbox_units(text["name"])}
for k in box_of:
    tb[k] = {"label": bbox_units(text[k]["label"]), "value": bbox_units(text[k]["value"])}
# calibrate font sizes so the sample text has the width it has in the picture
def natural_w(txt_segments):
    g, w = n.text_line(txt_segments, "ar", True)
    return w
wname = tb["name"][2] - tb["name"][0]
size_name = 40 * wname / natural_w([("يوسف", 40, "name")])
lab_txt = {"weight": "الوزن", "length": "الطول", "date": "التاريخ", "time": "الساعة"}
sl = [7.5 * (tb[k]["label"][2] - tb[k]["label"][0]) / natural_w([(lab_txt[k], 7.5, "word")]) for k in lab_txt]
size_label_factor = float(np.mean(sl)) / 7.5
ex_vals = {"weight": [("٣٫٤", 17, "num"), ("كغم", 9, "word")], "length": [("٥٠", 17, "num"), ("سم", 9, "word")],
           "date": [("١٢/٠٣/٢٠٢٦", 14.5, "num")], "time": [("٠٤:٣٥", 17, "num"), ("ص", 9, "word")]}
label_factor = {k: round((tb[k]["label"][2] - tb[k]["label"][0]) / natural_w([(lab_txt[k], 7.5, "word")]), 3) for k in lab_txt}
value_factor = {k: round((tb[k]["value"][2] - tb[k]["value"][0]) / natural_w(ex_vals[k]), 3) for k in ex_vals}
size_label_factor, size_value_factor = label_factor, value_factor
out.write_text(json.dumps({"main": ser(main_u), "accent": ser(yel_u), "text_traced": ser(text_u), "navy": ser(navy_u), "main_nobear": ser(nobear_u), "text": tb, "name_size": round(size_name, 2),
                           "label_factor": label_factor, "value_factor": value_factor}))
print("main polys", len(ser(main_u)), "accent", len(ser(yel_u)), "name", tb["name"], "size_name", round(size_name, 1), label_factor, value_factor)
