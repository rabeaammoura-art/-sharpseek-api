"""Fusion 360 script: collapsible 3-compartment "Mercedes" serving tray.

Builds the same geometry as cad/parts/_mercedes.py as parametric history features
(sketch -> extrude / loft -> combine) in two components: "Tray" (frame + 3 x N rings,
collapsed, print-in-place) and "Handle" (folded down, separate print).

Parameters: the key dimensions are created as User Parameters (mm).
  * Heights (ring_h, frame_h, lip_flat, lip, floor_t, handle_t, hinge_gap) drive the
    construction planes and extrude distances directly, so editing them in
    Modify > Change Parameters updates the model live.
  * Plan dimensions (tray_d, flange_w, divider_half, wall, clear, lip) and the
    derived step count N are applied when the script runs: edit the parameters,
    then run the script again in a new design and it rebuilds using the values you set.
    (If the active design already has these parameters, the script reads them.)

Run: Utilities > Add-Ins > Scripts and Add-Ins > + (My Scripts) > select this folder > Run.
"""
import math
import traceback

import adsk.core
import adsk.fusion

# name: (default mm, comment) — identical to cad/parts/_mercedes.py Params
PARAMS = {
    "tray_d": (280.0, "outer diameter of the flange"),
    "flange_w": (20.0, "flat outer rim width"),
    "divider_half": (2.0, "half width of a Mercedes divider rib"),
    "wall": (1.2, "ring wall thickness"),
    "clear": (0.4, "print-in-place gap between rings"),
    "lip": (1.6, "stop-lip protrusion (45 deg chamfer)"),
    "lip_flat": (0.6, "vertical land of each lip"),
    "ring_h": (7.0, "telescoping ring height"),
    "frame_h": (9.0, "flange + divider height"),
    "floor_t": (1.2, "compartment floor thickness"),
    "floor_inradius_min": (12.0, "smallest allowed floor inscribed radius"),
    "handle_r": (134.0, "handle centreline radius"),
    "handle_w": (10.0, "handle band radial width"),
    "handle_t": (6.0, "handle band thickness = pin diameter"),
    "pin_len": (5.5, "hinge pin length"),
    "pin_clear": (0.3, "pin to hole radial clearance"),
    "hinge_gap": (0.8, "gap handle to post and to flange"),
    "post_t": (6.0, "hinge post thickness along the axis"),
    "post_w": (12.0, "hinge post width"),
}
COMPARTMENT_ANGLES = (30.0, 150.0, 270.0)


def cm(mm):
    return mm / 10.0


class Geo:
    """Derived dimensions — same formulas as Params in _mercedes.py."""

    def __init__(self, v):
        self.__dict__.update(v)
        self.r_sector = self.tray_d / 2 - self.flange_w
        self.pitch = self.wall + self.lip + self.clear
        s = math.sin(math.radians(60))
        self.sector_inradius = self.r_sector * s / (1 + s)
        room = self.sector_inradius - self.floor_inradius_min - (self.divider_half + self.lip + self.clear + self.wall)
        self.n_rings = int(math.floor(room / self.pitch)) + 1
        self.hinge_z = self.frame_h + self.hinge_gap + self.handle_t / 2
        self.pin_r = self.handle_t / 2
        self.hole_r = self.pin_r + self.pin_clear
        post_outer = self.handle_r - self.handle_w / 2 - self.hinge_gap
        self.post_x = (post_outer - self.post_t, post_outer)
        self.post_top = self.hinge_z + self.hole_r * math.sqrt(2) + 1.5

    def ring_inset(self, k):
        return self.divider_half + self.lip + self.clear + (k - 1) * self.pitch

    def sector_points(self, d, theta_c):
        R = self.r_sector

        def u(a):
            return math.cos(math.radians(a)), math.sin(math.radians(a))

        apex_r = d / math.cos(math.radians(30))
        s = math.sqrt((R - d) ** 2 - d ** 2)
        e1, n1 = u(theta_c - 60), u(theta_c + 30)
        e2, n2 = u(theta_c + 60), u(theta_c - 30)
        apex = (apex_r * u(theta_c)[0], apex_r * u(theta_c)[1])
        a1 = (s * e1[0] + d * n1[0], s * e1[1] + d * n1[1])
        a2 = (s * e2[0] + d * n2[0], s * e2[1] + d * n2[1])
        mid = ((R - d) * u(theta_c)[0], (R - d) * u(theta_c)[1])
        return apex, a1, mid, a2


