"""STEP deliverables: faceted STEP of each modified housing (mesh-derived — Fusion: open, then
Mesh > Convert Mesh if you need B-rep features) and a full left/right assembly STEP."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from OCP.StlAPI import StlAPI_Reader
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS
from OCP.TopAbs import TopAbs_SHELL
from OCP.TopExp import TopExp_Explorer
from build123d import import_step, export_step, Compound, Solid, Shape
import geom as G

OUT = G.OUT; PT = OUT / "parts"; STEP = OUT / "step"; STEP.mkdir(exist_ok=True)


def stl_to_solid(path):
    sh = TopoDS_Shape(); StlAPI_Reader().Read(sh, str(path))
    sew = BRepBuilderAPI_Sewing(1e-3); sew.Add(sh); sew.Perform(); sewn = sew.SewedShape()
    ex = TopExp_Explorer(sewn, TopAbs_SHELL); mk = BRepBuilderAPI_MakeSolid()
    while ex.More():
        mk.Add(TopoDS.Shell(ex.Current())); ex.Next()
    return Solid(mk.Solid())


for s in "LR":
    # The housing is mesh-derived (original supplied as STL): a faceted STEP is ~110 MB and fails B-rep checks,
    # so the housing ships as STL; the assembly STEP holds every new solid part in its installed position.
    parts = [import_step(str(p)) for p in sorted(PT.glob(f"*_{s}.step"))]
    export_step(Compound(children=parts), str(STEP / f"assembly_new_parts_{s}.step"))
    print("assembly", s, "solids", len(parts))
