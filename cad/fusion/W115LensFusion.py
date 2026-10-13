"""Fusion 360 script: Mercedes W114/W115 late-series rear lamp lens (Euro), RH + mirrored LH.

Scripts and Add-Ins -> Scripts -> "+" -> pick this folder -> Run, in a NEW empty design.
Edit P below and re-run to change the size; the values are also written to
Modify -> Change Parameters (as user parameters) for reference.

Geometry follows cad/parts/w115_lens.py (the reference model, exported as STEP):
a core body behind the rib valley line (plan sketch, extruded), the rib relief swept
along the valley line round both ends and the amber wrap, the front-view outline, a
shell open at the back, a back flange plate at the inboard end, interior walls /
stop-lamp box / insert bosses, then red, clear, amber bodies with zero gap for a
one-shot multi-material print.
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
    crest_frac=0.4, rib_P0=11.0, rib_step=0.0,
    D_back=28.0, t=3.0,
    red_w=100.0, mid_w=120.0, A_wrap=50.0, R_end=25.0, R_end_out=20.0,
    r_in_top=12.0, r_in_bot=5.0,
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
    d["Rv"] = p["R_end"] - d["P_max"]
    d["Rvo"] = p["R_end_out"] - d["P_max"]
    d["Rg"] = (p["L_proj"] - d["xs"] - d["Rvo"] - d["P_max"]) / math.sin(d["A"]) + d["Rvo"]
    d["crest_h"] = p["crest_frac"] * d["pitch"]
    d["clear_top"] = 2 * d["pitch"] - d["crest_h"]
    d["box_top"] = p["H"] - p["lip_h"] - 2.0
    return d


def P3(x, y, z):
    return adsk.core.Point3D.create(x * CM, y * CM, z * CM)


def plan_loop(d, off, y_back):
    """Valley line in plan (offset `off` inward) as ('L', p, q) / ('A', p, mid, q) in mm (x, y),
    plus the closing back arc and line. Returns (path_segments, closing_segments)."""
    P, Rv, Rvo, xs, Rg, A = d["P_max"], d["Rv"], d["Rvo"], d["xs"], d["Rg"], d["A"]
    arc = lambda c, r, a0, a1: ("A", (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0)),
                                (c[0] + r * math.cos((a0 + a1) / 2), c[1] + r * math.sin((a0 + a1) / 2)),
                                (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1)))
    path = [("L", (P + off, y_back), (P + off, Rv)),
            arc((P + Rv, Rv), Rv - off, math.pi, 1.5 * math.pi),
            ("L", (P + Rv, off), (xs, off)),
            arc((xs, Rg), Rg - off, 1.5 * math.pi, 1.5 * math.pi + A)]
    co = (xs + (Rg - Rvo) * math.sin(A), Rg - (Rg - Rvo) * math.cos(A))
    path.append(arc(co, Rvo - off, A - math.pi / 2, A))
    start = (co[0] + (Rvo - off) * math.cos(A), co[1] + (Rvo - off) * math.sin(A))
    inward = (-math.sin(A), math.cos(A))
    f = (start[0] - xs, start[1] - Rg)
    rb = Rg - y_back
    bq = 2 * (f[0] * inward[0] + f[1] * inward[1])
    cq = f[0] ** 2 + f[1] ** 2 - rb * rb
    sq = (-bq - math.sqrt(bq * bq - 4 * cq)) / 2
    if sq < 0:
        sq = (-bq + math.sqrt(bq * bq - 4 * cq)) / 2
    end = (start[0] + inward[0] * sq, start[1] + inward[1] * sq)
    path.append(("L", start, end))
    a_end = math.atan2(end[1] - Rg, end[0] - xs)
    closing = [arc((xs, Rg), rb, a_end, 1.5 * math.pi) if a_end > 1.5 * math.pi
               else arc((xs, Rg), rb, a_end + 2 * math.pi, 1.5 * math.pi),
               ("L", (xs, y_back), (P + off, y_back))]
    return path, closing


def relief_segments(d):
    """Rib relief section in (n = outward from the valley line, z), closed 2 mm into the core."""
    H, hc, s45 = d["H"], d["crest_h"], math.sin(math.pi / 4)
    segs = []
    for i in range(d["n_ribs"]):
        zt = H - d["lip_h"] - i * d["pitch"]
        zb = zt - d["pitch"]
        Pi = d["rib_P0"] + i * d["rib_step"]
        segs.append(("A", (0, zt), (Pi * s45, zt - hc + hc * s45), (Pi, zt - hc)))   # crest
        segs.append(("L", (Pi, zt - hc), (0, zb)))                                   # face -> valley
    top = H - d["lip_h"]
    segs += [("L", (0, 0), (-2, 0)), ("L", (-2, 0), (-2, top)), ("L", (-2, top), (0, top))]
    return segs


def draw(sk, segs, to_model):
    """Draw segments; to_model maps a 2D point to model (x, y, z) in mm."""
    q = lambda pt: sk.modelToSketchSpace(P3(*to_model(pt)))
    curves = []
    for sg in segs:
        if sg[0] == "L":
            curves.append(sk.sketchCurves.sketchLines.addByTwoPoints(q(sg[1]), q(sg[2])))
        else:
            curves.append(sk.sketchCurves.sketchArcs.addByThreePoints(q(sg[1]), q(sg[2]), q(sg[3])))
    return curves


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

        # 1) Core behind the valley line: plan loop on XY, extruded over the full height.
        path_segs, closing = plan_loop(d, 0.0, D)
        sk_core = root.sketches.add(root.xYConstructionPlane)
        sk_core.name = "core plan"
        draw(sk_core, path_segs + closing, lambda pt: (pt[0], pt[1], 0))
        body = feats.extrudeFeatures.addSimple(largest_profile(sk_core), val(H * CM), NEW).bodies.item(0)
        body.name = "lens RH"

        # 2) Rib relief swept along the valley line (inboard end wall -> corner -> lens -> wrap ->
        #    outboard corner -> end wall). Profile sits in the back plane (Y = D) at the path start.
        sk_path = root.sketches.add(root.xYConstructionPlane)
        sk_path.name = "valley path"
        path_curves = draw(sk_path, path_segs, lambda pt: (pt[0], pt[1], 0))
        pi = root.constructionPlanes.createInput()
        pi.setByOffset(root.xZConstructionPlane, val(D * CM))
        plane_back = root.constructionPlanes.add(pi)
        if abs(plane_back.geometry.origin.y - D * CM) > 1e-6:      # XZ plane normal is -Y: flip the offset
            plane_back.deleteMe()
            pi = root.constructionPlanes.createInput()
            pi.setByOffset(root.xZConstructionPlane, val(-D * CM))
            plane_back = root.constructionPlanes.add(pi)
        sk_rel = root.sketches.add(plane_back)
        sk_rel.name = "rib relief section"
        draw(sk_rel, relief_segments(d), lambda pt: (d["P_max"] - pt[0], D, pt[1]))
        path = feats.createPath(path_curves[0], True)
        swi = feats.sweepFeatures.createInput(largest_profile(sk_rel), path, JOIN)
        swi.participantBodies = [body]
        feats.sweepFeatures.add(swi)

        # 4) Front-view outline with corner radii (XZ sketch, intersect along Y).
        sk3 = root.sketches.add(root.xZConstructionPlane)
        sk3.name = "front outline"
        L, rr = d["L_proj"] + 50, d          # open past the outboard end (its return shapes it)
        q3 = lambda x, z: sk3.modelToSketchSpace(P3(x, 0, z))
        L3, A3 = sk3.sketchCurves.sketchLines, sk3.sketchCurves.sketchArcs
        rt, rb_ = rr["r_in_top"], rr["r_in_bot"]
        c45 = math.cos(math.pi / 4)
        A3.addByThreePoints(q3(0, rb_), q3(rb_ - rb_ * c45, rb_ - rb_ * c45), q3(rb_, 0))          # inboard bottom
        A3.addByThreePoints(q3(0, H - rt), q3(rt - rt * c45, H - rt + rt * c45), q3(rt, H))       # inboard top
        L3.addByTwoPoints(q3(rb_, 0), q3(L, 0))
        L3.addByTwoPoints(q3(L, 0), q3(L, H))
        L3.addByTwoPoints(q3(L, H), q3(rt, H))
        L3.addByTwoPoints(q3(0, H - rt), q3(0, rb_))
        ei = feats.extrudeFeatures.createInput(largest_profile(sk3), NEW)
        ei.setSymmetricExtent(val(400 * CM), True)
        outline = feats.extrudeFeatures.add(ei).bodies.item(0)
        tbm = adsk.fusion.TemporaryBRepManager.get()
        outline_copy = tbm.copy(outline)
        tools = adsk.core.ObjectCollection.create()
        tools.add(outline)
        ci = feats.combineFeatures.createInput(body, tools)
        ci.operation = INTERSECT
        feats.combineFeatures.add(ci)

        # 5) Shell 3 mm inward, open at the back (planar back face + the wrap's back cylinder).
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
        # Back flange plate at the inboard end, out to the rib crests (straight edge seen from behind).
        plate = tbox(0, d["P_max"] + t, D - t, D, 0, H)
        tbm.booleanOperation(plate, tbm.copy(outline_copy), I)
        tbm.booleanOperation(shell, plate, U)
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
