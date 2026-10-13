"""Run MercedesTray.py against a minimal stand-in for the Fusion `adsk` API (backed by
build123d) and compare every body with the geometry used for the STL files.

This proves the script's geometry logic (formulas, units, feature order, booleans) matches
the STL. It cannot prove the real Fusion API accepts every call — run it in Fusion for that.
"""
import importlib.util
import re
import sys
import types
from math import isclose
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "parts"))
from build123d import Circle, Edge, Face, Location, Plane, Vector, Wire, extrude, loft  # noqa: E402

from _mercedes import P, base, handle, tray_bodies  # noqa: E402

# ------------------------------------------------------------------ mock adsk
core, fusion = types.ModuleType("adsk.core"), types.ModuleType("adsk.fusion")
adsk = types.ModuleType("adsk")
adsk.core, adsk.fusion, adsk.doEvents = core, fusion, lambda: None
PARAM_VALUES = {}  # mm


class Point3D:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z

    @staticmethod
    def create(x, y, z):
        return Point3D(x, y, z)

    def mm(self):
        return (self.x * 10, self.y * 10, self.z * 10)


class ValueInput:
    def __init__(self, mm):
        self.mm = mm

    @staticmethod
    def createByReal(v):
        return ValueInput(v * 10)

    @staticmethod
    def createByString(s):
        expr = s.replace("mm", "")
        for name in sorted(PARAM_VALUES, key=len, reverse=True):
            expr = re.sub(rf"\b{name}\b", repr(PARAM_VALUES[name]), expr)
        return ValueInput(float(eval(expr, {"__builtins__": {}})))


class ObjectCollection(list):
    @staticmethod
    def create():
        return ObjectCollection()

    def add(self, o):
        self.append(o)


class Matrix3D:
    @staticmethod
    def create():
        return Matrix3D()


core.Point3D, core.ValueInput, core.ObjectCollection, core.Matrix3D = Point3D, ValueInput, ObjectCollection, Matrix3D


class FeatureOperations:
    NewBodyFeatureOperation, JoinFeatureOperation, CutFeatureOperation = "new", "join", "cut"


class DesignTypes:
    ParametricDesignType = "parametric"


fusion.FeatureOperations, fusion.DesignTypes = FeatureOperations, DesignTypes


class CPlane:
    def __init__(self, plane: Plane):
        self.plane = plane


class PlaneInput:
    def setByOffset(self, base, vi):
        p = base.plane
        self._plane = CPlane(Plane(origin=p.origin + p.z_dir * vi.mm, x_dir=p.x_dir, z_dir=p.z_dir))


class Profile:
    def __init__(self, sketch, face=None):
        self.sketch, self._face = sketch, face

    def areaProperties(self):
        return types.SimpleNamespace(area=self.face().area / 100.0)  # cm^2

    def face(self):
        if self._face is not None:
            return self._face
        curves = self.sketch.curves
        if len(curves) == 1 and curves[0][0] == "circle":
            _, c, r = curves[0]
            pl = self.sketch.plane.plane
            return Face(Circle(r).wrapped).moved(Location(Plane(origin=c, x_dir=pl.x_dir, z_dir=pl.z_dir).location))
        return Face(Wire([e for _, e in curves]))


class Curves:
    def __init__(self, sk):
        self.sk = sk
        self.sketchLines = types.SimpleNamespace(addByTwoPoints=self.line, addTwoPointRectangle=self.rect)
        self.sketchArcs = types.SimpleNamespace(addByThreePoints=self.arc)
        self.sketchCircles = types.SimpleNamespace(addByCenterRadius=self.circle)

    def line(self, a, b):
        self.sk.curves.append(("edge", Edge.make_line(a.mm(), b.mm())))
        self.sk.segments.append((a.mm(), b.mm()))
        return types.SimpleNamespace(startSketchPoint=a, endSketchPoint=b)

    def arc(self, a, m, b):
        self.sk.curves.append(("edge", Edge.make_three_point_arc(a.mm(), m.mm(), b.mm())))

    def circle(self, c, r):
        self.sk.curves.append(("circle", Vector(*c.mm()), r * 10))

    def rect(self, a, b):
        (x0, y0, z), (x1, y1, _) = a.mm(), b.mm()
        pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
        for i in range(4):
            self.line(Point3D(*[v / 10 for v in pts[i]]), Point3D(*[v / 10 for v in pts[(i + 1) % 4]]))


