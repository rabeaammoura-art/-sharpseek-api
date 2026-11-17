"""Olive branches for the Dome of the Rock wall art, drawn clean: every leaf is a smooth almond on its own curved
spine (base, bend point, tip, width), olives are ellipses, twigs are smooth lines.  Positions measured on the picture.
-> black (leaves + olives + twigs), veins (midrib grooves, engraved later)."""
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

# base, bend (control point), tip, max width  -- picture pixels
LEAVES_TL = [
    ((187, 291), (225, 183), (152, 133), 37),     # 0 tall leaf beside the left frame
    ((254, 254), (307, 171), (378, 124), 49),     # 1 up to the top frame
    ((386, 235), (453, 180), (532, 107), 54),     # 2 up to the top frame, further right
    ((338, 234), (356, 214), (379, 211), 14),     # 3 bud on the twig
    ((519, 229), (635, 176), (732, 208), 52),     # 4 big right leaf, upper
    ((529, 223), (648, 254), (707, 341), 51),     # 5 big right leaf, lower
    ((363, 239), (454, 301), (490, 386), 53),     # 6 long middle leaf
    ((321, 327), (380, 375), (452, 398), 45),     # 7
    ((320, 355), (364, 461), (309, 526), 46),     # 8 hanging leaf
    ((160, 490), (205, 408), (248, 345), 52),     # 9 from the left frame, pointing up
    ((160, 539), (219, 476), (290, 470), 41),     # 10 lowest
]
OLIVES_TL = [((331, 284), 30, 33, -10), ((511, 273), 31, 35, 5), ((280, 386), 29, 36, 5)]
TWIGS_TL = [([(149, 388), (158, 345), (185, 300)], 22), ([(185, 300), (254, 255)], 14), ([(254, 255), (300, 243), (370, 234)], 14),
            ([(370, 234), (440, 224), (525, 217)], 12),
            ([(208, 300), (258, 308), (305, 322), (328, 340), (326, 362)], 15),
            ([(264, 310), (277, 354)], 7), ([(320, 236), (328, 254)], 6), ([(484, 222), (496, 243)], 7),
            ([(149, 522), (161, 490)], 14), ([(149, 562), (163, 538)], 14)]
LEAVES_BR = [
    ((805, 1195), (732, 1127), (646, 1114), 51),  # 11 upper big leaf
    ((759, 1193), (589, 1173), (511, 1272), 53),  # 12 lower big leaf
    ((704, 1199), (657, 1265), (628, 1310), 49),  # 13
    ((837, 1223), (796, 1267), (760, 1319), 48),  # 14
    ((885, 1227), (845, 1160), (794, 1096), 55),  # 15
    ((908, 1136), (898, 1068), (846, 962), 58),   # 16
    ((922, 1097), (924, 1044), (941, 1005), 18),  # 17
    ((897, 1115), (852, 1085), (793, 1060), 45),  # 18 leaf pointing left
    ((932, 1265), (930, 1168), (882, 1097), 18),  # 19 thin leaf beside the right frame
]
OLIVES_BR = [((751, 1241), 30, 35, 10)]
TWIGS_BR = [([(934, 1262), (905, 1238), (875, 1216), (845, 1204)], 22), ([(845, 1204), (800, 1189), (762, 1184)], 13),
            ([(905, 1238), (930, 1300)], 18), ([(775, 1190), (768, 1212)], 9)]


def leaf(base, bend, tip, width, k=60):
    B, C, T = (np.array(p, float) for p in (base, bend, tip))
    t = np.linspace(0, 1, k)[:, None]
    P = (1 - t) ** 2 * B + 2 * t * (1 - t) * C + t ** 2 * T
    d = 2 * (1 - t) * (C - B) + 2 * t * (T - C)
    n = np.c_[-d[:, 1], d[:, 0]] / np.hypot(d[:, 0], d[:, 1])[:, None]
    h = width / 2 * np.sin(np.pi * t ** 0.88) ** 0.8          # fullest a bit before the middle, both ends pointed
    body = Polygon(np.vstack([P + n * h, (P - n * h)[::-1]])).buffer(0)
    vein = LineString(P[int(k * .07):int(k * .9)])
    return body, vein


def branches(vein_w=3.6):
    black, veins = [], []
    for b, c, t, w in LEAVES_TL + LEAVES_BR:
        body, v = leaf(b, c, t, w)
        black.append(body)
        if w >= 30:
            veins.append(v.buffer(vein_w / 2, cap_style=1))
    for (c, rx, ry, rot) in OLIVES_TL + OLIVES_BR:
        black.append(affinity.rotate(affinity.scale(Point(c).buffer(1, 48), rx, ry), rot))
    for pts, w in TWIGS_TL + TWIGS_BR:
        black.append(LineString(pts).buffer(w / 2, join_style=1))
    return unary_union(black), unary_union(veins)
