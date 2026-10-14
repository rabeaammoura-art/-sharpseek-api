"""Derived geometry shared by the build, validation and render scripts."""
from pathlib import Path
import functools
import numpy as np
import trimesh

import sys; sys.path.insert(0, str(Path(__file__).parent))
import params as P

ROOT = Path(__file__).parent
OUT = ROOT / "out"


@functools.lru_cache(None)
def fascia_coeffs():
    """Robust quadratic fit Y = f(X, Z) of the original front face (left housing).
    Fitted on the visible front face outside the old scoop and the outboard opening."""
    m = trimesh.load(OUT / "housing_L_repaired.stl")
    xs = np.arange(-175, 166, 2.0); zs = np.arange(122, 292, 2.0)
    X, Z = np.meshgrid(xs, zs)
    o = np.stack([X.ravel(), np.full(X.size, -400.0), Z.ravel()], 1)
    loc, idx, _ = m.ray.intersects_location(o, np.tile([0, 1.0, 0], (len(o), 1)), multiple_hits=False)
    y = np.full(X.size, np.nan); y[idx] = loc[:, 1]
    x, z = X.ravel(), Z.ravel()
    s = (~np.isnan(y) & (z > 133) & (z < 247) & (x > -168) & (x < 160)
         & ((x - P.OUTBOARD_APERTURE_C[0]) ** 2 + (z - P.OUTBOARD_APERTURE_C[1]) ** 2 > 52 ** 2)
         & ~((x > -150) & (x < 25) & (z > 140) & (z < 232)))
    A = np.stack([np.ones(s.sum()), x[s], z[s], x[s] ** 2, x[s] * z[s], z[s] ** 2], 1)
    keep = np.ones(s.sum(), bool)
    for _ in range(6):
        c, *_ = np.linalg.lstsq(A[keep], y[s][keep], rcond=None)
        r = y[s] - A @ c
        keep = np.abs(r) < 2.5 * np.std(r[keep])
    return c, float(np.sqrt((r[keep] ** 2).mean())), float(keep.mean())


def F(x, z):
    c, *_ = fascia_coeffs()
    x = np.asarray(x, float); z = np.asarray(z, float)
    return c[0] + c[1] * x + c[2] * z + c[3] * x * x + c[4] * x * z + c[5] * z * z


def aperture_edge_y(cx, cz, d, n=360):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    y = F(cx + d / 2 * np.cos(t), cz + d / 2 * np.sin(t))
    return y.min(), y.max()


def projector_frame():
    """Y positions along the projector axis (left housing frame)."""
    cx, cz = P.PROJ_C
    ymin, ymax = aperture_edge_y(cx, cz, P.PROJ_APERTURE_D)
    y_front = ymax + P.PROJ_FRONT_RECESS            # shroud front plane
    y_mount = y_front + P.PROJ_SHROUD_L             # projector mounting face = carrier rear face
    return dict(y_front=y_front, y_mount=y_mount, y_carrier_front=y_mount - P.CARRIER_T,
                aperture_y=(ymin, ymax))


def aim_points():
    cx, cz = P.PROJ_C
    f = projector_frame()
    y = f["y_mount"] - P.CARRIER_T / 2
    return dict(P=np.array([cx - P.AIM_EAR_IN, y, cz + P.AIM_Z_LOW]),
                A=np.array([cx - P.AIM_EAR_IN, y, cz + P.AIM_Z_HIGH]),
                B=np.array([cx + P.AIM_EAR_OUT, y, cz + P.AIM_Z_LOW]))


if __name__ == "__main__":
    c, rms, kept = fascia_coeffs()
    print("fascia fit coeffs", np.round(c, 8).tolist(), f"rms {rms:.2f} mm on {kept:.0%} of face samples")
    print("projector aperture edge Y range", aperture_edge_y(*P.PROJ_C, P.PROJ_APERTURE_D))
    print("outboard aperture edge Y range", aperture_edge_y(*P.OUTBOARD_APERTURE_C, P.OUTBOARD_APERTURE_D))
    print("projector frame", projector_frame())
    print("aim points", {k: v.round(1).tolist() for k, v in aim_points().items()})