class Sketch:
    def __init__(self, plane):
        self.plane, self.curves, self.segments = plane, [], []
        self.isComputeDeferred = False
        self.sketchCurves = Curves(self)

    @property
    def profiles(self):
        """One closed loop -> one profile. Many line loops -> every enclosed region, like Fusion."""
        if len(self.curves) == len(self.segments) and self._loop_count() > 1:
            from shapely.geometry import LineString
            from shapely.ops import polygonize
            z = self.segments[0][0][2]
            regions = list(polygonize([LineString([a[:2], b[:2]]) for a, b in self.segments]))
            profs = []
            for poly in regions:
                ow = Wire.make_polygon([(x, y, z) for x, y in list(poly.exterior.coords)[:-1]], close=True)
                hw = [Wire.make_polygon([(x, y, z) for x, y in list(h.coords)[:-1]], close=True) for h in poly.interiors]
                profs.append(Profile(self, Face(ow, hw)))
        else:
            profs = [Profile(self)]
        return types.SimpleNamespace(count=len(profs), item=lambda i: profs[i])

    def _loop_count(self):
        # a loop closes when a segment ends where the loop's first segment started
        loops, start = 0, None
        for a, b in self.segments:
            if start is None:
                start = a
            if all(abs(u - v) < 1e-9 for u, v in zip(b, start)):
                loops, start = loops + 1, None
        return loops

    def modelToSketchSpace(self, p):  # mock keeps model coordinates; checks the point is on the plane
        pl = self.plane.plane
        dist = (Vector(*p.mm()) - pl.origin).dot(pl.z_dir)
        assert abs(dist) < 1e-6, f"point {p.mm()} is {dist} mm off its sketch plane"
        return p


class Body:
    def __init__(self, shape, comp):
        self.shape, self.name = shape, None
        comp.bodies.append(self)


class Features:
    def __init__(self, comp):
        self.comp = comp
        self.extrudeFeatures = types.SimpleNamespace(addSimple=self.add_simple, createInput=self.ext_input,
                                                     add=self.ext_add)
        self.loftFeatures = types.SimpleNamespace(createInput=self.loft_input, add=self.loft_add)
        self.combineFeatures = types.SimpleNamespace(createInput=self.comb_input, add=self.comb_add)

    @staticmethod
    def _result(body):
        return types.SimpleNamespace(bodies=types.SimpleNamespace(count=1, item=lambda i: body))

    def add_simple(self, prof, vi, op):
        assert op == "new"
        profs = list(prof) if isinstance(prof, ObjectCollection) else [prof]
        bodies = [Body(s, self.comp) for p in profs
                  for s in extrude(p.face(), vi.mm, dir=p.sketch.plane.plane.z_dir).solids()]
        if len(bodies) == 1:
            return self._result(bodies[0])
        return types.SimpleNamespace(bodies=types.SimpleNamespace(count=len(bodies), item=lambda i: bodies[i]))

    def ext_input(self, prof, op):
        inp = types.SimpleNamespace(prof=prof, sym=None)
        inp.setSymmetricExtent = lambda vi, full: setattr(inp, "sym", (vi.mm, full))
        return inp

    def ext_add(self, inp):
        length, full = inp.sym
        assert full
        face = inp.prof.face()
        n = inp.prof.sketch.plane.plane.z_dir
        return self._result(Body(extrude(face.moved(Location(-n * length / 2)), length, dir=n), self.comp))

    def loft_input(self, op):
        secs = []
        return types.SimpleNamespace(loftSections=types.SimpleNamespace(add=secs.append), secs=secs, isSolid=False)

    def loft_add(self, inp):
        assert inp.isSolid
        return self._result(Body(loft([p.face() for p in inp.secs], ruled=True), self.comp))

    def comb_input(self, target, tools):
        return types.SimpleNamespace(target=target, tools=tools, operation=None, isKeepToolBodies=True)

    def comb_add(self, inp):
        s = inp.target.shape
        for t in inp.tools:
            s = s - t.shape if inp.operation == "cut" else s + t.shape
            if not inp.isKeepToolBodies:
                self.comp.bodies.remove(t)
        inp.target.shape = s


