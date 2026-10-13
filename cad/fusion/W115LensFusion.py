"""Fusion 360 script: Mercedes W114/W115 late-series rear lamp lens (Euro), RH + mirrored LH.

Scripts and Add-Ins -> Scripts -> "+" -> pick this folder -> Run, in a NEW empty design.
Edit P below and re-run to change the size; the values are also written to
Modify -> Change Parameters (as user parameters) for reference.

Geometry matches cad/parts/w115_lens.py (the reference model, exported as STEP):
outer section extruded + revolved (amber wrap), plan / front-view trims, shell open at
the back, interior walls / stop-lamp box / insert bosses, then split into red, clear,
amber bodies with zero gap for a one-shot multi-material print.
Coordinates: X along the lens (0 = inboard end), Y depth (- = outward), Z up.
Difference from the reference: Fusion's Shell leaves a back rim of width t (3 mm);
the reference model widens it to flange_w (6 mm) as a seal flange.
NOTE: written against the documented Fusion API but not run inside Fusion here.
"""
import math
import traceback

import adsk.core
import adsk.fusion

P = dict(
    L_proj=325.0, H=140.0, lip_h=13.0, n_ribs=4,
    nose_R=6.0, shoulder_h=5.0, face_lean=2.0, rib_P0=10.0, rib_step=3.0,
    D_back=28.0, t=3.0,
    red_w=100.0, mid_w=120.0, A_wrap=50.0, R_end=25.0,
    r_in_top=25.0, r_in_bot=5.0, r_out_top=8.0, r_out_bot=30.0,
    wall_t=2.5, wall_backoff=6.0, box_cap_y=8.0,
    stud_x1=97.0, stud_dx=130.0, stud_from_top=73.0,
    boss_d=11.0, boss_back=4.0, insert_d=6.4, insert_depth=10.0,
)

CM = 0.1  # Fusion API works in cm


def derived(p):
    d = dict(p)
    d["pitch"] = (p["H"] - p["lip_h"]) / p["n_ribs"]
    d["P_max"] = p["rib_P0"] + (p["n_ribs"] - 1) * p["rib_step"]
    d["xs"] = p["red_w"] + p["mid_w"]
    d["A"] = math.radians(p["A_wrap"])
    d["Rg"] = (p["L_proj"] - d["xs"]) / math.sin(d["A"]) - d["P_max"]
    d["clear_top"] = d["pitch"] + 2 * p["nose_R"]
    d["box_top"] = p["H"] - p["lip_h"] - 2.0
    return d


def P3(x, y, z):
    return adsk.core.Point3D.create(x * CM, y * CM, z * CM)


def section_segments(d):
    """Outer section as ('L', (y,z), (y,z)) / ('A', start, mid, end) in mm, (y=depth, z=height)."""
    H, r, D = d["H"], d["nose_R"], d["D_back"]
    segs = [("L", (D, H), (0, H)), ("L", (0, H), (0, H - d["lip_h"]))]
    c45 = r * (1 - math.cos(math.pi / 4))
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * d["pitch"]
        zb = zt - d["pitch"]
        Pi = d["rib_P0"] + i * d["rib_step"]
        sh, fl = d["shoulder_h"], d["face_lean"]
        segs.append(("L", (0, zt), (-Pi + fl, zt - sh)))
        segs.append(("L", (-Pi + fl, zt - sh), (-Pi, zb + r)))
        segs.append(("A", (-Pi, zb + r), (-Pi + c45, zb + c45), (-Pi + r, zb)))
        segs.append(("L", (-Pi + r, zb), (0, zb) if i < d["n_ribs"] - 1 else (D, 0)))
    segs.append(("L", (D, 0), (D, H)))
    return segs


def draw_section(sk, d, x0):
    to_sk = lambda y, z: sk.modelToSketchSpace(P3(x0, y, z))
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    for s in section_segments(d):
        if s[0] == "L":
            lines.addByTwoPoints(to_sk(*s[1]), to_sk(*s[2]))
        else:
            arcs.addByThreePoints(to_sk(*s[1]), to_sk(*s[2]), to_sk(*s[3]))


