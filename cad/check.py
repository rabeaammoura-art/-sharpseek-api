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
import retrofit_onepiece_left as op_l  # noqa: E402
import retrofit_onepiece_ring as ring  # noqa: E402


def overlap(a, b):
    i = a & b
    return 0.0 if i is None else sum(s.volume for s in i.solids())


def main():
    light = Cylinder(op.LIGHT_D / 2, op.PAD_DEPTH, rotation=(90, 0, 0)).translate((0, -op.PAD_DEPTH / 2, 0))
    r = ring.make()
    # Outside the rear rib the housing's back sits on the fender: nothing may stick out there.
    fender = extrude(Plane.XZ.offset(op.FACE_T) * (op.base.outline() - op.base.outline(op._RIB_IN)), 60)
    ok = True
    for side, housing, bracket, sx in (("right", op.make(), br.make(), 1), ("left", op_l.make(), br_l.make(), -1)):
        results = {
            "housing x ring": overlap(housing, r),
            "housing x bracket": overlap(housing, bracket),
            "housing x light": overlap(housing, light),
            "ring x light": overlap(r, light),
            "housing x fender": overlap(housing, fender),
        }
        for name, v in results.items():
            flag = v < 1e-3
            ok &= flag
            print(f"{side:5} {name:18} {'ok' if flag else f'OVERLAP {v:.3f} mm3'}")
        y_ear = -op.PAD_DEPTH - br.T / 2
        ears = all(not bracket.is_inside(Vector(sx * x, y_ear, z)) for x, z in op.POSTS.values())
        x, z = op.ring_screw()
        screw = (not housing.is_inside(Vector(x, -2, z)) and not r.is_inside(Vector(x, 1.5, z))
                 and housing.is_inside(Vector(x + op.RING_SCREW_PILOT, -2, z)))
        lip_z = max(p.Y for p in (op.base.outline().outer_wire().position_at(i / 720) for i in range(720)))
        lip = r.is_inside(Vector(0, -op.FACE_T + op.LIP_T / 2, lip_z - 1)) and not housing.is_inside(
            Vector(0, -op.FACE_T + op.LIP_T / 2, lip_z - 1))
        ok &= ears and screw and lip
        print(f"{side:5} {'ear holes on posts':18} {'ok' if ears else 'MISALIGNED'}")
        print(f"{side:5} {'ring screw hole':18} {'ok' if screw else 'WRONG'}")
        print(f"{side:5} {'ring top lip':18} {'ok' if lip else 'WRONG'}")
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
