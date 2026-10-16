"""One-piece retrofit housing: the face plate alone, no rear shell and no light tube.

Idea from the user's own Fusion sketch. The face plate (traced W114 outline, raised frame,
two curved grooves above and below the light for 6x12 mm silicone neon-flex LED strip as
DRL "eyebrows") screws straight onto the car. The light's own halo does the turn signal. The 5.75" light hangs from a separate
aiming bracket (retrofit_onepiece_bracket.py) bolted to the 4 M5 holes on its back; the
bracket rides on 3 posts behind the face plate with a spring screw on each post, like the
original headlight's adjusters. Turning the screws tilts the light up/down and left/right.
Prints face-down on the bed, posts pointing up: no supports.
Axes: X = width, Z = height (on the car), Y = depth (front face at Y=0, -Y toward the engine).
"""
import importlib.util
from pathlib import Path

from build123d import *

_spec = importlib.util.spec_from_file_location("retrofit_housing", Path(__file__).with_name("retrofit_housing.py"))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

FACE_T = 5.0
PRINT_ROTATION = ("X", -90)  # front face down on the bed
LIGHT_D = 141              # found 5.75" light: 141 dia x 76 deep
LIGHT_Z = 0
TILT_GAP = 4.0             # radial gap around the light so it can tilt ~3 deg each way
OPENING_D = LIGHT_D + 2 * TILT_GAP

# Matte-black frame round the edge, in place of the chrome trim ring: a separate flat ring
# (retrofit_onepiece_ring.py) that snaps on with hooks through slots in the face plate and
# hides the car screws. Separate so the housing's front prints flat on the bed.
FRAME_W = 15
FRAME_H = 3                # ring thickness, stands proud of the face plate's front
FRAME = base.outline() - base.outline(FRAME_W)
# Car screws: M5 countersunk (flat head) so they sit flush under the ring.
CSK_D = 10.4               # countersink diameter at the face (M5 flat head ~9.2-10)

# --- Snap hooks (on the ring) and keepers (on the housing) ---
# Each hook goes through a slot in the face plate and its catch clicks into a window in a
# small keeper wall behind the face. The catch's front face is a 45 deg ramp, not a flat
# lock, so the ring comes off FROM THE FRONT: lever it with a plastic trim tool in one of the
# two pry notches under its bottom edge (the back of the housing is not reachable once it is
# screwed to the car). Long hook (~15 mm) so it bends gently: printed upright it bends
# across its layers, so strain must stay low (~1.5 %).
SNAP_INSET = 12            # hook centre line, measured in from the outline edge
SNAP_W = 8                 # hook width (along the edge)
SNAP_T = 2.0               # hook thickness
SNAP_CATCH = 0.8           # how far the catch sticks out
SNAP_WINDOW_TOP = 13.1     # keeper window's top edge, this far behind the face plate front
SNAP_GAP = 0.2             # hook <-> keeper wall clearance
# Catch tip (most protruding point) depth: puts the 45 deg retention ramp right on the
# window's top edge when the ring is home, so it sits without rattle.
SNAP_CATCH_Z = SNAP_WINDOW_TOP + SNAP_CATCH - SNAP_GAP
PRY_NOTCHES = (-20, 20)    # x of the pry notches in the ring's bottom edge
PRY_NOTCH = (10, 1.2, 4)   # width, depth into the ring's back, reach in from the edge
SNAP_LEN = 15.5            # hook length behind the face plate front
KEEPER_T = 2.0
KEEPER_LEN = 17.5          # keeper wall reaches this far behind the face plate front
# Hook positions as (x, sign of z): top/bottom pairs and side pairs, clear of the car screws
# and the aiming posts; symmetric, so one ring fits both lights.
SNAP_SPOTS = [(-40, 1), (40, 1), (-40, -1), (40, -1), ("side", 50), ("side", -50),
              ("-side", 50), ("-side", -50)]

