"""Removable folding kickstand for the backlit box of the original plaque (glow_cap). All parts are printed, no metal.

Parts (all single colour, no supports):
  * module  - a plate that slides into a dovetail pocket in the back of the box (two flanges + neck), two hinge ears and a stop bar.
  * leg     - flat bar with a barrel at the top end and a wide foot (printed lying flat).
  * pin     - printed hinge pin with a head and two snap prongs (printed lying flat).
Box side: `pocket_shapes(size)` gives the pad (local thickening inside the back panel), the lipped slot (+ two entry windows), the
chamber behind the lips and two detent dimples. The module enters through the windows and is pushed UP by SLIDE mm: the leg's load
(it pushes the module up) then presses it against the closed end of the chamber, so the load cannot unlock it.

Frames: box frame = x across, y up (front view), z = inward from the outer face of the back panel (printed back down).
Module frame (print pose) = x, y up the module, z from the inner face of the flange (outer face of the neck at z = MOD_T).
Leg frame (print pose) = x, a along the leg from the hinge axis, z = b (thickness direction, 0 = the face on the bed).
"""
import math

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

# ---- dimensions (mm) ----
NECK_W, FLANGE_W = 24.0, 30.0          # module neck (through the lips) and flanges (behind the lips)
NECK_T, FLANGE_T = 2.5, 2.0            # neck = outer 2.5 (lip thickness), flange = inner 2.0
MOD_T = NECK_T + FLANGE_T
LM, FL = 28.0, 10.0                    # module length, flange length (two flanges, one at each end)
SLIDE = 10.0                           # the module is pushed up by this much after entering through the windows
CLR = 0.4                              # clearance per side in the pocket
AX_Y = 17.0                            # hinge axis above the module's bottom end
AX_W = 4.5                             # hinge axis height above the back surface
LEG_W, LEG_T = 12.0, 4.0               # leg width / thickness
BARREL_R = 4.5
EAR_X0, EAR_T = LEG_W / 2 + 0.35, 4.5  # ear inner face / thickness (0.35 side play for the barrel)
HOLE_R = 2.7                           # hinge hole radius (pin radius 2.5)
PIN_R = 2.5
OPEN_DEG = 24.0                        # the leg opens 24 degrees from the back; the plaque leans 12
TILT_DEG = 12.0
FOOT_W, FOOT_L = 40.0, 10.0
STOP_Y0, STOP_Y1, STOP_T = 14.0, 8.0, 3.0   # stop bar between the ears, this far below the axis (from-to), thickness
DET_X, DET_R, DET_Y = 12.0, 0.45, 5.0  # detent: bump on the neck side face, local y of the bump
DIMPLE_R = 0.9
LIP_T, CH_TOP, PAD_TOP = NECK_T, MOD_T + 0.2, MOD_T + 0.2 + 2.0   # pocket z levels (box frame)


def layout(size):
    """Positions in the box frame (y up). The hinge axis is where the old leg pivoted (0.82 x size above the plaque bottom)."""
    half_out = size / 2 + 0.2 + 2.6                      # outer half size of the box (BOX_WALL 2.6)
    y_a = -size / 2 + 0.82 * size
    y0 = y_a - AX_Y                                      # module bottom, locked position
    return {"y_axis": y_a, "y_lock": y0, "y_in": y0 - SLIDE, "y_bot": -half_out, "half_out": half_out,
            "leg_len": y_a - (-half_out)}


def pocket_shapes(size):
    """2D shapes (box frame) for make_lit_box: pad (thickening, z 1..PAD_TOP), slot incl. windows (cut z 0..LIP_T),
    chamber (cut z LIP_T..CH_TOP), dimples (cut z 0..LIP_T). Returns also the z levels."""
    L = layout(size)
    y_lo, y_hi = L["y_in"] - CLR, L["y_lock"] + LM + CLR
    win_w = FLANGE_W / 2 + CLR
    wins = [box(-win_w, L["y_in"] - CLR, win_w, L["y_in"] + FL + CLR),
            box(-win_w, L["y_in"] + LM - FL - CLR, win_w, L["y_in"] + LM + CLR)]
    slot = unary_union([box(-NECK_W / 2 - CLR, y_lo, NECK_W / 2 + CLR, y_hi)] + wins)
    chamber = box(-win_w, y_lo, win_w, y_hi)
    y_det = L["y_lock"] + DET_Y
    dimples = unary_union([Point(s * (NECK_W / 2 + CLR), y_det).buffer(DIMPLE_R, 16) for s in (-1, 1)])
    pad = box(-win_w - 6, y_lo - 5, win_w + 6, y_hi + 5)
    return {"pad": pad, "slot": unary_union([slot, dimples]), "chamber": chamber, "z": (LIP_T, CH_TOP, PAD_TOP), "layout": L}


