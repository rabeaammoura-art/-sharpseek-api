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
    crest_frac=0.4,     # rounded crest = top 40% of each rib; the face below slopes in to the valley
    rib_P0=11.0,        # crest protrusion from the valley line
    rib_step=0.0,       # extra protrusion per rib going down (unconfirmed, so 0)
    D_back=28.0,        # groove line -> back/flange plane (body depth at nose = D_back + rib_P0)
    t=3.0,              # wall thickness
    flange_w=6.0,       # seal flange width at the back rim
    red_w=100.0,        # red inboard section width (front view)
    mid_w=120.0,        # middle section width (red top / clear bottom)
    A_wrap=50.0,        # amber wrap angle, degrees
    R_end=25.0,         # inboard corner radius in plan, at the rib crests (ribs wrap round it)
    R_end_out=20.0,     # outboard (amber) end return radius in plan, at the rib crests
    r_in_top=12.0, r_in_bot=5.0,   # front-view corner radii, inboard end (the outboard end is shaped by its return)
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
    d["Rvo"] = p["R_end_out"] - d["P_max"]                  # outboard return radius at the valley line
    # Wrap radius at the valley line, chosen so the outboard crest lands on L_proj.
    d["Rg"] = (p["L_proj"] - d["xs"] - d["Rvo"] - d["P_max"]) / math.sin(d["A"]) + d["Rvo"]
    d["crest_h"] = p["crest_frac"] * d["pitch"]
    d["Rv"] = p["R_end"] - d["P_max"]                       # inboard corner radius at the valley line
    d["clear_top"] = 2 * d["pitch"] - d["crest_h"]        # clear = bottom rib + face of the next, up to its crest
    d["box_top"] = p["H"] - p["lip_h"] - 2.0
    return d


def profile_2d(d):
    """Outer section in (u=Y depth, v=Z height)."""
    H, D = d["H"], d["D_back"]
    edges = [Line((D, H), (0, H)), Line((0, H), (0, H - d["lip_h"]))]
    hc = d["crest_h"]
    s45 = math.sin(math.pi / 4)
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * d["pitch"]
        zb = zt - d["pitch"]
        Pi = d["rib_P0"] + i * d["rib_step"]
        # crest: from the valley at the top of the rib, round outward and down to full protrusion
        edges.append(ThreePointArc((0, zt), (-Pi * s45, zt - hc + hc * s45), (-Pi, zt - hc)))
        # face: slopes back inward going down, into the valley at the bottom of the rib
        edges.append(Line((-Pi, zt - hc), (0, zb)))
    edges.append(Line((0, 0), (D, 0)))
    edges.append(Line((D, 0), (D, H)))
    return make_face(Wire(edges))


def _outboard(d, off, y_back, ang):
    """Outboard return: corner arc after the wrap, then the end wall running in to the back.
    Returns (corner arc, end-wall line, end point on the back circle)."""
    xs, Rg, Rvo, A = d["xs"], d["Rg"], d["Rvo"], d["A"]
    tdir = Vector(math.cos(A), math.sin(A))              # wrap tangent at its end
    inward = Vector(-math.sin(A), math.cos(A))           # toward the wrap centre
    co = Vector(xs + (Rg - Rvo) * math.sin(A), Rg - (Rg - Rvo) * math.cos(A))
    corner = CenterArc(co, Rvo - off, math.degrees(A) - 90, 90)
    start = co + tdir * (Rvo - off)
    # walk inward until the back circle (radius Rg - y_back about the wrap centre)
    c = Vector(xs, Rg)
    rb = Rg - y_back
    f = start - c
    b = 2 * f.dot(inward)
    cc = f.dot(f) - rb * rb
    s_ = (-b - math.sqrt(b * b - 4 * cc)) / 2 if b * b - 4 * cc >= 0 else 0
    s_ = max(s_, (-b + math.sqrt(max(b * b - 4 * cc, 0))) / 2) if s_ < 0 else s_
    end = start + inward * s_
    return corner, Line(start, end), end


def valley_path(d, off, y_start, ang=None):
    """Valley line in plan (offset `off` inward): inboard end wall, corner, along the lens,
    amber wrap, outboard corner and end wall. The rib relief is swept on it."""
    P, Rv, xs, Rg, A = d["P_max"], d["Rv"], d["xs"], d["Rg"], d["A"]
    corner, endline, _ = _outboard(d, off, y_start, A)
    return Wire([Line((P + off, y_start), (P + off, Rv)),
                 CenterArc((P + Rv, Rv), Rv - off, 180, 90),
                 Line((P + Rv, off), (xs, off)),
                 CenterArc((xs, Rg), Rg - off, 270, math.degrees(A)),
                 corner, endline])


