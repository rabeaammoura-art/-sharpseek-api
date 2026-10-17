"""Assembly checks for the one-piece retrofit, both sides: no part overlaps another, the
light (141 dia, 60 to the pads) clears the housing, the bracket ears line up with the posts,
and the ring's top lip and bottom screw land on the housing.

Usage: python check.py
"""
import sys
from pathlib import Path

from build123d import Cylinder, Plane, Vector, extrude

sys.path.insert(0, str(Path(__file__).parent / "parts"))
import retrofit_onepiece as op  # noqa: E402
import retrofit_onepiece_bracket as br  # noqa: E402
import retrofit_onepiece_bracket_left as br_l  # noqa: E402
import retrofit_onepiece_gasket as gasket  # noqa: E402
import retrofit_onepiece_left as op_l  # noqa: E402
import retrofit_onepiece_ring as ring  # noqa: E402


def solid_at(part, p, size=0.4):
    """Robust point test (is_inside is flaky on some mirrored spline solids)."""
    from build123d import Box, Pos
    i = part & (Pos(p.X, p.Y, p.Z) * Box(size, size, size))
    return i is not None and sum(s.volume for s in i.solids()) > 0.5 * size ** 3


def overlap(a, b):
    i = a & b
    return 0.0 if i is None else sum(s.volume for s in i.solids())


def main():
    light = Cylinder(op.LIGHT_D / 2, op.PAD_DEPTH, rotation=(90, 0, 0)).translate((0, -op.PAD_DEPTH / 2, 0))
    r = ring.make()
    g = gasket.make()
    # Outside the rear rib the housing's back sits on the fender: nothing may stick out there.
    # (0.1 mm off the rib's face: the mirrored spline differs from the original by a hair.)
    zone = op.base.outline() - op.base.outline(op._RIB_IN - 0.1)
    fender = extrude(Plane.XZ.offset(op.FACE_T) * zone, -60)  # toward the engine
    ok = True
    for side, housing, bracket, sx in (("right", op.make(), br.make(), 1), ("left", op_l.make(), br_l.make(), -1)):
        results = {
            "housing x ring": overlap(housing, r),
            "housing x bracket": overlap(housing, bracket),
            "housing x light": overlap(housing, light),
            "ring x light": overlap(r, light),
            "housing x fender": overlap(housing, fender),
            "housing x gasket": overlap(housing, g),
            "ring x gasket": overlap(r, g),
        }
        for name, v in results.items():
            flag = v < 1e-3
            ok &= flag
            print(f"{side:5} {name:18} {'ok' if flag else f'OVERLAP {v:.3f} mm3'}")
        y_ear = -op.PAD_DEPTH - br.T / 2
        ears = all(not solid_at(bracket, Vector(sx * x, y_ear, z)) for x, z in op.POSTS.values())
        x, z = op.ring_screw()
        screw = (not solid_at(housing, Vector(x, -2, z)) and not solid_at(r, Vector(x, 1.5, z))
                 and solid_at(housing, Vector(x + op.RING_SCREW_PILOT, -2, z)))
        lip_z = max(p.Y for p in (op.base.outline().outer_wire().position_at(i / 720) for i in range(720)))
        lip_p = Vector(0, -op.FACE_T + op.LIP_T / 2, lip_z - 1)
        lip = solid_at(r, lip_p) and not solid_at(housing, lip_p)
        ok &= ears and screw and lip
        print(f"{side:5} {'ear holes on posts':18} {'ok' if ears else 'MISALIGNED'}")
        print(f"{side:5} {'ring screw hole':18} {'ok' if screw else 'WRONG'}")
        print(f"{side:5} {'ring top lip':18} {'ok' if lip else 'WRONG'}")
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