# Car fixing holes through the face plate (PLACEHOLDER positions: match the car's screws).
CAR_HOLE_D = 5.5
CAR_HOLE_INSET = 7         # hole centre distance in from the outline edge

# --- Aiming: 3 posts behind the face plate, one spring screw (M5) on each ---
# P = pivot corner (set once), V above it = up/down, H beside it = left/right.
# Posts sit in the side band beside the light, clear of the neon grooves.
POSTS = {"P": (-78, -30), "V": (-78, 30), "H": (78, -30)}
PAD_DEPTH = 60             # measured: light front face -> mounting-pad face on its back
SPRING_GAP = 10            # spring length between post end and bracket (reuse the old ones)
POST_D = 14
POST_END_Y = -(PAD_DEPTH - SPRING_GAP)  # posts stop here; the bracket sits at -PAD_DEPTH
M5_CLEAR = 5.5
M5_NUT_AF = 8.0 + 0.3      # trapped M5 nut in each post end
M5_NUT_H = 5.0 + 0.4      # fits a plain or a nylon-lock (nyloc) M5 nut
NUT_FROM_END = 4.0
ROOT_R = 8                 # post root flare, so the post doesn't snap off at the layer joint
ROOT_H = 12

# --- Neon-flex DRL grooves above and below the light ---
# For 6 x 12 mm "side bend" silicone neon flex: 6 mm lit face forward, 12 mm deep.
# The strip sits in the groove flush with the face; each end dives into a slot to the back
# for the end cap and cable. Three line styles (make(style=...)):
#   "arc"      arcs concentric with the light
#   "frame"    gentle curves that follow the frame's top and bottom edges
#   "straight" straight horizontal bars
NEON_W = 6.0 + 0.4         # strip width + fit
NEON_DEPTH = 12.0          # groove depth from the face front (strip height)
NEON_WALL = 2.0            # groove walls behind the face plate
NEON_GAP = 16              # face left between the light opening and the groove
NEON_MARGIN = 2            # face left between groove wall and the frame's inner edge
NEON_MIN_BEND_R = 50       # tightest bend a 6x12 side-bend strip takes
NEON_END_HOLE = (NEON_W, 14)  # through-slot at each end for the end cap + cable
_KEEP_OUT = NEON_W / 2 + NEON_WALL + NEON_MARGIN  # centre line -> frame inner edge
_FRAME_IN = base.outline(FRAME_W).outer_wire()


def _inside_frame(x, z):
    return Face(_FRAME_IN).is_inside(Vector(x, z)) and _FRAME_IN.distance_to(Vertex(x, z, 0)) >= _KEEP_OUT


def _arc_paths():
    import math
    r = OPENING_D / 2 + NEON_GAP + NEON_W / 2
    paths = []
    for mid in (90, 270):
        da = 0
        while da < 90:
            a = math.radians(mid + da + 1)
            if not _inside_frame(r * math.cos(a), LIGHT_Z + r * math.sin(a)):
                break
            da += 1
        paths.append(Edge.make_circle(r, start_angle=mid - da, end_angle=mid + da)
                     .locate(Location((0, LIGHT_Z))))
    return paths


def _straight_paths():
    paths = []
    r_open = OPENING_D / 2
    for sign in (1, -1):
        z_frame = max(p.Y * sign for p in (_FRAME_IN.position_at(i / 400) for i in range(400)))
        z = sign * (r_open + NEON_GAP + NEON_W / 2)
        z = sign * min(abs(z), z_frame - _KEEP_OUT)
        x = 0
        while _inside_frame(x + 1 + NEON_W / 2, z):
            x += 1
        paths.append(Edge.make_line((-x, z), (x, z)))
    return paths


