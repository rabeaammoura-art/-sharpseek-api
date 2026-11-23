"""Threaded rear feet for the backlit box (alternative to the removable kickstand; `"stand": "thread_feet"`).

Two rigid feet screw straight into two bosses at the bottom corners of the box (no separate screws). The foot is a round rod that stands on the table
at its cut end; its other end is a coarse printed thread (stud) that screws into a threaded hole in a boss inside the box (thread axis = the back
normal, so the rod points back and slightly down: the plaque leans 12 degrees). Screwing a foot in / out adjusts the lean and levels the box.

Thread (printed, axis vertical when printing): major diameter 11 mm, pitch 3 mm, 45 degree flanks (no support), depth 1.2 mm, flat crest 0.4 mm,
0.3 mm clearance in the hole. Frames: box frame (x across, y up, z inward from the outer back face).
"""
import math

import manifold3d as m3
import numpy as np
import trimesh

RM, DEPTH, PITCH, CREST = 5.5, 1.2, 3.0, 0.4      # thread: major radius, depth, pitch, crest flat width (mm)
RN = RM - DEPTH                                    # minor radius
CLR = 0.3                                          # radial clearance of the hole (45 degree flanks: about 0.2 mm normal gap)
ROD_R = 7.0                                        # foot rod radius
STUD_L = 9.5                                       # engaged thread length (boss top at z = BOSS_TOP = 10)
BOSS_R, BOSS_TOP = 8.0, 10.0                       # boss inside the box: radius, top (box frame z)
ATTACH_S = 20.0                                    # attach point: this far up the back face from the outer bottom edge
X_IN = 25.0                                        # the foot axis is this far inside the plaque edge (x = size / 2 - X_IN)
TILT = 12.0


def _radius(a):
    """Thread radius at axial offset a (periodic in PITCH): root flat - 45 deg flank up - crest flat - 45 deg flank down."""
    a %= PITCH
    root = PITCH - 2 * DEPTH - CREST
    if a < root / 2:
        return RN
    a -= root / 2
    if a < DEPTH:
        return RN + a
    a -= DEPTH
    if a < CREST:
        return RM
    a -= CREST
    if a < DEPTH:
        return RM - a
    return RN


def cross_section(extra=0.0, n=360):
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        r = _radius(PITCH * th / (2 * math.pi)) + extra
        pts.append((r * math.cos(th), r * math.sin(th)))
    return m3.CrossSection([pts])


def thread_manifold(length, extra=0.0, z0=0.0):
    """Right-hand coarse thread along +z from z0 to z0 + length (a twisted extrusion of the one-lobe cross-section)."""
    turns = length / PITCH
    cs = cross_section(extra)
    th = m3.Manifold.extrude(cs, length, n_divisions=max(int(turns * 36), 1), twist_degrees=360.0 * turns)
    return th.rotate((0, 0, 360.0 * z0 / PITCH)).translate((0, 0, z0))       # keep the global thread phase: the profile at height z is the same for every tool


def to_trimesh(man):
    mesh = man.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=True)


def foot_length():
    """Distance along the axis from the back face to the CENTRE of the ball tip so that the ball's lowest point is on the table:
    the attach point is ATTACH_S up the back, the axis points back and down TILT degrees, ball radius = ROD_R."""
    t = math.radians(TILT)
    return (ATTACH_S * math.cos(t) - ROD_R) / math.sin(t)


def up_box():
    """World 'up' in the box frame (x, y, z): table normal."""
    t = math.radians(TILT)
    return np.array([0.0, math.cos(t), math.sin(t)])


def foot_points(size):
    """Attach points on the outer back face (box frame, z = 0): two bottom corners."""
    half_out = size / 2 + 0.2 + 2.6
    xf = size / 2 - X_IN
    y = -half_out + ATTACH_S
    return [(-xf, y), (xf, y)]


def make_foot():
    """One foot in the box frame at the origin: stud z in [0, STUD_L] (goes into the box), rod z in [-L, 0] (outside), ball tip centred at z = -L
    (radius ROD_R, its back-most 3 mm cut flat for printing: the cut is NOT the table contact, the ball's lowest point is)."""
    L = foot_length()
    rod = m3.Manifold.cylinder(L, ROD_R, ROD_R, 96).translate((0, 0, -L))
    ball = m3.Manifold.sphere(ROD_R, 96).translate((0, 0, -L))
    stud = thread_manifold(STUD_L, 0.0, 0.0)
    foot = rod + ball + stud
    cut = m3.Manifold.cube((40, 40, 20), center=True).translate((0, 0, -(L + ROD_R - 3.0) - 10.0))
    foot = foot - cut
    return to_trimesh(foot)


def foot_for_printing(foot):
    """Print pose = the box frame pose with the flat tip down on the bed (tip is the lowest z) and the stud pointing up."""
    f = foot.copy()
    f.apply_translation([0, 0, -f.bounds[0][2]])
    return f


def hole_tools(size):
    """Thread-hole tools (with clearance) for the box bosses, in the box frame: from z = -0.5 to the boss top."""
    out = []
    for x, y in foot_points(size):
        tool = thread_manifold(BOSS_TOP + 0.5, CLR, -0.5).translate((x, y, 0))
        out.append(to_trimesh(tool))
    return out