# ---------- helpers ----------
def _prism_yz(poly, x0, x1):
    """Polygon given in (Y, Z) coordinates, extruded along x from x0 to x1 -> mesh with x = x0..x1, y = poly x, z = poly y."""
    m = trimesh.creation.extrude_polygon(poly.simplify(0.01), x1 - x0)   # poly (X=Y, Y=Z), extruded along its z (= our x)
    m.apply_transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], float))
    return m


def _teardrop(cy, cz, r):
    """Circle with a 45 degree point on +z (hole printed with its axis horizontal needs no support)."""
    pts = [(cy - r * math.cos(math.radians(45)), cz + r * math.sin(math.radians(45))),
           (cy + r * math.cos(math.radians(45)), cz + r * math.sin(math.radians(45))), (cy, cz + r * math.sqrt(2))]
    return unary_union([Point(cy, cz).buffer(r, 24), Polygon(pts)])


def _union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def stop_height(leg_poly_ab):
    """Height w (above the back surface) where the stop bar bottom must be so that the leg touches it at OPEN_DEG."""
    th = math.radians(OPEN_DEG)
    # leg point (a, b) -> (y, w) relative to the module bottom: y = AX_Y - a cos + b sin ; w = AX_W + a sin + b cos
    A = np.array([[-math.cos(th), math.sin(th)], [math.sin(th), math.cos(th)]])
    rot = Polygon([(AX_Y + A[0] @ p, AX_W + A[1] @ p) for p in np.array(leg_poly_ab.exterior.coords)])
    strip = box(AX_Y - STOP_Y0, -50, AX_Y - STOP_Y1, 50)
    return rot.intersection(strip).bounds[3]


def leg_profile(size):
    """Leg outline in (a, b): bar b in [-4.5, -0.5] from the axis down to the table-flat slanted end + barrel circle."""
    L = layout(size)
    t, th = math.radians(TILT_DEG), math.radians(OPEN_DEG)
    s = L["leg_len"]
    A_y = s * math.cos(t) - AX_W * math.sin(t)                   # world height of the hinge axis
    def a_end(b):                                               # where the leg's face at b meets the table (world y = 0)
        return (A_y - b * math.sin(th - t)) / math.cos(th - t)
    a1, a2 = a_end(-AX_W), a_end(-AX_W + LEG_T)
    bar = Polygon([(0, -AX_W), (a1, -AX_W), (a2, -AX_W + LEG_T), (0, -AX_W + LEG_T)])
    return bar, a1, a2


def make_module(size):
    L = layout(size)
    bar, _, _ = leg_profile(size)
    w_b = stop_height(bar.union(Point(0, 0).buffer(BARREL_R, 24)))
    w_top = w_b + STOP_T
    parts = []
    for y in (0.0, LM - FL):                                     # flanges (inner, printed first on the bed)
        parts.append(trimesh.creation.box(extents=(FLANGE_W, FL, FLANGE_T), transform=trimesh.transformations.translation_matrix((0, y + FL / 2, FLANGE_T / 2))))
    parts.append(trimesh.creation.box(extents=(NECK_W, LM, NECK_T), transform=trimesh.transformations.translation_matrix((0, LM / 2, FLANGE_T + NECK_T / 2))))
    # detent bumps on the neck side faces (vertical half-cylinders)
    for s in (-1, 1):
        c = trimesh.creation.cylinder(radius=DET_R, height=NECK_T, sections=16)
        c.apply_translation((s * NECK_W / 2, DET_Y, FLANGE_T + NECK_T / 2))
        parts.append(c)
    # ears: profile in (y, w), extruded across the ear thickness; w is measured from the neck's outer face
    ear = box(AX_Y - STOP_Y0 - 1.0, 0, AX_Y + 6.5, w_top)
    for s in (-1, 1):
        x0, x1 = (EAR_X0, EAR_X0 + EAR_T) if s > 0 else (-EAR_X0 - EAR_T, -EAR_X0)
        m = _prism_yz(ear, x0, x1)
        m.apply_translation((0, 0, MOD_T))
        parts.append(m)
    # stop bar between and into the ears
    xb = EAR_X0 + EAR_T
    bar_m = trimesh.creation.box(extents=(2 * xb, STOP_Y0 - STOP_Y1, STOP_T),
                                 transform=trimesh.transformations.translation_matrix((0, AX_Y - (STOP_Y0 + STOP_Y1) / 2, MOD_T + w_b + STOP_T / 2)))
    parts.append(bar_m)
    mod = _union(parts)
    hole = _prism_yz(_teardrop(AX_Y, MOD_T + AX_W, HOLE_R), -(EAR_X0 + EAR_T) - 1, EAR_X0 + EAR_T + 1)
    mod = trimesh.boolean.difference([mod, hole], engine="manifold")     # hinge hole through both ears
    return mod, {"w_stop": w_b, "ear_top": w_top, "length": LM, "width": FLANGE_W, "height": MOD_T + w_top}


