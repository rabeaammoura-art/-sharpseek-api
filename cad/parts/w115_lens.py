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
    # Each rib is a trapezoid, all faces flat, top to bottom (fractions of the rib height):
    up_frac=0.06,       # upper flank, out from the valley above to the crest (near vertical, measured)
    crest_frac=0.64,    # flat crest (~20 mm, measured from the owner's video)
    down_frac=0.06,     # lower flank, back in to the valley (the rest is the flat valley floor, ~7.6 mm slot)
    rib_P0=23.0,        # crest protrusion from the valley line (~25 mm deep slots, measured)
    rib_step=1.5,       # each lower rib sticks out this much further (slight, per the owner)
    edge_r=1.5,         # small rounding on every crest / valley edge (not sharp, per the owner)
    D_back=28.0,        # groove line -> back/flange plane (body depth at nose = D_back + rib_P0)
    t=3.0,              # wall thickness
    flange_w=6.0,       # seal flange width at the back rim
    red_w=100.0,        # red inboard section width (front view)
    mid_w=120.0,        # middle section width (red top / clear bottom)
    A_wrap=88.0,        # amber wrap angle of the swept surface, degrees (cut back by the end edge)
    wrap_cut=72.0,      # where the open amber end edge cuts the wrap, at the bottom (valley angle, deg)
    R_end=72.5,         # inboard end: one big sweep back to the flange (sled-like, per the video); radius at the deepest crest
    fade_in=95.0,       # ribs fade out over this path length at the inboard end (video)
    fade_out=75.0,      # ... and at the outboard (amber) end, finishing before the end edge
    end_slant=25.0,     # amber end cut on a slant along the fender: bottom reaches this much further out
    r_in_top=12.0, r_in_bot=5.0,   # front-view corner radii, inboard end (the outboard end is shaped by its return)
    wall_t=2.5,         # inner partition walls
    wall_backoff=6.0,   # partition walls stop this far before the back plane
    box_cap_y=8.0,      # depth (Y) of the stop-lamp box inner panel
    stud_x1=97.0, stud_dx=120.0,   # stud spacing ~115-120 mm from the ruler photo
    stud_from_top=73.0,
    boss_d=11.0, boss_back=4.0,        # boss ends this far before the back plane
    insert_d=6.4, insert_depth=10.0,   # M5 heat-set insert (stud = M5 threaded rod)
)


def derived(p):
    d = dict(p)
    d["pitch"] = (p["H"] - p["lip_h"]) / p["n_ribs"]
    d["P_max"] = p["rib_P0"] + (p["n_ribs"] - 1) * p["rib_step"]
    d["xs"] = p["red_w"] + p["mid_w"]                     # wrap start = amber boundary
    d["A"] = math.radians(p["A_wrap"])
    # Wrap radius at the valley line: the amber shell curls round the car corner like a horn and
    # simply ends at a slanted edge (no end wall); at the bottom that edge sits on L_proj.
    d["Rg"] = (p["L_proj"] - d["xs"]) / math.sin(math.radians(p["wrap_cut"]))
    d["Rv"] = p["R_end"] - d["P_max"]                       # inboard corner radius at the valley line
    # clear = bottom rib + the 3rd rib's lower flank, up to the bottom edge of its flat crest
    d["clear_top"] = 2 * d["pitch"] - (p["up_frac"] + p["crest_frac"]) * d["pitch"]
    d["box_top"] = p["H"] - p["lip_h"] - 2.0
    for k in ("Rv",):         # corner radius at the valley line must clear the flange inset
        if d[k] <= p["flange_w"]:
            raise ValueError(f"{k}={d[k]:.1f} mm: raise R_end above P_max + flange_w = "
                             f"{d['P_max'] + p['flange_w']:.1f} mm")
    return d


def rib_points(d):
    """Rib relief from the top of the ribs down to z = 0, as (n, z) points; n = outward from the valley line."""
    H, pt = d["H"], d["pitch"]
    pts = []
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * pt
        Pi = d["rib_P0"] + i * d["rib_step"]
        z1 = zt - d["up_frac"] * pt
        z2 = z1 - d["crest_frac"] * pt
        z3 = z2 - d["down_frac"] * pt
        pts += [(0, zt), (Pi, z1), (Pi, z2), (0, z3)]     # upper flank, flat crest, lower flank
    pts.append((0, 0))                                     # flat valley floor of the last rib
    return pts


