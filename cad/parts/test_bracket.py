"""Test part: L-shaped bracket with two mounting holes and a fillet."""
from build123d import *

THICKNESS = 4
WIDTH = 30
LEG = 40
HOLE_D = 5


def make() -> Part:
    with BuildPart() as bracket:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline((0, 0), (LEG, 0), (LEG, THICKNESS), (THICKNESS, THICKNESS),
                         (THICKNESS, LEG), (0, LEG), close=True)
            make_face()
        extrude(amount=-WIDTH)
        # Fillet the inner corner of the L for strength.
        inner = [e for e in bracket.edges().filter_by(Axis.Y)
                 if abs(e.center().X - THICKNESS) < 1e-6 and abs(e.center().Z - THICKNESS) < 1e-6]
        fillet(inner, radius=3)
        with Locations((LEG * 0.65, WIDTH / 2, THICKNESS)):
            Hole(HOLE_D / 2)
        with Locations(Location((0, WIDTH / 2, LEG * 0.65), (0, 90, 0))):
            Hole(HOLE_D / 2)
    return bracket.part