def make_leg(size):
    """Leg lying flat (z = b + 4.5 so the back face is on the bed). Returns (mesh, info)."""
    bar, a1, a2 = leg_profile(size)
    foot_a0 = min(a1, a2) - FOOT_L
    shift = AX_W                                                  # print frame z = b + shift
    def prof(poly):                                               # polygon (a, b) -> polygon (Y=a, Z=b+shift)
        return affinity.translate(poly, 0, shift)
    bar_m = _prism_yz(prof(bar), -LEG_W / 2, LEG_W / 2)
    foot_poly = bar.intersection(box(foot_a0, -10, a1 + 5, 10))
    foot_m = _prism_yz(prof(foot_poly), -FOOT_W / 2, FOOT_W / 2)
    barrel = Point(0, 0).buffer(BARREL_R, 24)
    barrel_m = _prism_yz(prof(barrel), -LEG_W / 2, LEG_W / 2)
    hole_cut = _prism_yz(prof(_teardrop(0, 0, HOLE_R)), -LEG_W, LEG_W)
    leg = _union([bar_m, foot_m, barrel_m])
    leg = trimesh.boolean.difference([leg, hole_cut], engine="manifold")
    return leg, {"length": a1, "width": LEG_W, "foot": (FOOT_W, FOOT_L), "thickness": LEG_T}


def make_pin():
    """Printed hinge pin along x: head + shaft (with a small flat for the bed) + slit + two barb lugs at the free end."""
    xe = EAR_X0 + EAR_T
    shaft = trimesh.creation.cylinder(radius=PIN_R, height=2 * xe + 3.0, sections=32)
    shaft.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 1, 0)))
    shaft.apply_translation(((3.0) / 2, 0, 0))                    # x from -xe to xe + 3
    head = trimesh.creation.cylinder(radius=4.0, height=2.0, sections=32)
    head.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (0, 1, 0)))
    head.apply_translation((-xe - 1.0, 0, 0))
    lugs = []
    for s in (-1, 1):
        lugs.append(trimesh.creation.box(extents=(1.2, 0.9, 2.4), transform=trimesh.transformations.translation_matrix((xe + 1.5, s * (PIN_R + 0.2), 0))))
    pin = _union([shaft, head] + lugs)
    slit = trimesh.creation.box(extents=(4.2, 1.0, 10.0), transform=trimesh.transformations.translation_matrix((xe + 3.0 - 2.1 + 0.001, 0, 0)))
    pin = trimesh.boolean.difference([pin, slit], engine="manifold")
    flat = trimesh.creation.box(extents=(60, 10, 2.0), transform=trimesh.transformations.translation_matrix((0, 0, -PIN_R - 1.0 + 0.2)))
    pin = trimesh.boolean.difference([pin, flat], engine="manifold")
    pin.apply_translation((0, 0, PIN_R - 0.2))                    # lowest point on the bed
    return pin


# ---------- assembly (box frame) for checks and drawings ----------
def module_in_box(mod, size, slid=True):
    """Module placed in the box frame (rotated 180 degrees about y: the neck outer face is on the back surface z = 0)."""
    L = layout(size)
    m = mod.copy()
    m.apply_transform(np.array([[-1, 0, 0, 0], [0, 1, 0, L["y_lock"] if slid else L["y_in"]], [0, 0, -1, MOD_T], [0, 0, 0, 1]], float))
    return m


def leg_in_box(leg, size, theta_deg):
    L = layout(size)
    th = math.radians(theta_deg)
    m = leg.copy()
    m.apply_translation((0, 0, -AX_W))                            # leg frame z = b + AX_W  ->  b
    # (x, a, b) -> (x, y_a - a cos + b sin, z_box = -(AX_W + a sin + b cos))
    M = np.array([[1, 0, 0, 0], [0, -math.cos(th), math.sin(th), L["y_axis"]], [0, -math.sin(th), -math.cos(th), -AX_W], [0, 0, 0, 1]], float)
    m.apply_transform(M)
    return m


def pin_in_box(pin, size):
    L = layout(size)
    m = pin.copy()
    m.apply_translation((0, 0, -(PIN_R - 0.2)))
    # pin axis (x) stays along x; hinge axis is at (y_axis, w = AX_W) -> z_box = -AX_W
    m.apply_translation((0, L["y_axis"], -AX_W))
    return m