def _rounded(pts, round_pts, r):
    """Closed polygon face with the vertices at round_pts filleted by r."""
    with BuildSketch() as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
        targets = [v for v in sk.vertices()
                   if any(abs(v.X - x) < 1e-6 and abs(v.Y - y) < 1e-6 for x, y in round_pts)]
        if r > 0 and targets:
            fillet(targets, r)
    return sk.sketch.face()


def profile_2d(d):
    """Outer section in (u=Y depth, v=Z height)."""
    H, D = d["H"], d["D_back"]
    ribs = [(-n, z) for n, z in rib_points(d)]
    pts = [(D, H), (0, H)] + ribs + [(D, 0)]
    return _rounded(pts, ribs[:-1], d["edge_r"])


def valley_path(d, off, y_start, ang=None):
    """Valley line in plan (offset `off` inward): short inboard wall, big inboard sweep, along the
    lens, then the amber wrap (cut later by the slanted end edge). The rib relief is swept on it."""
    P, Rv, xs, Rg, A = d["P_max"], d["Rv"], d["xs"], d["Rg"], d["A"]
    # inboard sweep: arc of radius Rv about (P + Rv, Rv), starting where it meets y = y_start
    phi0 = 180.0 - math.degrees(math.asin(max(-1.0, min(1.0, (y_start - Rv) / (Rv - off)))))
    return Wire([CenterArc((P + Rv, Rv), Rv - off, phi0, 270.0 - phi0),
                 Line((P + Rv, off), (xs, off)),
                 CenterArc((xs, Rg), Rg - off, 270, math.degrees(A))])


def core(d, off, y_back, ang, z0, z1):
    """Body behind the valley line (closed along the back), extruded over z0..z1."""
    xs, Rg = d["xs"], d["Rg"]
    path = valley_path(d, off, y_back)
    end = path.position_at(1)
    rb = Rg - y_back
    a_end = 270 + math.degrees(ang)
    back_end = Vector(xs + rb * math.cos(math.radians(a_end)), Rg + rb * math.sin(math.radians(a_end)))
    start = path.position_at(0)
    edges = list(path.edges()) + [Line(end, back_end), CenterArc((xs, Rg), rb, 270, a_end - 270),
                                  Line((xs, y_back), start)]
    face = make_face(Wire.combine(edges)[0])
    return extrude(face, amount=z1 - z0).moved(Location((0, 0, z0)))


RELIEF_OVERLAP = 2.0  # relief sections reach this far into the core so the union is clean


def relief_outer(d):
    """Rib relief section in (n = outward from the valley line, z), closed slightly into the core."""
    e, top = RELIEF_OVERLAP, d["H"] - d["lip_h"]
    ribs = rib_points(d)
    return _rounded(ribs + [(-e, 0), (-e, top)], ribs[1:-1], d["edge_r"])


def relief_inner(d):
    """Cavity part inside the ribs: the wall-offset section, re-expressed about the inner valley line."""
    t, e, P, H = d["t"], RELIEF_OVERLAP, d["P_max"], d["H"]
    inner2d = offset(profile_2d(d), -t)
    clip = Rectangle(P + t + 10 + e, H + 10, align=(Align.MIN, Align.CENTER)).moved(Location((-P - 10, H / 2)))
    face = (inner2d & clip).face()                      # keeps y <= t + e
    return face.mirror(Plane.YZ).moved(Location((t, 0, 0)))   # (y, z) -> (n = t - y, z)


def sweep_relief(d, face, off, y_start, ang):
    path = valley_path(d, off, y_start, ang)
    o, t = path.position_at(0), path.tangent_at(0)
    pl = Plane(origin=(o.X, o.Y, 0), x_dir=(t.Y, -t.X, 0), z_dir=(-t.X, -t.Y, 0))
    return sweep(pl * face, path=path, transition=Transition.RIGHT)