def core(d, off, y_back, ang, z0, z1):
    """Body behind the valley line (closed along the back), extruded over z0..z1."""
    xs, Rg = d["xs"], d["Rg"]
    path = valley_path(d, off, y_back)
    end = path.position_at(1)
    rb = Rg - y_back
    a_end = math.degrees(math.atan2(end.Y - Rg, end.X - xs)) % 360
    edges = list(path.edges()) + [CenterArc((xs, Rg), rb, 270, a_end - 270),
                                  Line((xs, y_back), (d["P_max"] + off, y_back))]
    face = make_face(Wire.combine(edges)[0])
    return extrude(face, amount=z1 - z0).moved(Location((0, 0, z0)))


RELIEF_OVERLAP = 2.0  # relief sections reach this far into the core so the union is clean


def relief_outer(d):
    """Rib relief section in (n = outward from the valley line, z)."""
    H, hc, s45, e = d["H"], d["crest_h"], math.sin(math.pi / 4), RELIEF_OVERLAP
    edges = []
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * d["pitch"]
        zb = zt - d["pitch"]
        Pi = d["rib_P0"] + i * d["rib_step"]
        edges.append(ThreePointArc((0, zt), (Pi * s45, zt - hc + hc * s45), (Pi, zt - hc)))
        edges.append(Line((Pi, zt - hc), (0, zb)))
    top = H - d["lip_h"]
    edges += [Line((0, 0), (-e, 0)), Line((-e, 0), (-e, top)), Line((-e, top), (0, top))]
    return make_face(Wire(edges))


def relief_inner(d):
    """Cavity part inside the ribs: the wall-offset section, re-expressed about the inner valley line."""
    t, e, P, H = d["t"], RELIEF_OVERLAP, d["P_max"], d["H"]
    inner2d = offset(profile_2d(d), -t)
    clip = Rectangle(P + t + 10 + e, H + 10, align=(Align.MIN, Align.CENTER)).moved(Location((-P - 10, H / 2)))
    face = (inner2d & clip).face()                      # keeps y <= t + e
    return face.mirror(Plane.YZ).moved(Location((t, 0, 0)))   # (y, z) -> (n = t - y, z)


def sweep_relief(d, face, off, y_start, ang):
    pl = Plane(origin=(d["P_max"] + off, y_start, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
    return sweep(pl * face, path=valley_path(d, off, y_start, ang), transition=Transition.RIGHT)


def front_trim(d, inset):
    """Prism (along Y) with the front-view outline: inboard corner radii; open past the outboard end."""
    L, H = d["L_proj"] + 50, d["H"]
    with BuildSketch(Plane.XZ) as s:
        with Locations((L / 2, H / 2)):
            Rectangle(L - 2 * inset, H - 2 * inset)
        for vx, vz, key in ((0, H, "r_in_top"), (0, 0, "r_in_bot")):
            # re-read vertices after each fillet; sketch-local coords, so local Y is global Z here
            v = min(s.vertices(), key=lambda q: (q.X - vx) ** 2 + (q.Y - vz) ** 2)
            fillet(v, max(d[key] - inset, 0.5))
    return extrude(s.sketch, amount=200, both=True)


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0, align=Align.MIN).moved(Location((x0, y0, z0)))


def make_bodies(p=P):
    d = derived(p)
    t, fw, D, H = d["t"], d["flange_w"], d["D_back"], d["H"]
    A, R_back = d["A"], d["Rg"] - D
    outer = (core(d, 0, D, A, 0, H) + sweep_relief(d, relief_outer(d), 0, D, A)) & front_trim(d, 0)

    # Cavity: wall-offset chamber + back opening that leaves a seal flange of width fw.
    chamber = core(d, t, D - t, A, t, H - t) + sweep_relief(d, relief_inner(d), t, D - t, A)
    # back opening: behind the flat back in the straight part, inside the back cylinder in the wrap
    behind = box(-50, d["xs"], D - t - 0.5, D + 10, -50, 500) + (
        Cylinder(R_back + t + 0.5, 500).moved(Location((d["xs"], d["Rg"], 0))) & box(d["xs"], 1000, -1000, 1000, -50, 500))
    opening = core(d, fw, D + 10, A, fw, H - fw) & behind
    cavity = (chamber + opening) & front_trim(d, t)
    shell = outer - cavity
    # Flat back flange plate: at the inboard end it reaches out to the rib crests, so seen
    # from behind the end is a straight edge (as on the real lens), not the rib scallops.
    plate = (box(0, d["xs"], D - t, D, 0, H) & front_trim(d, 0)) - opening
    shell += plate

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
        boss = Cylinder(d["boss_d"] / 2, yb + 60, rotation=(90, 0, 0), align=(Align.CENTER, Align.CENTER, Align.MIN))
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
