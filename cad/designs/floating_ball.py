"""Floating ball: a 40 mm ping-pong ball glued on the spin axis. See spiral.py for the trick."""
from build123d import *

from spiral import Spiral

BALL_D = 40.0  # standard ping-pong ball

SPIRAL = Spiral(payload_r=BALL_D / 2, helix_h=90.0)


def ball() -> Part:
    return Sphere(BALL_D / 2).moved(Location((0, 0, SPIRAL.contact_z)))


def base() -> Part:
    return SPIRAL.base()


def rotor() -> Part:
    return SPIRAL.rotor(ball())


def ring() -> Part:
    return SPIRAL.ring()


def assembly() -> Compound:
    return SPIRAL.assembly(rotor(), ball())