def fade_region(d, inset):
    """Plan region (extruded in Z) behind a curve that follows the rib crests along the lens and
    closes in onto the valley line at both ends, so the ribs fade out there. `inset` moves it inward
    (for the cavity, so the wall keeps its thickness)."""
    path = valley_path(d, 0, d["D_back"])
    # ribs are gone just before the end edge reaches them at the top (the edge is slanted, so the
    # top of the lens ends first); from there the amber is a smooth horn down to the bottom tip
    x_top = d["L_proj"] - d["end_slant"]
    th_top = math.asin(min((x_top - d["xs"]) / d["Rg"], 1.0)) - math.radians(3)
    S = sum(e.length for e in path.edges()[:2]) + d["Rg"] * th_top          # edges: inboard sweep, straight, wrap
    full = d["P_max"] + 6.0
    pts = []
    n = 260
    for i in range(n + 1):
        s_ = path.length * i / n
        a = min(s_ / d["fade_in"], 1.0); b = min(max(S - s_, 0.0) / d["fade_out"], 1.0)
        f = (a * a * (3 - 2 * a)) * (b * b * (3 - 2 * b))
        p = path.position_at(s_, position_mode=PositionMode.LENGTH)
        t = path.tangent_at(s_, position_mode=PositionMode.LENGTH)
        out = Vector(t.Y, -t.X)                              # outward from the valley line
        e = (full + 1.0) * f - 1.0 - inset              # fully faded = 1 mm inside the body (clean union)
        pts.append((p.X + out.X * e, p.Y + out.Y * e))
    # close behind the lens: carry on past the outboard end wall (into the body), then round the back
    t_end = path.tangent_at(1.0)
    ext = (pts[-1][0] + t_end.X * 200, pts[-1][1] + t_end.Y * 200)
    far = 600.0
    pts += [ext, (ext[0], far), (pts[0][0], far)]
    with BuildSketch() as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return extrude(sk.sketch, amount=d["H"] + 20).moved(Location((0, 0, -10)))


def slant_keep(d, inset):
    """Half-space (as a big prism along Y) on the inboard side of the slanted amber end cut."""
    H, L = d["H"], d["L_proj"]
    x0, x1 = L + 0.5 - d["end_slant"], L + 0.5          # cut line at z = H and z = 0
    n = Vector(H, 0, x1 - x0).normalized()               # plane normal in XZ (points outboard)
    off = n * inset
    pts = [(-500, -500), (x1 + (x1 - x0) * 500 / H, -500), (x0 - (x1 - x0) * 500 / H, H + 500), (-500, H + 500)]
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine():
            Polyline(*pts, close=True)
        make_face()
    return extrude(sk.sketch, amount=600, both=True).moved(Location((-off.X, 0, -off.Z)))


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
    outer = (core(d, 0, D, A, 0, H) + (sweep_relief(d, relief_outer(d), 0, D, A) & fade_region(d, 0))) \
        & front_trim(d, 0) & slant_keep(d, 0)

    # Cavity: wall-offset chamber + back opening that leaves a seal flange of width fw.
    chamber = core(d, t, D - t, A, t, H - t) + (sweep_relief(d, relief_inner(d), t, D - t, A) & fade_region(d, t))
    # back opening: behind the flat back in the straight part, inside the back cylinder in the wrap
    behind = box(-50, d["xs"], D - t - 0.5, D + 10, -50, 500) + (
        Cylinder(R_back + t + 0.5, 500).moved(Location((d["xs"], d["Rg"], 0))) & box(d["xs"], 1000, -1000, 1000, -50, 500))
    opening = core(d, fw, D + 10, A, fw, H - fw) & behind
    cavity = (chamber + opening) & front_trim(d, t)   # open at the amber end edge, like the real one
    shell = outer - cavity
    # Flat back flange plate over the straight part (the inboard end sweeps back into it).
    x_plate = valley_path(d, 0, D).position_at(0).X
    plate = (box(x_plate, d["xs"], D - t, D, 0, H) & front_trim(d, 0)) - opening
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