def largest_profile(sk):
    best = None
    for pr in sk.profiles:
        a = pr.areaProperties().area
        if best is None or a > best[0]:
            best = (a, pr)
    return best[1]


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        feats = root.features
        d = derived(P)
        H, D, t = d["H"], d["D_back"], d["t"]
        NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
        INTERSECT = adsk.fusion.FeatureOperations.IntersectFeatureOperation
        val = adsk.core.ValueInput.createByReal

        for k, v in P.items():
            unit = "" if k == "n_ribs" else ("deg" if k == "A_wrap" else "mm")
            if root.parentDesign.userParameters.itemByName(k) is None:
                design.userParameters.add(k, adsk.core.ValueInput.createByString(f"{v} {unit}".strip()), unit, "W115 lens")

        # 1) Section on a plane at the wrap start (X = xs), with the wrap axis as a construction line.
        pi = root.constructionPlanes.createInput()
        pi.setByOffset(root.yZConstructionPlane, val(d["xs"] * CM))
        plane_xs = root.constructionPlanes.add(pi)
        sk = root.sketches.add(plane_xs)
        sk.name = "rib section"
        draw_section(sk, d, d["xs"])
        axis = sk.sketchCurves.sketchLines.addByTwoPoints(
            sk.modelToSketchSpace(P3(d["xs"], d["Rg"], 0)), sk.modelToSketchSpace(P3(d["xs"], d["Rg"], H)))
        axis.isConstruction = True
        prof = largest_profile(sk)

        # 2) Straight run back to X = 0, then the amber wrap revolve.
        ext = feats.extrudeFeatures.addSimple(prof, val(-d["xs"] * CM), NEW)
        body = ext.bodies.item(0)
        if body.boundingBox.minPoint.x > 1e-3:          # plane normal pointed the other way
            ext.deleteMe()
            ext = feats.extrudeFeatures.addSimple(prof, val(d["xs"] * CM), NEW)
            body = ext.bodies.item(0)
        body.name = "lens RH"
        ri = feats.revolveFeatures.createInput(prof, axis, JOIN)
        ri.setAngleExtent(False, val(d["A"]))
        ri.participantBodies = [body]
        rev = feats.revolveFeatures.add(ri)
        if body.boundingBox.maxPoint.x < (d["xs"] + 1) * CM:  # revolved backwards: flip
            rev.deleteMe()
            ri = feats.revolveFeatures.createInput(prof, axis, JOIN)
            ri.setAngleExtent(False, val(-d["A"]))
            ri.participantBodies = [body]
            feats.revolveFeatures.add(ri)

        # 3) Plan-view rounding of the inboard end (XY sketch, intersect along Z).
        sk2 = root.sketches.add(root.xYConstructionPlane)
        sk2.name = "plan trim"
        R, y0, ybig, xbig = d["R_end"], -d["P_max"], D + 200, d["L_proj"] + 200
        L2, A2 = sk2.sketchCurves.sketchLines, sk2.sketchCurves.sketchArcs
        q = lambda x, y: sk2.modelToSketchSpace(P3(x, y, 0))
        L2.addByTwoPoints(q(R, y0 - 0.0), q(xbig, y0))
        L2.addByTwoPoints(q(xbig, y0), q(xbig, ybig))
        L2.addByTwoPoints(q(xbig, ybig), q(0, ybig))
        L2.addByTwoPoints(q(0, ybig), q(0, y0 + R))
        A2.addByThreePoints(q(0, y0 + R), q(R - R * math.cos(math.pi / 4), y0 + R - R * math.sin(math.pi / 4)), q(R, y0))
        ei = feats.extrudeFeatures.createInput(largest_profile(sk2), INTERSECT)
        ei.setSymmetricExtent(val((H + 50) * CM), True)
        ei.participantBodies = [body]
        feats.extrudeFeatures.add(ei)

        # 4) Front-view outline with corner radii (XZ sketch, intersect along Y).
        sk3 = root.sketches.add(root.xZConstructionPlane)
        sk3.name = "front outline"
        L, rr = d["L_proj"], d
        q3 = lambda x, z: sk3.modelToSketchSpace(P3(x, 0, z))
        L3, A3 = sk3.sketchCurves.sketchLines, sk3.sketchCurves.sketchArcs
        corners = [((0, 0), rr["r_in_bot"], (1, 1)), ((L, 0), rr["r_out_bot"], (-1, 1)),
                   ((L, H), rr["r_out_top"], (-1, -1)), ((0, H), rr["r_in_top"], (1, -1))]
        pts = []
        for (cx, cz), r, (sx, sz) in corners:
            cc = (cx + sx * r, cz + sz * r)
            a = (cc[0] - sx * r * math.cos(math.pi / 4), cc[1] - sz * r * math.sin(math.pi / 4))
            # arc from the vertical edge point to the horizontal edge point (or reverse), via 45 deg
            p_vert, p_hor = (cx, cc[1]), (cc[0], cz)
            A3.addByThreePoints(q3(*p_vert), q3(*a), q3(*p_hor))
            pts.append((p_vert, p_hor))
        L3.addByTwoPoints(q3(*pts[0][1]), q3(*pts[1][1]))   # bottom
        L3.addByTwoPoints(q3(*pts[1][0]), q3(*pts[2][0]))   # outboard end
        L3.addByTwoPoints(q3(*pts[2][1]), q3(*pts[3][1]))   # top
        L3.addByTwoPoints(q3(*pts[3][0]), q3(*pts[0][0]))   # inboard end
        ei = feats.extrudeFeatures.createInput(largest_profile(sk3), INTERSECT)
        ei.setSymmetricExtent(val(400 * CM), True)
        ei.participantBodies = [body]
        feats.extrudeFeatures.add(ei)

        # 5) Shell 3 mm inward, open at the back (planar back face + the wrap's back cylinder).
        tbm = adsk.fusion.TemporaryBRepManager.get()
        solid_copy = tbm.copy(body)
        back = adsk.core.ObjectCollection.create()
        for f in body.faces:
            pt = f.pointOnFace
            on_plane = abs(pt.y - D * CM) < 1e-4
            rad = math.hypot(pt.x - d["xs"] * CM, pt.y - d["Rg"] * CM)
            on_cyl = pt.x > d["xs"] * CM and abs(rad - (d["Rg"] - D) * CM) < 1e-4
            if on_plane or on_cyl:
                back.add(f)
        si = feats.shellFeatures.createInput(back, False)
        si.insideThickness = val(t * CM)
        feats.shellFeatures.add(si)

        # 6) Interior (partitions, stop-lamp box, insert bosses) as a base feature, clipped to the cavity.
        cavity = tbm.copy(solid_copy)
        tbm.booleanOperation(cavity, tbm.copy(body), adsk.fusion.BooleanTypes.DifferenceBooleanType)
        shell = tbm.copy(body)

        def tbox(x0, x1, y0, y1, z0, z1):
            obb = adsk.core.OrientedBoundingBox3D.create(
                P3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0),
                (x1 - x0) * CM, (y1 - y0) * CM, (z1 - z0) * CM)
            return tbm.createBox(obb)

        U, I, S = (adsk.fusion.BooleanTypes.UnionBooleanType, adsk.fusion.BooleanTypes.IntersectionBooleanType,
                   adsk.fusion.BooleanTypes.DifferenceBooleanType)
        wt, ct, bt, x1, xs = d["wall_t"], d["clear_top"], d["box_top"], d["red_w"], d["xs"]
        yl, yc = D - d["wall_backoff"], d["box_cap_y"]
        for b in (tbox(x1 - wt / 2, x1 + wt / 2, -50, yl, -1, H + 1), tbox(xs - wt, xs, -50, yl, -1, H + 1),
                  tbox(x1, xs, -50, yc, ct, ct + wt), tbox(x1, xs, -50, yc, bt - wt, bt),
                  tbox(x1, xs, yc - wt, yc, ct, bt)):
            tbm.booleanOperation(b, tbm.copy(cavity), I)
            tbm.booleanOperation(shell, b, U)
        sz, yb = H - d["stud_from_top"], D - d["boss_back"]
        for sx in (d["stud_x1"], d["stud_x1"] + d["stud_dx"]):
            boss = tbm.createCylinderOrCone(P3(sx, -60, sz), d["boss_d"] / 2 * CM, P3(sx, yb, sz), d["boss_d"] / 2 * CM)
            tbm.booleanOperation(boss, tbm.copy(solid_copy), I)
            tbm.booleanOperation(shell, boss, U)
            hole = tbm.createCylinderOrCone(P3(sx, yb - d["insert_depth"], sz), d["insert_d"] / 2 * CM,
                                            P3(sx, yb + 1, sz), d["insert_d"] / 2 * CM)
            tbm.booleanOperation(shell, hole, S)

        # 7) Split into colour bodies (zero gap): red = inboard + middle-top, clear = middle-bottom, amber = wrap.
        big = 2000

        def piece(x0, x1, z0, z1):
            b = tbm.copy(shell)
            tbm.booleanOperation(b, tbox(x0, x1, -big, big, z0, z1), I)
            return b

        red = piece(-big, x1, -big, big)
        tbm.booleanOperation(red, piece(x1, xs, ct, big), U)
        parts = {"RH red": red, "RH clear": piece(x1, xs, -big, ct), "RH amber": piece(xs, big, -big, big)}

        base = feats.baseFeatures.add()
        base.startEdit()
        out_bodies = adsk.core.ObjectCollection.create()
        for name, b in parts.items():
            nb = root.bRepBodies.add(b, base)
            nb.name = name
            out_bodies.add(nb)
        base.finishEdit()
        body.isLightBulbOn = False       # the shelled envelope stays in the timeline, hidden

        # 8) LH = mirror of RH about the YZ plane.
        mi = feats.mirrorFeatures.createInput(out_bodies, root.yZConstructionPlane)
        feats.mirrorFeatures.add(mi)

        ui.messageBox("W115 lens built: RH red/clear/amber + mirrored LH.\n"
                      "Export each body as STL (or the design as 3MF) for Bambu Studio.")
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