def _frame_paths():
    """Flat arcs that follow the frame's top and bottom edges: a 3-point arc through the
    frame-parallel contour at the centre and at +/-x, grown while it stays inside the frame
    and NEON_GAP clear of the light."""
    contour = base.outline(FRAME_W + _KEEP_OUT + 1).outer_wire()  # +1: off the keep-out line
    pts = [contour.position_at(i / 1440) for i in range(1440)]
    r_min = OPENING_D / 2 + NEON_GAP + NEON_W / 2

    def z_at(x, sign):
        near = [p for p in pts if p.Y * sign > 0 and abs(p.X - x) < 1.0]
        return sign * max(p.Y * sign for p in near)

    def ok(edge):
        for i in range(41):
            p = edge.position_at(i / 40)
            if (p - Vector(0, LIGHT_Z)).length < r_min or not _inside_frame(p.X, p.Y):
                return False
        return 1 / max(_curv(edge, 0.5), 1e-9) >= NEON_MIN_BEND_R

    paths = []
    for sign in (1, -1):
        z0 = z_at(0, sign)
        best = None
        for x in range(20, 90):
            z1 = (z_at(x, sign) + z_at(-x, sign)) / 2
            e = Edge.make_three_point_arc((-x, z1), (0, z0), (x, z1))
            if not ok(e):
                break
            best = e
        paths.append(best)
    return paths


def _curv(edge, t):
    """Curvature at parameter t, from three nearby points."""
    a, b, c = (edge.position_at(min(max(u, 0), 1)) for u in (t - 0.01, t, t + 0.01))
    ab, bc, ca = (b - a).length, (c - b).length, (a - c).length
    area2 = abs((b - a).cross(c - a).Z)
    return 2 * area2 / max(ab * bc * ca, 1e-9)


NEON_STYLES = {"arc": _arc_paths, "frame": _frame_paths, "straight": _straight_paths}


def neon_ends(paths):
    """(x, z, angle) of each groove end, angle = path tangent there in degrees."""
    import math
    out = []
    for e in paths:
        for t in (0, 1):
            p, d = e.position_at(t), e.tangent_at(t)
            out.append((p.X, p.Y, math.degrees(math.atan2(d.Y, d.X))))
    return out


def car_holes():
    z_top, z_bot = base.FLANGE_PROFILE[0][1], base.FLANGE_PROFILE[-1][1]
    x_side = base.half_width(0, 0) - CAR_HOLE_INSET
    return [(0, z_top - CAR_HOLE_INSET), (0, z_bot + CAR_HOLE_INSET), (x_side, 0), (-x_side, 0)]


def snap_planes():
    """One Plane per hook: origin on the hook centre line at the face plate front, x along
    the edge, y pointing inward (toward the keeper wall), z toward the front of the car.
    Found on the +X side and mirrored, so the pattern is exactly symmetric."""
    wire = base.outline(SNAP_INSET).outer_wire()
    pts = [(i / 1440, wire.position_at(i / 1440)) for i in range(1440)]
    planes = []
    for a, b in SNAP_SPOTS:
        if a in ("side", "-side"):
            sx = 1 if a == "side" else -1
            u, p = min(pts, key=lambda q: abs(q[1].Y - b) + (0 if q[1].X > 0 else 1e3))
        else:
            sx = 1 if a > 0 else -1
            u, p = min(pts, key=lambda q: abs(q[1].X - abs(a)) + (0 if q[1].Y * b > 0 else 1e3))
        t = wire.tangent_at(u)
        origin = Vector(sx * p.X, 0, p.Y)
        t3 = Vector(sx * t.X, 0, t.Y)
        y_dir = Vector(0, 1, 0).cross(t3)  # local y = z x x
        if y_dir.dot(Vector(-origin.X, 0, LIGHT_Z - origin.Z)) < 0:
            t3 = -t3
        planes.append(Plane(origin=origin, x_dir=t3, z_dir=(0, 1, 0)))
    return planes


