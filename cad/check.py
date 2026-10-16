"""Assembly checks for the one-piece retrofit, both sides: no part overlaps another, the
light (141 dia, 60 to the pads) clears the housing, the bracket ears line up with the posts,
and every snap catch sits in its keeper window.

Usage: python check.py
"""
import sys
from pathlib import Path

from build123d import Cylinder, Vector

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
    ok = True
    for side, housing, bracket, sx in (("right", op.make(), br.make(), 1), ("left", op_l.make(), br_l.make(), -1)):
        results = {
            "housing x ring": overlap(housing, r),
            "housing x bracket": overlap(housing, bracket),
            "housing x light": overlap(housing, light),
            "ring x light": overlap(r, light),
        }
        for name, v in results.items():
            flag = v < 1e-3
            ok &= flag
            print(f"{side:5} {name:18} {'ok' if flag else f'OVERLAP {v:.3f} mm3'}")
        y_ear = -op.PAD_DEPTH - br.T / 2
        ears = all(not bracket.is_inside(Vector(sx * x, y_ear, z)) for x, z in op.POSTS.values())
        catches = all(not housing.is_inside(pl.from_local_coords(Vector(0, op.SNAP_T / 2 + 0.4, -op.SNAP_CATCH_Z - 0.3)))
                      and r.is_inside(pl.from_local_coords(Vector(0, op.SNAP_T / 2 + 0.4, -op.SNAP_CATCH_Z - 0.3)))
                      for pl in op.snap_planes())
        ok &= ears and catches
        print(f"{side:5} {'ear holes on posts':18} {'ok' if ears else 'MISALIGNED'}")
        print(f"{side:5} {'catches in windows':18} {'ok' if catches else 'WRONG'}")
    print("ALL OK" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