BOSS_TOP_Z_BOTTOM = 142.0      # top face of all floor bosses (floor height varies 130.3..136 after the cut)
BOSS_BOT_Z_TOP = 236.0         # bottom face of all ceiling bosses


def mounts():
    """Bracket fixings (x, y, side). 'bot': M5 from BELOW through the housing floor into an insert in the
    bracket base; 'top': M5 from ABOVE through the top plate into an insert in the bracket top.
    Brackets are installed once on the bench; module service never needs them removed."""
    f = projector_frame(); a = aim_points(); ym = f["y_mount"]
    xi, xo = a["P"][0] - 7.0, a["B"][0]
    return {
        "inb_bot_1": (xi, ym + 10.0, "bot"), "inb_bot_2": (xi, ym + 30.0, "bot"), "inb_bot_3": (xi + 12.0, ym + 30.0, "bot"),
        "out_bot_1": (xo + 14.0, ym + 12.0, "bot"), "out_bot_2": (xo, ym + 42.0, "bot"),
        "out_top_1": (xo + 14.0, ym + 28.0, "top"),
    }


def adjusters():
    """Top-access adjuster screw axes (x, y): directly behind the A and B follower contacts."""
    a = aim_points(); ym = projector_frame()["y_mount"]
    w = wedge_geom(); return {"A": (a["A"][0], w["screw_y"]), "B": (a["B"][0], w["screw_y"])}


def top_step_y(x):
    """[CAD] the top plate has a 5 mm step whose edge runs diagonally, parallel to the face sweep:
    measured Y = -49.5 + 0.275 (X + 40) (X -140..40). In front of it the plate is Z 241.3..246.3, behind 246.3..251.3."""
    return -49.5 + 0.275 * (x + 40.0)


def top_surface_z(x, y):
    return 246.3 if y < top_step_y(x) else 251.3


def top_underside_z(x, y):
    return P.TOP_PLATE_UNDERSIDE_FRONT if y < top_step_y(x) else P.TOP_PLATE_UNDERSIDE_REAR


SEAT_Z = 252.3          # all top-side screw heads sit on flat pads 1 mm above the highest local top surface
ADJ_SEAT = {"A": "inboard_bracket", "B": "housing"}   # A: original plate ends in front of the screw


def devil_frame():
    """Devil Eye stack along Y (left frame)."""
    cx, cz = P.DEVIL_C
    ymin, ymax = aperture_edge_y(cx, cz, P.OUTBOARD_APERTURE_D)
    y_front = ymax + P.DEVIL_FRONT_RECESS
    y_flange = y_front + P.DEVIL_LENS_AHEAD           # module flange front face
    return dict(y_front=y_front, y_flange=y_flange, aperture_y=(ymin, ymax),
                ring_front=P.LIGHTRING_SEAT_Y, ring_rear=y_flange + P.DEVIL_FLANGE_T - 0.2)   # 0.2 mm clamp preload


def wedge_geom():
    """45° wedge in the Y-Z plane. Follower = Ø8 steel ball held FOLLOWER_OFFSET behind the carrier by a
    45° holder; contact normal n = (0, +s, -s) (rearward-down). Ball centre = the aim point A/B in Z."""
    import math
    ym = projector_frame()["y_mount"]
    r = P.FOLLOWER_BALL_D / 2; s = 1 / math.sqrt(2)
    ball_y = ym + P.FOLLOWER_OFFSET
    cy = ball_y + r * s
    h = P.WEDGE_RAMP_HALF
    return dict(ball_y=ball_y, cy=cy, dz=-r * s, y_front=cy - h, y_back=cy + h + 8.0, screw_y=cy + h + 4.5,
                ramp_half=h, below=14.0, above=13.0, s=s, r=r)


def aim_posts():
    """v2: post end Y (insert face) for P, A, B = carrier front face minus installed spring length."""
    f = projector_frame(); a = aim_points()
    y_end = f["y_mount"] - P.CARRIER_T - P.AIM_SPRING["l_installed"]
    return {k: (a[k][0], y_end, a[k][2]) for k in "PAB"}
