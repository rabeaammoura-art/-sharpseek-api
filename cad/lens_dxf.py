"""Export the lamp-box lens outlines (top = indicator, bottom = fog) as DXF for cutting
2 mm clear polycarbonate by laser/CNC, or as a printable 1:1 paper template (SVG).

Usage: python lens_dxf.py   -> out/lens_top.dxf, out/lens_bottom.dxf (+ .svg)
"""
import sys
from pathlib import Path

from build123d import ExportDXF, ExportSVG, Unit, offset

sys.path.insert(0, str(Path(__file__).parent / "parts"))
import retrofit_onepiece as op  # noqa: E402

FIT = 0.3  # lens is this much smaller than its pocket all round

for name, pocket in zip(("top", "bottom"), op.LENS):
    lens = offset(pocket, -FIT).faces()[0]
    for exporter, ext in ((ExportDXF(unit=Unit.MM), "dxf"), (ExportSVG(unit=Unit.MM), "svg")):
        exporter.add_shape(lens.outer_wire())
        exporter.write(f"out/lens_{name}.{ext}")
    bb = lens.bounding_box()
    print(f"lens_{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} mm")
