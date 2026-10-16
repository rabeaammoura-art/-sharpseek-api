"""Mercedes W114/W115 Euro headlight retrofit housing — DRAFT with placeholder dimensions.

Replaces the original metal housing + glass lens with a printed housing that carries a
ready-made round light (e.g. 5.75" LED with halo DRL/turn ring).
Two bodies: a rear shell (cup) and a front face plate that holds the light.
Every dimension marked PLACEHOLDER must be measured on the car before printing.
Axes: X = width, Z = height (on the car), Y = depth (front face at Y=0, -Y toward the engine).
"""
from build123d import *

# --- Outer shape (PLACEHOLDER: measure the fender opening) ---
WIDTH = 165          # across the car
HEIGHT = 245         # vertical
CORNER_R = 35
DEPTH = 95           # shell depth behind the face plate
WALL = 3.0

# --- Front face plate ---
FACE_T = 5.0
FLANGE = 6.0         # face plate overhang around the shell (bezel seat / seal land)

# --- Round light (size to be decided; 5.75" sealed LED ≈ 146 mm) ---
LIGHT_D = 146 + 1.0  # cut-out = light body + clearance
LIGHT_Z = 0.0        # light centre height relative to housing centre

# --- Optional windows (set to 0 to drop) ---
TOP_WINDOW = (120, 22)     # indicator strip (W, H); 0 if the light has an amber halo
BOTTOM_WINDOW = (110, 20)  # fog / DRL strip

# --- Fixing ---
SCREW_D = 4.5              # face plate -> shell screws (M4 + clearance)
WIRE_HOLE_D = 20           # rear grommet
TAB_SIZE = (18, 14, 4)     # side mounting tabs to the car (PLACEHOLDER positions)


def outline(w, h, r):
    return RectangleRounded(w, h, r)


def face_plate() -> Part:
    with BuildPart() as face:
        with BuildSketch(Plane.XZ):
            outline(WIDTH + 2 * FLANGE, HEIGHT + 2 * FLANGE, CORNER_R + FLANGE)
        extrude(amount=FACE_T)  # Plane.XZ normal is -Y, so this grows toward the engine
        with BuildSketch(Plane.XZ):
            with Locations((0, LIGHT_Z)):
                Circle(LIGHT_D / 2)
            if TOP_WINDOW[0]:
                with Locations((0, HEIGHT / 2 - 12 - TOP_WINDOW[1] / 2)):
                    RectangleRounded(*TOP_WINDOW, 5)
            if BOTTOM_WINDOW[0]:
                with Locations((0, -HEIGHT / 2 + 12 + BOTTOM_WINDOW[1] / 2)):
                    RectangleRounded(*BOTTOM_WINDOW, 5)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
        # Screw holes into the shell's side walls, above and below the light.
        with BuildSketch(Plane.XZ):
            with Locations(*screw_points()):
                Circle(SCREW_D / 2)
        extrude(amount=FACE_T, mode=Mode.SUBTRACT)
    return face.part


def screw_points():
    x, z = WIDTH / 2 - WALL - 4.5, HEIGHT / 2 - 45
    return [(sx * x, sz * z) for sx in (1, -1) for sz in (1, -1)]


def shell() -> Part:
    with BuildPart() as sh:
        with BuildSketch(Plane.XZ.offset(FACE_T)):
            outline(WIDTH, HEIGHT, CORNER_R)
        extrude(amount=DEPTH)
        # Hollow it out, leaving the front open and the back closed.
        front = sh.faces().sort_by(Axis.Y)[-1]
        offset(amount=-WALL, openings=front)
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
        # Side mounting tabs (to the car body).
        tw, th, tt = TAB_SIZE
        for sx in (1, -1):
            with BuildSketch(Plane.YZ.offset(sx * WIDTH / 2)):
                with Locations((-FACE_T - DEPTH / 2, 0)):
                    Rectangle(th * 2, tw)
            extrude(amount=sx * tw)
        for sx in (1, -1):
            with Locations((sx * (WIDTH / 2 + tw / 2), -FACE_T - DEPTH / 2, 0)):
                Cylinder(SCREW_D / 2, tw, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    return sh.part


def make() -> Part:
    return Compound([shell(), face_plate()])
