"""Mercedes W114/W115 Euro headlight retrofit housing — DRAFT, dimensions estimated from photos.

Replaces the original metal housing + glass lens with a printed housing that carries
ready-made round lights (one 5.75" LED, or two 4.5" stacked).
Two bodies: a rear shell (cup) and a front face plate that holds the lights.
Axes: X = width, Z = height (on the car), Y = depth (front face at Y=0, -Y toward the engine).
"""
from build123d import *

# --- Outer outline of the original housing flange (= our face plate) ---
# Traced from the front-view photo of the bare housing, scaled 0.273 mm/px so the
# lens matches the ruler photos (~165 wide, ~260 tall). Accuracy about ±5 mm.
# Wider at the top than the bottom; big round top end, flatter bottom end.
# (half-width X, height Z) from top centre down the right side to bottom centre.
FLANGE_PROFILE = [
    (0.0, 132.1), (13.7, 131.9), (28.7, 130.8), (47.8, 127.2), (61.0, 122.0),
    (71.0, 113.0), (78.5, 100.0), (83.8, 86.3), (89.5, 59.0), (91.7, 31.7),
    (90.1, 4.4), (88.5, -22.9), (86.3, -50.2), (81.4, -77.5), (74.8, -104.8),
    (69.9, -118.5), (65.5, -125.5), (59.0, -130.0), (50.0, -132.0), (25.0, -132.3), (0.0, -132.3),
]
DEPTH = 95           # shell depth behind the face plate (PLACEHOLDER: depends on the light)
WALL = 3.0

# --- Front face plate ---
FACE_T = 5.0
FLANGE = 6.0         # face plate overhang around the shell (bezel seat / seal land)

# --- Round lights: (diameter of light body, centre height from housing centre) ---
LIGHT_CLEARANCE = 1.0      # added to each cut-out diameter
SINGLE_575 = [(146, 0)]    # one 5.75" LED
TWIN_45 = [(114, 60), (114, -60)]  # two 4.5" stacked

# --- Optional windows (W, H, centre Z); W = 0 to drop ---
TOP_WINDOW = (110, 22, 100)      # indicator strip; drop if the light has an amber halo
BOTTOM_WINDOW = (100, 20, -103)  # fog / DRL strip

# --- Fixing ---
SCREW_D = 4.5              # face plate -> shell screws (M4 + clearance)
SCREW_Z = 84               # face screws at +/- this height
WIRE_HOLE_D = 20           # rear grommet
TAB_SIZE = (18, 14, 4)     # side mounting tabs to the car (PLACEHOLDER positions)


def flange_face() -> Face:
    right = [Vector(x, z) for x, z in FLANGE_PROFILE]
    left = [Vector(-x, z) for x, z in reversed(FLANGE_PROFILE[1:-1])]
    return Face(Wire([Edge.make_spline(right + left, periodic=True)]))


_OUTLINES = {}


def outline(inset=0.0) -> Face:
    """Flange outline in sketch coordinates (X, Z), shrunk by `inset` mm.

    Call outside any builder first (done below at import): offset() inside a builder
    would add the result to that builder.
    """
    if inset not in _OUTLINES:
        face = flange_face()
        _OUTLINES[inset] = face if not inset else offset(face, -inset).faces()[0]
    return _OUTLINES[inset]


for _inset in (0.0, FLANGE, FLANGE + WALL):
    outline(_inset)


def half_width(z, inset):
    """Half-width of the outline at height z, measured along +X."""
    probe = Edge.make_line((0, z), (200, z))
    hits = probe.intersect(outline(inset).outer_wire())
    return max(v.X for v in hits.vertices())


def clearances(lights):
    """Smallest gap (mm) from each light cut-out to the shell's inner wall."""
    inner = outline(FLANGE + WALL).outer_wire()
    return [inner.distance_to(Vertex(0, z, 0)) - (d + LIGHT_CLEARANCE) / 2 for d, z in lights]


def screw_points():
    pts = []
    for z in (SCREW_Z, -SCREW_Z):
        x = half_width(z, FLANGE) - WALL - 4.5
        pts += [(x, z), (-x, z)]
    return pts


def face_plate(lights, top_window, bottom_window) -> Part:
    with BuildPart() as face:
        with BuildSketch(Plane.XZ):
            add(outline())
        extrude(amount=FACE_T)  # Plane.XZ normal is -Y, so this grows toward the engine
        with BuildSketch(Plane.XZ):
            for d, z in lights:
                with Locations((0, z)):
                    Circle((d + LIGHT_CLEARANCE) / 2)
            for w, h, z in (top_window, bottom_window):
                if w:
                    with Locations((0, z)):
                        RectangleRounded(w, h, 5)
            with Locations(*screw_points()):
                Circle(SCREW_D / 2)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
    return face.part


def shell() -> Part:
    with BuildPart() as sh:
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            add(outline(FLANGE))
        extrude(amount=DEPTH)
        # Hollow it out, leaving the front open and the back closed.
        # (A 2D inner outline instead of a 3D shell: OCC fails to shell the offset spline.)
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            add(outline(FLANGE + WALL))
        extrude(amount=DEPTH - WALL, mode=Mode.SUBTRACT)
        # Screw bosses inside the rim.
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            with Locations(*screw_points()):
                Circle(5)
        extrude(amount=15)
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            with Locations(*screw_points()):
                Circle(3.3 / 2)  # M4 self-tap / heat-insert pilot
        extrude(amount=15, mode=Mode.SUBTRACT)
        # Rear wire hole.
        with BuildSketch(Plane.XZ.offset(FACE_T + DEPTH)):
            Circle(WIRE_HOLE_D / 2)
        extrude(amount=-WALL * 2, both=True, mode=Mode.SUBTRACT)
        # Side mounting tabs (to the car body), at the widest-but-one point z=0.
        tw, th, tt = TAB_SIZE
        x_side = half_width(0, FLANGE) - 1  # sink 1 mm into the wall so the tab fuses
        for sx in (1, -1):
            with BuildSketch(Plane.YZ.offset(sx * x_side)):
                with Locations((-FACE_T - DEPTH / 2, 0)):
                    Rectangle(th * 2, tw)
            extrude(amount=sx * (tw + 1))
        for sx in (1, -1):
            with Locations((sx * (x_side + 1 + tw / 2), -FACE_T - DEPTH / 2, 0)):
                Cylinder(SCREW_D / 2, tw, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    return sh.part


def make(lights=SINGLE_575, top_window=TOP_WINDOW, bottom_window=BOTTOM_WINDOW) -> Part:
    """Default variant: one 5.75" light with indicator and fog windows."""
    return Compound([shell(), face_plate(lights, top_window, bottom_window)])
