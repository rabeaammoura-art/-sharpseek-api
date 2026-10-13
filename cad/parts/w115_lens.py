"""Mercedes W114/W115 /8 late-series (1973-76) rear lamp lens, Euro spec.

Approximate, parametric reproduction from photos (no factory drawing). Every
dimension lives in P and can be edited; see w115_lens/README.md for sources.

Coordinates (RH lens, as seen standing behind the car):
  X  along the lens, 0 = inboard (number-plate) end, + = outboard
  Z  up, 0 = bottom edge
  Y  depth, 0 = rib groove line, - = outward (toward the viewer), + = into the car
The amber section is a revolve that wraps toward +Y around the car corner.
"""
import math

from build123d import *

P = dict(
    L_proj=325.0,       # length seen straight from behind (rib noses)
    H=140.0,            # overall height
    lip_h=13.0,         # top seal-lip band (rubber gasket sits on it)
    n_ribs=4,
    nose_R=6.0,         # rounded nose at the bottom of each rib
    shoulder_h=5.0,     # height of the top shoulder (sets the groove width between ribs)
    face_lean=2.0,      # rib front face leans out this much from top to bottom
    rib_P0=10.0,        # top rib protrusion from groove line
    rib_step=3.0,       # each lower rib sticks out this much further
    D_back=28.0,        # groove line -> back/flange plane (body depth at nose = D_back + rib_P0)
    t=3.0,              # wall thickness
    flange_w=6.0,       # seal flange width at the back rim
    red_w=100.0,        # red inboard section width (front view)
    mid_w=120.0,        # middle section width (red top / clear bottom)
    A_wrap=50.0,        # amber wrap angle, degrees
    R_end=25.0,         # inboard end rounding in plan view
    r_in_top=25.0, r_in_bot=5.0, r_out_top=8.0, r_out_bot=30.0,  # front-view corner radii
    wall_t=2.5,         # inner partition walls
    wall_backoff=6.0,   # partition walls stop this far before the back plane
    box_cap_y=8.0,      # depth (Y) of the stop-lamp box inner panel
    stud_x1=97.0, stud_dx=130.0, stud_from_top=73.0,
    boss_d=11.0, boss_back=4.0,        # boss ends this far before the back plane
    insert_d=6.4, insert_depth=10.0,   # M5 heat-set insert (stud = M5 threaded rod)
)


def derived(p):
    d = dict(p)
    d["pitch"] = (p["H"] - p["lip_h"]) / p["n_ribs"]
    d["P_max"] = p["rib_P0"] + (p["n_ribs"] - 1) * p["rib_step"]
    d["xs"] = p["red_w"] + p["mid_w"]                     # wrap start = amber boundary
    d["A"] = math.radians(p["A_wrap"])
    # Wrap radius at the groove line, chosen so the outermost nose lands on L_proj.
    d["Rg"] = (p["L_proj"] - d["xs"]) / math.sin(d["A"]) - d["P_max"]
    d["clear_top"] = d["pitch"] + 2 * p["nose_R"]         # clear = bottom rib + lower part of the next
    d["box_top"] = p["H"] - p["lip_h"] - 2.0
    return d


def profile_2d(d):
    """Outer section in (u=Y depth, v=Z height)."""
    H, r, D = d["H"], d["nose_R"], d["D_back"]
    edges = [Line((D, H), (0, H)), Line((0, H), (0, H - d["lip_h"]))]
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * d["pitch"]
        zb = zt - d["pitch"]
        Pi = d["rib_P0"] + i * d["rib_step"]
        sh, fl = d["shoulder_h"], d["face_lean"]
        c45 = r * (1 - math.cos(math.pi / 4))
        edges.append(Line((0, zt), (-Pi + fl, zt - sh)))                    # top shoulder
        edges.append(Line((-Pi + fl, zt - sh), (-Pi, zb + r)))              # broad front face
        edges.append(ThreePointArc((-Pi, zb + r), (-Pi + c45, zb + c45), (-Pi + r, zb)))  # nose
        edges.append(Line((-Pi + r, zb), (0, zb) if i < d["n_ribs"] - 1 else (D, 0)))  # undercut
    edges.append(Line((D, 0), (D, H)))
    return make_face(Wire(edges))


def section_plane(x0):
    return Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))


def sweep_body(face2d, d, x_start, angle_trim):
    """Straight run from x_start to xs, then revolve (A - angle_trim) around the wrap axis."""
    straight = extrude(section_plane(x_start) * face2d, amount=d["xs"] - x_start, dir=(1, 0, 0))
    axis = Axis((d["xs"], d["Rg"], 0), (0, 0, 1))
    wrap = revolve(section_plane(d["xs"]) * face2d, axis, math.degrees(d["A"] - angle_trim))
    return straight, wrap