class Builder:
    def __init__(self, design, comp):
        self.design, self.comp = design, comp
        self.f = comp.features
        self.planes = {}

    # ---- planes & sketches ------------------------------------------------
    def zplane(self, expr):
        """Construction plane parallel to XY at height `expr` (parameter expression or None)."""
        if expr is None:
            return self.comp.xYConstructionPlane
        if expr not in self.planes:
            pi = self.comp.constructionPlanes.createInput()
            pi.setByOffset(self.comp.xYConstructionPlane, adsk.core.ValueInput.createByString(expr))
            self.planes[expr] = self.comp.constructionPlanes.add(pi)
        return self.planes[expr]

    def xplane(self, x_mm):
        pi = self.comp.constructionPlanes.createInput()
        pi.setByOffset(self.comp.yZConstructionPlane, adsk.core.ValueInput.createByReal(cm(x_mm)))
        return self.comp.constructionPlanes.add(pi)

    @staticmethod
    def pt(sk, x, y, z):
        return sk.modelToSketchSpace(adsk.core.Point3D.create(cm(x), cm(y), cm(z)))

    def sector_profile(self, g, d, th, z_expr, z_mm):
        sk = self.comp.sketches.add(self.zplane(z_expr))
        apex, a1, mid, a2 = [self.pt(sk, x, y, z_mm) for x, y in g.sector_points(d, th)]
        lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
        lines.addByTwoPoints(apex, a1)
        arcs.addByThreePoints(a1, mid, a2)
        lines.addByTwoPoints(a2, apex)
        return sk.profiles.item(0)

    # ---- features -----------------------------------------------------------
    def extrude(self, prof, dist_expr):
        e = self.f.extrudeFeatures.addSimple(prof, adsk.core.ValueInput.createByString(dist_expr),
                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        return e.bodies.item(0)

    def extrude_sym(self, prof, length_mm):
        ei = self.f.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ei.setSymmetricExtent(adsk.core.ValueInput.createByReal(cm(length_mm)), True)
        return self.f.extrudeFeatures.add(ei).bodies.item(0)

    def loft(self, p0, p1):
        li = self.f.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        li.loftSections.add(p0)
        li.loftSections.add(p1)
        li.isSolid = True
        return self.f.loftFeatures.add(li).bodies.item(0)

    def combine(self, target, tools, cut):
        coll = adsk.core.ObjectCollection.create()
        for t in tools:
            coll.add(t)
        ci = self.f.combineFeatures.createInput(target, coll)
        ci.operation = (adsk.fusion.FeatureOperations.CutFeatureOperation if cut
                        else adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ci.isKeepToolBodies = False
        self.f.combineFeatures.add(ci)
        return target

    # ---- primitives (mirror _mercedes.py) ------------------------------------
    def prism(self, g, d, th, z0, dist):
        """z0 / dist are (expression, mm value) pairs."""
        return self.extrude(self.sector_profile(g, d, th, z0[0], z0[1]), dist)

    def frustum(self, g, d0, z0, d1, z1, th):
        return self.loft(self.sector_profile(g, d0, th, z0[0], z0[1]), self.sector_profile(g, d1, th, z1[0], z1[1]))

    def lipped_cavity(self, g, d_open, th, height_expr):
        lo, hi = ("lip_flat", g.lip_flat), ("lip_flat + lip", g.lip_flat + g.lip)
        return [self.prism(g, d_open + g.lip, th, (None, 0.0), height_expr),
                self.frustum(g, d_open + g.lip, lo, d_open, hi, th),
                self.prism(g, d_open, th, hi, f"({height_expr}) - lip_flat - lip")]

    def ring(self, g, k, th):
        a = g.ring_inset(k)
        z_chamfer = ("ring_h - lip_flat - lip", g.ring_h - g.lip_flat - g.lip)
        z_land = ("ring_h - lip_flat", g.ring_h - g.lip_flat)
        body = self.prism(g, a, th, (None, 0.0), "ring_h")
        self.combine(body, [self.frustum(g, a, z_chamfer, a - g.lip, z_land, th),
                            self.prism(g, a - g.lip, th, z_land, "lip_flat")], cut=False)
        if k < g.n_rings:
            cavity = self.lipped_cavity(g, a + g.wall, th, "ring_h")
        else:
            cavity = [self.prism(g, a + g.wall, th, ("floor_t", g.floor_t), "ring_h - floor_t")]
        self.combine(body, cavity, cut=True)
        body.name = f"c{int(th)}_r{k:02d}"
        return body

    def teardrop_x(self, g, x0, x1):
        sk = self.comp.sketches.add(self.xplane((x0 + x1) / 2))
        x, r, z = (x0 + x1) / 2, g.hole_r, g.hinge_z
        q = r / math.sqrt(2)
        p_left, p_right, apex = self.pt(sk, x, -q, z + q), self.pt(sk, x, q, z + q), self.pt(sk, x, 0, z + r * math.sqrt(2))
        sk.sketchCurves.sketchArcs.addByThreePoints(p_right, self.pt(sk, x, 0, z - r), p_left)
        sk.sketchCurves.sketchLines.addByTwoPoints(p_left, apex)
        sk.sketchCurves.sketchLines.addByTwoPoints(apex, p_right)
        return self.extrude_sym(sk.profiles.item(0), x1 - x0)

    def cylinder_x(self, g, x0, x1, r, z):
        sk = self.comp.sketches.add(self.xplane((x0 + x1) / 2))
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.pt(sk, (x0 + x1) / 2, 0, z), cm(r))
        return self.extrude_sym(sk.profiles.item(0), x1 - x0)

    def frame(self, g):
        sk = self.comp.sketches.add(self.comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.pt(sk, 0, 0, 0), cm(g.tray_d / 2))
        body = self.extrude(sk.profiles.item(0), "frame_h")
        xi, xo = g.post_x
        posts = []
        for side in (1, -1):
            skp = self.comp.sketches.add(self.zplane("frame_h"))
            skp.sketchCurves.sketchLines.addTwoPointRectangle(self.pt(skp, side * xi, -g.post_w / 2, g.frame_h),
                                                              self.pt(skp, side * xo, g.post_w / 2, g.frame_h))
            posts.append(self.extrude(skp.profiles.item(0), f"{g.post_top - g.frame_h:.6f} mm"))
        self.combine(body, posts, cut=False)
        tools = []
        for th in COMPARTMENT_ANGLES:
            tools += self.lipped_cavity(g, g.divider_half, th, "frame_h")
        for side in (1, -1):
            x0, x1 = sorted((side * (xi - 1), side * (xo + 1)))
            tools.append(self.teardrop_x(g, x0, x1))
        self.combine(body, tools, cut=True)
        body.name = "frame"
        return body

    def handle(self, g):
        r0, r1 = g.handle_r - g.handle_w / 2, g.handle_r + g.handle_w / 2
        z = g.frame_h + g.hinge_gap
        sk = self.comp.sketches.add(self.zplane("frame_h + hinge_gap"))
        p = lambda x, y: self.pt(sk, x, y, z)  # noqa: E731
        arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
        arcs.addByThreePoints(p(r1, 0), p(0, r1), p(-r1, 0))
        lines.addByTwoPoints(p(-r1, 0), p(-r0, 0))
        arcs.addByThreePoints(p(-r0, 0), p(0, r0), p(r0, 0))
        lines.addByTwoPoints(p(r0, 0), p(r1, 0))
        body = self.extrude(sk.profiles.item(0), "handle_t")
        xi, _ = g.post_x
        tools = []
        for side in (1, -1):
            tools.append(self.cylinder_x(g, side * r0, side * r1, g.handle_t / 2, g.hinge_z))
            lo, hi = sorted((side * (xi + 1.0), side * r0))
            tools.append(self.cylinder_x(g, lo, hi, g.pin_r, g.hinge_z))
        self.combine(body, tools, cut=False)
        body.name = "handle"
        return body


def read_params(design):
    up = design.userParameters
    values = {}
    for name, (default, comment) in PARAMS.items():
        p = up.itemByName(name)
        if p is None:
            p = up.add(name, adsk.core.ValueInput.createByString(f"{default} mm"), "mm", comment)
        values[name] = p.value * 10.0  # internal cm -> mm
    return values


def build(design):
    g = Geo(read_params(design))
    root = design.rootComponent
    tray = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    tray.name = "Tray"
    tb = Builder(design, tray)
    tb.frame(g)
    for th in COMPARTMENT_ANGLES:
        for k in range(1, g.n_rings + 1):
            tb.ring(g, k, th)
            adsk.doEvents()
    hcomp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    hcomp.name = "Handle"
    Builder(design, hcomp).handle(g)
    return g


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a Fusion design first.")
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        g = build(design)
        ui.messageBox(f"Mercedes tray built: {g.n_rings} rings x 3 compartments, "
                      f"depth {g.n_rings * (g.ring_h - 2 * g.lip_flat - g.lip + g.clear):.1f} mm.")
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