def make(style="frame") -> Part:
    paths = NEON_STYLES[style]()
    post_len = -POST_END_Y - FACE_T
    with BuildPart() as p:
        with BuildSketch(Plane.XZ):
            add(base.outline())
        extrude(amount=FACE_T)  # Plane.XZ normal is -Y: grows toward the engine
        # Aiming posts.
        back = Plane.XZ.offset(FACE_T)
        with BuildSketch(back):
            with Locations(*POSTS.values()):
                Circle(POST_D / 2)
        extrude(amount=post_len)
        # Cone at each post root: spreads the load into the face plate.
        for x, z in POSTS.values():
            with Locations((x, -FACE_T - ROOT_H / 2, z)):
                Cone(ROOT_R, POST_D / 2, ROOT_H, rotation=(90, 0, 0))
        with BuildSketch(back.offset(post_len)):
            with Locations(*POSTS.values()):
                Circle(M5_CLEAR / 2)
        extrude(amount=-25, mode=Mode.SUBTRACT)
        # Nut trap near each post end, slot opening toward the light so the nut slides in.
        with BuildSketch(back.offset(post_len - NUT_FROM_END - M5_NUT_H)):
            for x, z in POSTS.values():
                with Locations((x, z)):
                    RegularPolygon(M5_NUT_AF / 3 ** 0.5, 6)
                with Locations((x - (POST_D / 2) * (1 if x > 0 else -1), z)):
                    Rectangle(POST_D, M5_NUT_AF)
        extrude(amount=M5_NUT_H, mode=Mode.SUBTRACT)
        # Neon grooves: walls behind the face, then the groove from the front.
        for path in paths:
            with BuildSketch(back):
                SlotArc(path, NEON_W + 2 * NEON_WALL)
            extrude(amount=NEON_DEPTH + NEON_WALL - FACE_T)
            with BuildSketch(Plane.XZ):
                SlotArc(path, NEON_W)
            extrude(amount=NEON_DEPTH, mode=Mode.SUBTRACT)
        # End slots through the groove floor for the end caps and cables.
        with BuildSketch(Plane.XZ.offset(NEON_DEPTH)):
            for x, z, ang in neon_ends(paths):
                with Locations(Location((x, z), ang)):
                    Rectangle(NEON_END_HOLE[1], NEON_END_HOLE[0])
        extrude(amount=NEON_WALL, mode=Mode.SUBTRACT)
        # Snap keepers: a wall behind the face beside each slot, with a window for the catch.
        y_wall = SNAP_T / 2 + SNAP_GAP
        for pl in snap_planes():
            with BuildPart(pl, mode=Mode.ADD):
                with Locations((0, y_wall + KEEPER_T / 2, -(FACE_T + KEEPER_LEN) / 2)):
                    Box(SNAP_W + 4, KEEPER_T, KEEPER_LEN - FACE_T)
            with BuildPart(pl, mode=Mode.SUBTRACT):
                win_top, win_bot = SNAP_WINDOW_TOP, SNAP_LEN + 1
                with Locations((0, y_wall + KEEPER_T / 2, -(win_top + win_bot) / 2)):
                    Box(SNAP_W + 0.6, KEEPER_T + 0.2, win_bot - win_top)
                # Slot through the face plate; its inner side is flush with the keeper wall.
                y0 = -SNAP_T / 2 - SNAP_CATCH - 0.1
                with Locations(((0, (y0 + y_wall) / 2, -FACE_T / 2))):
                    Box(SNAP_W + 0.6, y_wall - y0, FACE_T + 0.2)
        # Light opening and car holes.
        with BuildSketch(Plane.XZ):
            with Locations((0, LIGHT_Z)):
                Circle(OPENING_D / 2)
            with Locations(*car_holes()):
                Circle(CAR_HOLE_D / 2)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
        # 90 deg countersinks for M5 flat-head car screws.
        h = (CSK_D - CAR_HOLE_D) / 2
        for x, z in car_holes():
            with Locations((x, -h / 2, z)):
                Cone(CSK_D / 2, CAR_HOLE_D / 2, h, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
    return p.part