def plan_trim(d, inset):
    """Prism (along Z) rounding the inboard front corner in plan view."""
    with BuildSketch() as s:
        with Locations(((inset + d["xs"] + 5) / 2, (-d["P_max"] + inset + d["D_back"] + 40) / 2)):
            Rectangle(d["xs"] + 5 - inset, d["D_back"] + 40 + d["P_max"] - inset)
        fillet(s.vertices().group_by(Axis.X)[0].sort_by(Axis.Y)[0], max(d["R_end"] - inset, 0.5))
    return extrude(s.sketch, amount=d["H"] + 20).moved(Location((0, 0, -10)))


def front_trim(d, inset):
    """Prism (along Y) with the front-view outline and its corner radii."""
    L, H = d["L_proj"], d["H"]
    with BuildSketch(Plane.XZ) as s:
        with Locations(((L) / 2, H / 2)):
            Rectangle(L - 2 * inset, H - 2 * inset)
        vs = s.vertices()
        for vx, vz, key in ((0, H, "r_in_top"), (0, 0, "r_in_bot"), (L, H, "r_out_top"), (L, 0, "r_out_bot")):
            v = min(vs, key=lambda q: (q.X - vx) ** 2 + (q.Z - vz) ** 2)
            fillet(v, max(d[key] - inset, 0.5))
    return extrude(s.sketch, amount=200, both=True)


def solid_from(face2d, d, inset, angle_trim):
    straight, wrap = sweep_body(face2d, d, inset, angle_trim)
    straight = straight & plan_trim(d, inset)
    return (straight + wrap) & front_trim(d, inset)


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0, align=Align.MIN).moved(Location((x0, y0, z0)))


def make_bodies(p=P):
    d = derived(p)
    t, fw, D, H = d["t"], d["flange_w"], d["D_back"], d["H"]
    R_back = d["Rg"] - D
    outer_face = profile_2d(d)
    outer = solid_from(outer_face, d, 0.0, 0.0)

    # Cavity = wall-offset section + back opening that leaves a flange of width fw.
    inner_face = offset(outer_face, -t)
    with BuildSketch() as op:
        with Locations(((D - t - 0.5 + D + 10) / 2, H / 2)):
            Rectangle(10.5 + t, H - 2 * fw)
    cavity = solid_from(inner_face, d, t, t / R_back) + solid_from(op.sketch.face(), d, fw, fw / R_back)
    shell = outer - cavity

    # Inner partitions and the raised stop-lamp box (all clipped to the cavity).
    wt, ct, bt = d["wall_t"], d["clear_top"], d["box_top"]
    yl = D - d["wall_backoff"]
    x1, xs = d["red_w"], d["xs"]
    feats = [
        box(x1 - wt / 2, x1 + wt / 2, -50, yl, -1, H + 1),
        box(xs - wt, xs, -50, yl, -1, H + 1),
        box(x1, xs, -50, d["box_cap_y"], ct, ct + wt),
        box(x1, xs, -50, d["box_cap_y"], bt - wt, bt),
        box(x1, xs, d["box_cap_y"] - wt, d["box_cap_y"], ct, bt),
    ]
    for f in feats:
        shell += f & cavity

    # Stud bosses with M5 heat-set insert holes, opening toward the back.
    sz = H - d["stud_from_top"]
    yb = D - d["boss_back"]
    for sx in (d["stud_x1"], d["stud_x1"] + d["stud_dx"]):
        boss = Cylinder(d["boss_d"] / 2, yb + 60, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MAX))
        boss = boss.moved(Location((sx, yb, sz))) & outer
        hole = Cylinder(d["insert_d"] / 2, d["insert_depth"] + 1, rotation=(90, 0, 0),
                        align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((sx, yb + 1, sz)))
        shell = (shell + boss) - hole

    # Split into colour bodies; zero gap so they fuse in a single multi-material print.
    big = 1000
    red = (shell & box(-big, x1, -big, big, -big, big)) + (shell & box(x1, xs, -big, big, ct, big))
    clear = shell & box(x1, xs, -big, big, -big, ct)
    amber = shell & box(xs, big, -big, big, -big, big)
    return {"red": red, "clear": clear, "amber": amber}, d


def mirror_lh(part):
    return mirror(part, about=Plane.YZ)


def make() -> Part:
    bodies, _ = make_bodies()
    return Compound(children=list(bodies.values()))
