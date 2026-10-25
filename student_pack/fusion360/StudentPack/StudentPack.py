"""Fusion 360 script: build the 3D ZONE TECH student pack from pack.json (written by student_pack/generate.py).

Install: Fusion 360 > Utilities > Add-Ins > Scripts and Add-Ins > "+" next to My Scripts > pick this folder
(fusion360/StudentPack).  Run it, choose pack.json (e.g. out/OSAYD_construction/pack.json).

For every piece in pack.json it creates one component "<name>_<piece>" that contains one solid body per colour,
named by colour ("black", "yellow", ...).  Each body is the exact polygon set from the generator extruded from the
base height to that colour's own height (the outline-colour body also carries the full-silhouette base slab).  Hanging
holes are already cut in the polygons; the pencil plate gets its horizontal teardrop tunnel as a real cut feature.
Units: pack.json is in mm; the Fusion API works in cm, hence the / 10.
"""
import json
import traceback

import adsk.core
import adsk.fusion

MM = 0.1          # mm -> cm


def _pt(x, y, z=0.0):
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def _draw_ring(sketch, ring):
    """Closed polyline from [[x, y], ...] (mm)."""
    lines = sketch.sketchCurves.sketchLines
    pts = [adsk.core.Point3D.create(x * MM, y * MM, 0) for x, y in ring]
    first = lines.addByTwoPoints(pts[0], pts[1])
    prev = first
    for p in pts[2:]:
        prev = lines.addByTwoPoints(prev.endSketchPoint, p)
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _extrude(comp, sketch, profiles, z0, z1, operation, bodies=None):
    coll = adsk.core.ObjectCollection.create()
    for p in profiles:
        coll.add(p)
    if coll.count == 0:
        return None
    ext_in = comp.features.extrudeFeatures.createInput(coll, operation)
    ext_in.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(z0 * MM))
    ext_in.setDistanceExtent(False, adsk.core.ValueInput.createByReal((z1 - z0) * MM))
    if bodies:
        ext_in.participantBodies = bodies
    return comp.features.extrudeFeatures.add(ext_in)


def _profiles_for(sketch, n_loops_wanted):
    """Profiles of `sketch` whose loop count equals n_loops_wanted (outer + holes => the solid ring, not the hole islands)."""
    out = []
    for i in range(sketch.profiles.count):
        prof = sketch.profiles.item(i)
        if prof.profileLoops.count == n_loops_wanted:
            out.append(prof)
    return out


def build_region(comp, name, polys, z0, z1, operation=None, bodies=None):
    """Extrude a list of {"ext": ring, "holes": [ring...]} polygons.  Polygons without holes share one sketch; a polygon
    with holes gets its own sketch so the hole islands can be told apart from the solid."""
    op = operation if operation is not None else adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    feats = []
    simple = [p for p in polys if not p["holes"]]
    complex_ = [p for p in polys if p["holes"]]
    xy = comp.xYConstructionPlane
    if simple:
        sk = comp.sketches.add(xy)
        sk.name = f"{name} outlines"
        for p in simple:
            _draw_ring(sk, p["ext"])
        feats.append(_extrude(comp, sk, _profiles_for(sk, 1), z0, z1, op, bodies))
    for k, p in enumerate(complex_):
        sk = comp.sketches.add(xy)
        sk.name = f"{name} outline+holes {k + 1}"
        _draw_ring(sk, p["ext"])
        for h in p["holes"]:
            _draw_ring(sk, h)
        feats.append(_extrude(comp, sk, _profiles_for(sk, 1 + len(p["holes"])), z0, z1, op, bodies))
    return [f for f in feats if f]


def build_piece(root, pack_name, kind, d):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = f"{pack_name}_{kind}"
    base, tops, outline = d["base"], d["tops"], d["outline"]
    bodies = {}
    # outline colour: full-silhouette slab, then its raised parts joined to it
    slab = build_region(comp, f"{outline} base", d["silhouette"], 0.0, base)
    body = slab[0].bodies.item(0)
    body.name = outline
    bodies[outline] = body
    if outline in d["parts"]:
        build_region(comp, f"{outline} raised", d["parts"][outline], base, tops[outline],
                     adsk.fusion.FeatureOperations.JoinFeatureOperation, [body])
    for color in d["order"]:
        if color == outline or color not in d["parts"]:
            continue
        feats = build_region(comp, color, d["parts"][color], base, tops[color])
        # several features (one per sketch) -> merge into one body named by colour
        first = feats[0].bodies.item(0)
        for f in feats[1:]:
            tools = adsk.core.ObjectCollection.create()
            tools.add(f.bodies.item(0))
            comp.features.combineFeatures.add(comp.features.combineFeatures.createInput(first, tools))
        first.name = color
        bodies[color] = first
    if d.get("tunnel"):
        _cut_tunnel(comp, d, body)
    return comp


def _cut_tunnel(comp, d, body):
    """Horizontal teardrop tunnel along X: circle d, apex up (45 deg), apex cut flat so the roof stays inside the plate."""
    import math
    t = d["tunnel"]
    r, zc, y0, roof = t["d"] / 2, t["zc"], t["y"], t["roof_cut"]
    c = r / math.sqrt(2)
    pts = []
    # circle arc from the right tangent point round the bottom to the left tangent point, then up the 45 deg flanks
    a0, a1 = math.radians(45), math.radians(135)
    n = 48
    for i in range(n + 1):
        a = a0 - (2 * math.pi - (a1 - a0)) * i / n          # from +45 deg clockwise to 135 deg (through the bottom)
        pts.append((y0 + r * math.cos(a), zc + r * math.sin(a)))
    half = r * math.sqrt(2) - roof                          # half width of the flat roof
    pts.append((y0 - half, zc + roof))
    pts.append((y0 + half, zc + roof))
    sk = comp.sketches.add(comp.yZConstructionPlane)
    sk.name = "pencil tunnel"
    lines = sk.sketchCurves.sketchLines
    sp = [sk.modelToSketchSpace(_pt(0, y, z)) for y, z in pts]      # robust to the plane's axis orientation
    first = lines.addByTwoPoints(sp[0], sp[1])
    prev = first
    for p in sp[2:]:
        prev = lines.addByTwoPoints(prev.endSketchPoint, p)
    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    L = d["size_mm"][0] + 4
    ext_in = comp.features.extrudeFeatures.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext_in.setTwoSidesExtent(adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(L * MM)),
                             adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByReal(L * MM)))
    ext_in.participantBodies = [body]
    comp.features.extrudeFeatures.add(ext_in)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        dlg = ui.createFileDialog()
        dlg.title = "Choose pack.json from student_pack/out/<NAME>_<theme>/"
        dlg.filter = "pack.json (*.json)"
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        pack = json.load(open(dlg.filename))
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.DirectDesignType      # no timeline: faster, bodies stay plain solids
        root = design.rootComponent
        for kind, d in pack["pieces"].items():
            build_piece(root, pack["name"].upper(), kind, d)
        ui.messageBox(f"Built {len(pack['pieces'])} pieces for {pack['name']} ({pack['theme']}).\n"
                      "Export each component as 3MF/STL or use Make > 3D Print.")
    except Exception:
        if ui:
            ui.messageBox("Student pack failed:\n" + traceback.format_exc())
