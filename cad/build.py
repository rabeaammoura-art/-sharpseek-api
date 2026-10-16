"""Build every part in parts/: export STEP (Fusion 360), STL and 3MF (Bambu Studio).

STEP keeps the part in car coordinates. STL/3MF are laid out for printing: a part module
may set PRINT_ROTATION = (axis, degrees) to turn it onto its print face; the result is
dropped onto the bed (min Z = 0) and centred.

Usage: python build.py [part_name ...]
"""
import importlib.util
import sys
from pathlib import Path

from build123d import Axis, Mesher, Vector, export_step, export_stl

ROOT = Path(__file__).parent
OUT = ROOT / "out"
# Bambu Lab H2D, single-nozzle printable volume (mm).
BED = (325, 320, 325)


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.make(), mod


def _wants_build(path: Path) -> bool:
    """Modules can opt out of `make` (build everything) with BUILD = False."""
    return "BUILD = False" not in path.read_text()


def for_print(part, mod):
    rot = getattr(mod, "PRINT_ROTATION", None)
    if rot:
        axis, deg = rot
        part = part.rotate({"X": Axis.X, "Y": Axis.Y, "Z": Axis.Z}[axis], deg)
    bb = part.bounding_box()
    return part.translate(Vector(-bb.center().X, -bb.center().Y, -bb.min.Z))


def main(names):
    OUT.mkdir(exist_ok=True)
    paths = [ROOT / "parts" / f"{n}.py" for n in names] or sorted((ROOT / "parts").glob("*.py"))
    for path in paths:
        if not names and not _wants_build(path):
            continue
        part, mod = load(path)
        export_step(part, str(OUT / f"{path.stem}.step"))
        printed = for_print(part, mod)
        bb = printed.bounding_box()
        export_stl(printed, str(OUT / f"{path.stem}.stl"), tolerance=0.01, angular_tolerance=0.1)
        mesher = Mesher()
        mesher.add_shape(printed, linear_deflection=0.01, angular_deflection=0.1)
        mesher.write(str(OUT / f"{path.stem}.3mf"))
        print(f"{path.stem}: volume={part.volume:.1f} mm^3  print size={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} mm")
        # Footprint may be rotated on the bed, so compare sorted dimensions.
        fits_xy = all(a <= b for a, b in zip(sorted((bb.size.X, bb.size.Y)), sorted(BED[:2])))
        if not fits_xy or bb.size.Z > BED[2]:
            print(f"  WARNING: {path.stem} does not fit the H2D bed {BED[0]}x{BED[1]}x{BED[2]} mm")


if __name__ == "__main__":
    main(sys.argv[1:])
