"""BMW painter openwork wall art - PHASE 1 (flat vector design).
usage: python phase1.py <car_rgba.png> <composition.png> <out_dir>
Own code only; the pictures and everything derived from them stay OUT of git (pass paths as args)."""
import sys, os, json
import cv2, numpy as np
from scipy import ndimage as ndi

CAR, COMP, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
PPM = 10                      # canvas px per mm
W_MM, H_MM = 300.0, 150.0
CW, CH = int(W_MM*PPM), int(H_MM*PPM)

SC_CAR = 0.133                # mm per car-picture px
SC_PNT = 0.150                # mm per painter-picture px
R_CAR = 0.32                  # mm added per side to car lines
R_PNT = 0.45
CLOSE_GAP = 0.5               # mm: gaps narrower than this are closed (can't print)

# ---------- load ----------
car = cv2.imread(CAR, cv2.IMREAD_UNCHANGED)
car_m = (car[..., 3] > 128).astype(np.float32)
comp = cv2.imread(COMP)
b, g, r = [comp[..., i].astype(int) for i in range(3)]
dark = ((b < 120) & (r < 120) & (g < 120)).astype(np.uint8)
blue_ref = ((b > 140) & (r < 110) & (g < 120))
dark[806:] = 0; dark[:, :1190] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
keep = np.zeros_like(dark)
for i in range(1, n):
    if st[i, 4] > 30 and st[i, 0] + st[i, 2] > 1270:
        keep[lab == i] = 1
pnt_m = keep.astype(np.float32)

def place(mask, sc, ox_px, oy_px, tx_mm, ty_mm):
    """mask pixel (ox_px,oy_px) -> canvas mm (tx,ty)"""
    s = sc*PPM
    M = np.float32([[s, 0, tx_mm*PPM - s*ox_px], [0, s, ty_mm*PPM - s*oy_px]])
    big = cv2.warpAffine(cv2.GaussianBlur(mask, (0, 0), 1.0), M, (CW, CH), flags=cv2.INTER_CUBIC)
    return big > 0.5

def disc(mask, r_mm):
    if r_mm <= 0: return mask
    d = ndi.distance_transform_edt(~mask)
    return d <= r_mm*PPM

def close_gaps(mask, g_mm):
    r = g_mm/2*PPM
    d = ndi.distance_transform_edt(~mask)
    dil = d <= r
    d2 = ndi.distance_transform_edt(dil)
    return d2 > r - 0.5 + 0 if False else (ndi.distance_transform_edt(~(~dil)) > 0) & (ndi.distance_transform_edt(dil) > r) | mask

# ---------- layout ----------
Y_G = 126.0                                   # y of the painter's ground (mm) = rear tyre bottom
car_ox, car_oy = 9, 80                        # car bbox top-left in picture
# rear tyre bottom in picture px (measured below)
REAR_TYRE_BOT = 655.0
car_tx = 2.0
car_ty = Y_G - (REAR_TYRE_BOT - car_oy)*SC_CAR   # so rear tyre bottom lies on Y_G
PX0, PY0 = 1195, 11                           # painter bbox top-left (picture)
PY_BOOT = 806.0
pnt_tx = 300.0 - 2.0 - (1724-1195)*SC_PNT
pnt_ty = Y_G - (PY_BOOT-PY0)*SC_PNT

def car_pt(x, y):   # car picture px -> mm
    return np.array([car_tx + (x-car_ox)*SC_CAR, car_ty + (y-car_oy)*SC_CAR])
def pnt_pt(x, y):
    return np.array([pnt_tx + (x-PX0)*SC_PNT, pnt_ty + (y-PY0)*SC_PNT])

car_c = place(car_m, SC_CAR, car_ox, car_oy, car_tx, car_ty)
pnt_c = place(pnt_m, SC_PNT, PX0, PY0, pnt_tx, pnt_ty)

# ---------- wheels: keep rim, replace spokes by 5 strong spokes ----------
def canvas_poly(pts):
    return np.round(np.array(pts)*PPM).astype(np.int32)

def wheel(cx, cy, a, bb, rot_deg, phase=0.0, k_hole=0.30, k_hub=0.62):
    """cx,cy,a,bb in car picture px (centre, semi-axes x,y). Returns (erase_mask, add_mask) in canvas."""
    erase = np.zeros((CH, CW), np.uint8); add = np.zeros((CH, CW), np.uint8)
    c = car_pt(cx, cy)
    A, B = a*SC_CAR, bb*SC_CAR
    cv2.ellipse(erase, tuple(np.round(c*PPM).astype(int)), (int(A*PPM), int(B*PPM)), 0, 0, 360, 1, -1)
    # hub disc + hole
    hub_r = 0.30
    cv2.ellipse(add, tuple(np.round(c*PPM).astype(int)), (int(A*hub_r*PPM), int(B*hub_r*PPM)), 0, 0, 360, 1, -1)
    hole = np.zeros_like(add)
    cv2.ellipse(hole, tuple(np.round(c*PPM).astype(int)), (int(A*0.13*PPM), int(B*0.13*PPM)), 0, 0, 360, 1, -1)
    # 5 spokes: tapered bars from hub to rim, drawn in unit-circle coords then scaled to the ellipse
    for k in range(5):
        th = np.deg2rad(phase + 72*k)
        u = np.array([np.cos(th), np.sin(th)]); v = np.array([-u[1], u[0]])
        w0, w1 = 0.26, 0.17                           # half width (unit) at hub / rim
        pts = [0.2*u + w0*v*0.5, 1.0*u + w1*v*0.5, 1.0*u - w1*v*0.5, 0.2*u - w0*v*0.5]
        pp = [c + np.array([p[0]*A, p[1]*B]) for p in pts]
        cv2.fillPoly(add, [canvas_poly(pp)], 1)
    return erase.astype(bool), add.astype(bool), hole.astype(bool), (A, B)

