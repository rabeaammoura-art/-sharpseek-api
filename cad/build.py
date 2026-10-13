"""Build every part in parts/: export STEP (for Fusion 360) and STL (for slicing).

Usage: python build.py [part_name ...]
"""
import importlib.util
import sys
from pathlib import Path

from build123d import export_step, export_stl

ROOT = Path(__file__).parent
OUT = ROOT / "out"
sys.path.insert(0, str(ROOT / "parts"))  # parts may share helpers in parts/_*.py


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.make(), getattr(mod, "STL_TOLERANCE", (0.01, 0.1))


def main(names):
    OUT.mkdir(exist_ok=True)
    paths = [ROOT / "parts" / f"{n}.py" for n in names] or sorted(p for p in (ROOT / "parts").glob("*.py") if not p.name.startswith("_"))
    for path in paths:
        part, (tol, ang) = load(path)
        bb = part.bounding_box()
        export_step(part, str(OUT / f"{path.stem}.step"))
        export_stl(part, str(OUT / f"{path.stem}.stl"), tolerance=tol, angular_tolerance=ang)
        print(f"{path.stem}: volume={part.volume:.1f} mm^3  size={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} mm")


if __name__ == "__main__":
    main(sys.argv[1:])
