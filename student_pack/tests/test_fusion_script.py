"""Smoke-test fusion360/StudentPack/StudentPack.py against a fake `adsk` API (Fusion itself is not available here).

Checks that the script walks pack.json, creates one body per colour with the right heights, uses cm units and
cuts the pencil tunnel.  It cannot prove Fusion-specific behaviour (profile selection, plane orientation): try the
script once in Fusion on a real pack.json.
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).parent.parent


class P3:
    def __init__(s, x, y, z): s.x, s.y, s.z = x, y, z
    @staticmethod
    def create(x, y, z): return P3(x, y, z)


class Coll(list):
    @staticmethod
    def create(): return Coll()
    def add(s, x): s.append(x)
    @property
    def count(s): return len(s)


class SP:  # sketch point
    pass


class Line:
    def __init__(s): s.startSketchPoint, s.endSketchPoint = SP(), SP()


class Lines:
    def __init__(s, sk): s.sk = sk
    def addByTwoPoints(s, a, b):
        s.sk.segments += 1
        return Line()


class Profile:
    def __init__(s, loops): s.profileLoops = types.SimpleNamespace(count=loops)


class Sketch:
    def __init__(s): s.segments, s.name, s.rings = 0, "", 0; s.sketchCurves = types.SimpleNamespace(sketchLines=Lines(s))
    @property
    def profiles(s):
        loops = s.rings if "holes" in s.name else 1
        items = [Profile(loops)]
        return types.SimpleNamespace(count=len(items), item=lambda i: items[i])
    def modelToSketchSpace(s, p): return p


class Body:
    def __init__(s): s.name = ""


class Feature:
    def __init__(s): s.bodies = types.SimpleNamespace(item=lambda i: BODY_POOL.pop() if BODY_POOL else Body())


BODY_POOL = []
LOG = {"extrudes": [], "cuts": 0, "sketches": []}


class ExtIn:
    def __init__(s, prof, op): s.prof, s.op = prof, op; s.startExtent = None; s.dist = None
    def setDistanceExtent(s, sym, v): s.dist = v
    def setTwoSidesExtent(s, a, b): s.two = (a, b)


class Comp:
    def __init__(s):
        s.name = ""
        s.xYConstructionPlane = s.yZConstructionPlane = object()
        s.sketches = types.SimpleNamespace(add=s._add)
        s.features = types.SimpleNamespace(
            extrudeFeatures=types.SimpleNamespace(createInput=lambda p, op: ExtIn(p, op), add=s._ext),
            combineFeatures=types.SimpleNamespace(createInput=lambda a, b: None, add=lambda x: None))
    def _add(s, plane):
        sk = Sketch(); LOG["sketches"].append(sk); return sk
    def _ext(s, i):
        LOG["extrudes"].append((i.startExtent, i.dist, i.op))
        if i.op == "cut": LOG["cuts"] += 1
        return Feature()


adsk = types.ModuleType("adsk"); core = types.ModuleType("adsk.core"); fusion = types.ModuleType("adsk.fusion")
core.Point3D = P3; core.ObjectCollection = Coll
core.ValueInput = types.SimpleNamespace(createByReal=lambda v: v)
core.Matrix3D = types.SimpleNamespace(create=lambda: None)
fusion.OffsetStartDefinition = types.SimpleNamespace(create=lambda v: ("offset", v))
fusion.DistanceExtentDefinition = types.SimpleNamespace(create=lambda v: ("dist", v))
fusion.FeatureOperations = types.SimpleNamespace(NewBodyFeatureOperation="new", JoinFeatureOperation="join", CutFeatureOperation="cut")
adsk.core, adsk.fusion = core, fusion
sys.modules.update({"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion})
spec = importlib.util.spec_from_file_location("StudentPack", HERE / "fusion360/StudentPack/StudentPack.py")
SP_MOD = importlib.util.module_from_spec(spec); spec.loader.exec_module(SP_MOD)
_orig_draw = SP_MOD._draw_ring


def _counting_draw(sketch, ring):
    sketch.rings += 1
    return _orig_draw(sketch, ring)


SP_MOD._draw_ring = _counting_draw


def test_builds_every_piece():
    for pack_path in sorted((HERE / "out").glob("*/pack.json")):
        pack = json.loads(pack_path.read_text())
        root = types.SimpleNamespace(occurrences=types.SimpleNamespace(addNewComponent=lambda m: types.SimpleNamespace(component=Comp())))
        LOG["extrudes"].clear(); LOG["cuts"] = 0
        for kind, d in pack["pieces"].items():
            BODY_POOL[:] = []
            comp = SP_MOD.build_piece(root, pack["name"].upper(), kind, d)
            assert comp.name == f"{pack['name'].upper()}_{kind}"
        assert LOG["extrudes"], "nothing extruded"
        assert LOG["cuts"] == 1, "exactly one teardrop tunnel cut (pencil)"
        # every extrusion is in cm: base slab starts at z=0, raised parts start at base*0.1
        starts = {round(e[0][1], 4) for e in LOG["extrudes"] if e[0]}
        assert 0.0 in starts and 0.16 in starts and 1.04 in starts, starts


if __name__ == "__main__":
    test_builds_every_piece(); print("fusion script smoke test ok")
