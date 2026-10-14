"""Build all new parts: STEP (Fusion 360, solid/parametric source here) + STL, left and right."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from build123d import export_step, export_stl, mirror, Plane, Pos
import params as P
import parts_lib as L

OUT = Path(__file__).parent / "out" / "parts"
PARTS = {   # name: (function, printed?)  -- v2: 2 printed parts + housing per lamp
    "projector_carrier": (L.projector_carrier_v2, True),
    "devil_clamp": (L.devil_clamp, True),
    "PH_projector_ASSUMED": (L.ph_projector, False),
    "PH_projector_lens": (L.ph_projector_lens, False),
    "PH_devil_eye_ASSUMED": (L.ph_devil, False),
}


def right(part):
    return Pos(P.RH_SHIFT_X, 0, 0) * mirror(part, Plane.YZ)


def main(names):
    OUT.mkdir(parents=True, exist_ok=True)
    for n in names or PARTS:
        fn, printed = PARTS[n]
        t = time.time(); p = fn()
        for side, q in (("L", p), ("R", right(p))):
            export_step(q, str(OUT / f"{n}_{side}.step"))
            export_stl(q, str(OUT / f"{n}_{side}.stl"), tolerance=0.02, angular_tolerance=0.1)
        bb = p.bounding_box()
        print(f"{n:24s} vol={p.volume/1000:7.2f} cm3  size={bb.size.X:6.1f} x {bb.size.Y:6.1f} x {bb.size.Z:6.1f}  valid={p.is_valid}  ({time.time()-t:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1:])