class Component:
    def __init__(self):
        self.name, self.bodies = None, []
        self.xYConstructionPlane = CPlane(Plane.XY)
        self.yZConstructionPlane = CPlane(Plane.YZ)
        self.constructionPlanes = types.SimpleNamespace(createInput=PlaneInput, add=lambda inp: inp._plane)
        self.sketches = types.SimpleNamespace(add=Sketch)
        self.features = Features(self)
        self.children = []
        self.occurrences = types.SimpleNamespace(addNewComponent=self._new)

    def _new(self, m):
        c = Component()
        self.children.append(c)
        return types.SimpleNamespace(component=c)


class UserParameters:
    def __init__(self):
        self.items = {}

    def itemByName(self, n):
        return self.items.get(n)

    def add(self, name, vi, units, comment):
        assert units in ("mm", ""), units
        PARAM_VALUES[name] = vi.mm  # createByString evaluated the expression in mm / unitless
        self.items[name] = types.SimpleNamespace(value=vi.mm / 10 if units == "mm" else vi.mm)
        return self.items[name]


class Design:
    def __init__(self):
        self.rootComponent, self.userParameters, self.designType = Component(), UserParameters(), None

    @staticmethod
    def cast(o):
        return o


fusion.Design = Design
sys.modules.update({"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion})


# ------------------------------------------------------------------ run & compare
def main():
    spec = importlib.util.spec_from_file_location("MercedesTray", HERE / "MercedesTray" / "MercedesTray.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # parameter defaults must equal the STL model's Params
    for name, (val, _, _) in mod.PARAMS.items():
        ref = getattr(P, name[:-1])[int(name[-1])] if name[:-1] in ("pocket_x", "pocket_y") else getattr(P, name)
        assert isclose(ref, val), f"param {name}: fusion {val} != stl {ref}"
    assert tuple(mod.COMPARTMENT_ANGLES) == tuple(P.compartment_angles)

    # decor.json next to the script must be the current decoration (no stale copy)
    import json
    import tempfile
    from _decor import export_json
    with tempfile.NamedTemporaryFile("r", suffix=".json") as f:
        export_json(P, f.name)
        fresh = json.load(open(f.name))
    assert json.load(open(HERE / "MercedesTray" / "decor.json")) == fresh, "decor.json is stale: run make mercedes"

    design = Design()
    g = mod.build(design)
    assert g.n_rings == P.n_rings, (g.n_rings, P.n_rings)
    fusion_bodies = {b.name: b.shape for c in design.rootComponent.children for b in c.bodies}
    ref = dict(tray_bodies(P, 0.0))
    ref["handle"] = handle(P, 0)
    ref["base"] = base(P)
    assert set(fusion_bodies) == set(ref), set(fusion_bodies) ^ set(ref)

    worst = 0.0
    for name, r in ref.items():
        f = fusion_bodies[name]
        diff = (f - r).volume + (r - f).volume
        worst = max(worst, diff / r.volume)
        assert diff / r.volume < 1e-6, f"{name}: symmetric difference {diff:.4f} mm^3"
    print(f"PASS: Fusion script == STL geometry for all {len(ref)} bodies "
          f"(params identical, N = {g.n_rings}, max relative symmetric difference {worst:.1e})")


if __name__ == "__main__":
    main()