wh = []
wh.append(wheel(833, 607, 77, 117, 0, phase=-90))
wh.append(wheel(1412, 531, 43, 90, 0, phase=-90))
lines0 = car_c.copy()
adds = np.zeros_like(car_c); holes = np.zeros_like(car_c)
for er, ad, hole, _ in wh:
    lines0 = lines0 & ~er
    adds |= ad; holes |= hole
car_c = lines0 | adds

# ---------- thicken ----------
# even, slightly heavier lines: car strokes grow by R_CAR per side (original ~1.0-1.3 mm -> ~1.7-2.0 mm)
fas = np.zeros((CH, CW), np.uint8)   # front fascia (grille, lamps): finest details, keep them open
cv2.fillPoly(fas, [canvas_poly([car_pt(*p) for p in [(15,395),(640,395),(640,640),(15,640)]])], 1)
fas = cv2.GaussianBlur(fas.astype(np.float32), (0,0), 15) > 0.5
car_t = np.where(fas, disc(lines0, 0.12), disc(lines0, R_CAR)) | adds
car_t = car_t & ~holes
pnt_t = disc(pnt_c, R_PNT)
black = car_t | pnt_t

# ---------- ground line ----------
gl = np.zeros((CH, CW), np.uint8)
tyre_f = car_pt(780, 774)       # front tyre bottom (measured)
tyre_r = car_pt(1410, 655)
GW = 3.0
p1 = np.array([car_tx+1.5, tyre_f[1] + (tyre_f[0]-car_tx-1.5)*(tyre_r[1]-tyre_f[1])/(tyre_r[0]-tyre_f[0])*-1.0])
slope = (tyre_r[1]-tyre_f[1])/(tyre_r[0]-tyre_f[0])
y_at = lambda x: tyre_f[1] + slope*(x-tyre_f[0])
pts = [(tyre_f[0]-4, y_at(tyre_f[0]-4)+GW/2), (tyre_r[0]+4, y_at(tyre_r[0]+4)+GW/2), (tyre_r[0]+4+8, Y_G+GW/2), (298, Y_G+GW/2)]
cv2.polylines(gl, [canvas_poly(pts)], False, 1, int(GW*PPM), cv2.LINE_AA)
for p in pts:
    cv2.circle(gl, tuple(np.round(np.array(p)*PPM).astype(int)), int(GW/2*PPM), 1, -1)
gl = gl.astype(bool)
black = black | gl

# ---------- blue: beams + quarter-panel accents ----------
bl = np.zeros((CH, CW), np.uint8)
nozzle = pnt_pt(1245, 347)
# three broad beams from the nozzle to the rear quarter edge of the car
tgt_x = car_pt(1498, 0)[0]
ys = [car_pt(0, y)[1] for y in (300, 366, 432, 498)]
for i in range(3):
    tri = [nozzle, (tgt_x, ys[i]+1.3), (tgt_x, ys[i+1]-1.3)]
    cv2.fillPoly(bl, [canvas_poly(tri)], 1)
def stripe(p, q, w):
    cv2.line(bl, tuple(np.round(car_pt(*p)*PPM).astype(int)), tuple(np.round(car_pt(*q)*PPM).astype(int)), 1, int(w*PPM), cv2.LINE_AA)
stripe((1030, 548), (1322, 506), 4.0)               # sill stripe
stripe((1030, 578), (1322, 540), 2.6)               # second, thinner sill stripe
# rear-arch crescent: arc between the two arch lines
arc = [(1352, 438), (1372, 395), (1405, 368), (1445, 370), (1478, 395)]
cv2.polylines(bl, [canvas_poly([car_pt(*p) for p in arc])], False, 1, int(4.0*PPM), cv2.LINE_AA)
blue = bl.astype(bool)
blue = blue & ~black          # blue only where the black does not already sit (black on top)
blue_core = blue

# ---- bridge any island to the main body with a 2 mm bar (shortest gap) ----
u = black | blue
lab, ncomp = ndi.label(u, structure=np.ones((3, 3)))
sizes = ndi.sum(u, lab, range(1, ncomp+1)); main = 1 + int(np.argmax(sizes))
BR = []
for i in range(1, ncomp+1):
    if i == main: continue
    dist, idx = ndi.distance_transform_edt(lab != i, return_indices=True)
    isl = lab == i
    cand = np.where(((lab == main)) & (dist < 400))
    k = np.argmin(dist[cand]); y2, x2 = cand[0][k], cand[1][k]
    ys_, xs_ = np.where(isl); j = np.argmin((ys_-y2)**2 + (xs_-x2)**2)
    cv2.line(bl, (int(xs_[j]), int(ys_[j])), (int(x2), int(y2)), 1, int(2.0*PPM))
    black = black | (np.zeros((CH, CW), np.uint8) + cv2.line(np.zeros((CH, CW), np.uint8), (int(xs_[j]), int(ys_[j])), (int(x2), int(y2)), 1, int(2.0*PPM))).astype(bool)
    BR.append((xs_[j]/PPM, ys_[j]/PPM))
print('bridges at (mm)', BR)
np.savez_compressed(os.path.join(OUT, 'masks.npz'), black=black, blue=blue)

# ---------- preview ----------
img = np.full((CH, CW, 3), 255, np.uint8)
img[black] = (20, 20, 20)
img[blue] = (200, 60, 20)       # BGR blue
cv2.imwrite(os.path.join(OUT, 'preview_p1.png'), img)
print('ok', black.sum()/PPM**2, 'mm2 black', blue.sum()/PPM**2, 'mm2 blue')
