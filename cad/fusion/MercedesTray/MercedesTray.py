"""Fusion 360 script: collapsible 3-compartment "Mercedes" serving tray.

Builds the same geometry as cad/parts/_mercedes.py as parametric history features
(sketch -> extrude / loft -> combine) in two components: "Tray" (frame + 3 x N rings +
handle ring with hinge pins, collapsed, one print-in-place job) and "Base" (separate print,
twist-locked to the floors). Decoration (carved swirls, border lines, edge teeth) is read from
decor.json next to this script, written by cad/parts/_decor.py.

Parameters: the key dimensions are created as User Parameters (mm).
  * Heights (ring_h, frame_h, lip_flat, lip, floor_t, base_t, pocket_d) drive the
    construction planes and extrude distances directly, so editing them in
    Modify > Change Parameters updates the model live.
  * Plan dimensions (tray_d, flange_w, divider_half, wall, clear, lip, handle and pocket\n    values) and the
    derived step count N are applied when the script runs: edit the parameters,
    then run the script again in a new design and it rebuilds using the values you set.
    (If the active design already has these parameters, the script reads them.)

Run: Utilities > Add-Ins > Scripts and Add-Ins > + (My Scripts) > select this folder > Run.
"""
import json
import math
import os
import traceback

import adsk.core
import adsk.fusion

# name: (default, unit, comment) — identical to cad/parts/_mercedes.py Params
PARAMS = {
    "tray_d": (264.0, "mm", "diameter of the frame flange"),
    "flange_w": (12.0, "mm", "flat rim between compartments and handle ring"),
    "divider_half": (2.0, "mm", "half width of a Mercedes divider rib"),
    "wall": (1.2, "mm", "ring wall thickness"),
    "clear": (0.4, "mm", "print-in-place gap between rings"),
    "lip": (1.6, "mm", "stop-lip protrusion (45 deg chamfer)"),
    "lip_flat": (0.6, "mm", "vertical land of each lip"),
    "ring_h": (7.0, "mm", "telescoping ring height"),
    "frame_h": (10.0, "mm", "flange, divider and handle ring height"),
    "floor_t": (1.2, "mm", "compartment floor thickness"),
    "floor_inradius_min": (12.0, "mm", "smallest allowed floor inscribed radius"),
    "handle_gap": (0.5, "mm", "print-in-place gap handle ring to flange"),
    "handle_w": (10.0, "mm", "radial width of the handle ring"),
    "leg_deg": (28.93, "", "leg length past the hinge, degrees"),
    "leg_gap_deg": (1.5, "", "gap leg end to fixed outer ring, degrees"),
    "pin_r": (2.0, "mm", "hinge pin radius"),
    "pin_clear": (0.4, "mm", "pin to hole radial clearance"),
    "pin_len": (5.0, "mm", "pin length into the flange"),
    "stop_deg": (100.0, "", "handle angle at the pocket stop, degrees"),
    "base_d": (290.0, "mm", "base plate diameter"),
    "base_t": (6.0, "mm", "base plate thickness"),
    "pocket_d": (4.0, "mm", "foot pocket depth"),
    "pocket_x0": (117.15, "mm", "foot pocket floor, inner x"),
    "pocket_x1": (127.18, "mm", "foot pocket floor, outer x"),
    "pocket_y0": (-17.19, "mm", "foot pocket floor start (45 deg entry ramp before it)"),
    "pocket_y1": (17.19, "mm", "foot pocket stop wall (vertical)"),
    "twist_lock": (1, "", "1 = base posts + floor keyholes"),
    "lock_deg": (7.0, "", "twist to unlock, degrees"),
    "post_neck_r": (2.2, "mm", "twist-lock post neck radius"),
    "post_head_r": (4.0, "mm", "twist-lock post head radius"),
    "post_head_t": (1.0, "mm", "twist-lock head cylinder height"),
    "lock_clear": (0.4, "mm", "twist-lock clearance"),
    "lock_play": (1.0, "mm", "twist-lock head height above the floor (vertical play)"),
    "decor": (1, "", "1 = carved swirls, border lines and edge teeth from decor.json"),
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
        self.r_flange = self.tray_d / 2
        self.handle_r0 = self.r_flange + self.handle_gap
        self.handle_r1 = self.handle_r0 + self.handle_w
        self.hinge_z = self.frame_h / 2
        self.hole_r = self.pin_r + self.pin_clear
        self.lock_c = self.sector_inradius / math.sin(math.radians(60))

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

    def combine(self, target, tools, cut, keep_tools=False):
        coll = adsk.core.ObjectCollection.create()
        for t in tools:
            coll.add(t)
        ci = self.f.combineFeatures.createInput(target, coll)
        ci.operation = (adsk.fusion.FeatureOperations.CutFeatureOperation if cut
                        else adsk.fusion.FeatureOperations.JoinFeatureOperation)
        ci.isKeepToolBodies = keep_tools
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
            if g.twist_lock:
                cavity += self.keyhole(g, th)
        self.combine(body, cavity, cut=True)
        body.name = f"c{int(th)}_r{k:02d}"
        return body

    def annulus_sector(self, r0, r1, a0, a1, height_expr, z0=(None, 0.0)):
        sk = self.comp.sketches.add(self.zplane(z0[0]))

        def pol(r, a):
            return self.pt(sk, r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), z0[1])

        am = (a0 + a1) / 2
        arcs, lines = sk.sketchCurves.sketchArcs, sk.sketchCurves.sketchLines
        arcs.addByThreePoints(pol(r1, a0), pol(r1, am), pol(r1, a1))
        lines.addByTwoPoints(pol(r1, a1), pol(r0, a1))
        arcs.addByThreePoints(pol(r0, a1), pol(r0, am), pol(r0, a0))
        lines.addByTwoPoints(pol(r0, a0), pol(r1, a0))
        return self.extrude(sk.profiles.item(0), height_expr)

    def yz_prism(self, profile, x0, x1):
        """Prism along X (x0..x1) of a closed (y, z) profile of ('line', a, b) / ('arc', a, m, b)."""
        xm = (x0 + x1) / 2
        sk = self.comp.sketches.add(self.xplane(xm))
        for seg in profile:
            pts = [self.pt(sk, xm, y, z) for y, z in seg[1:]]
            if seg[0] == "line":
                sk.sketchCurves.sketchLines.addByTwoPoints(*pts)
            else:
                sk.sketchCurves.sketchArcs.addByThreePoints(*pts)
        return self.extrude_sym(sk.profiles.item(0), x1 - x0)

    @staticmethod
    def pin_profile(g):
        r, z = g.pin_r, g.hinge_z
        return [("arc", (r, z), (0, z + r), (-r, z)), ("line", (-r, z), (0, z - r)), ("line", (0, z - r), (r, z))]

    @staticmethod
    def hole_profile(g):
        r, z = g.hole_r, g.hinge_z
        q = r / math.sqrt(2)
        return [("arc", (q, z + q), (0, z - r), (-q, z + q)), ("line", (-q, z + q), (0, z + r * math.sqrt(2))),
                ("line", (0, z + r * math.sqrt(2)), (q, z + q))]

    def frame(self, g):
        sk = self.comp.sketches.add(self.comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.pt(sk, 0, 0, 0), cm(g.r_flange))
        body = self.extrude(sk.profiles.item(0), "frame_h")
        gap = g.leg_deg + g.leg_gap_deg
        self.combine(body, [self.annulus_sector(g.r_flange - 1.0, g.handle_r1, 180 + gap, 360 - gap, "frame_h")],
                     cut=False)
        tools = []
        for th in COMPARTMENT_ANGLES:
            tools += self.lipped_cavity(g, g.divider_half, th, "frame_h")
        for side in (1, -1):
            x0, x1 = sorted((side * (g.r_flange - g.pin_len - 1.0), side * (g.r_flange + 0.1)))
            tools.append(self.yz_prism(self.hole_profile(g), x0, x1))
        self.combine(body, tools, cut=True)
        if g.decor:
            self.combine(body, self.decor_tools(g.decor_specs, "frame"), cut=True)
        body.name = "frame"
        return body

    def handle(self, g):
        body = self.annulus_sector(g.handle_r0, g.handle_r1, -g.leg_deg, 180 + g.leg_deg, "frame_h")
        pins = []
        for side in (1, -1):
            x0, x1 = sorted((side * (g.r_flange - g.pin_len), side * (g.handle_r0 + 0.5)))
            pins.append(self.yz_prism(self.pin_profile(g), x0, x1))
        self.combine(body, pins, cut=False)
        if g.decor:
            self.combine(body, self.decor_tools(g.decor_specs, "handle"), cut=True)
        body.name = "handle"
        return body

    def rect_profile(self, z_expr, z_mm, x0, y0, x1, y1):
        sk = self.comp.sketches.add(self.zplane(z_expr))
        pts = [self.pt(sk, x, y, z_mm) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        for i in range(4):
            sk.sketchCurves.sketchLines.addByTwoPoints(pts[i], pts[(i + 1) % 4])
        return sk.profiles.item(0)

    def polar(self, r, a):
        return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))

    def circle_profile(self, x, y, r, z_mm):
        sk = self.comp.sketches.add(self.zplane(f"{z_mm} mm" if z_mm else None))
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.pt(sk, x, y, z_mm), cm(r))
        return sk.profiles.item(0)

    def cylinder(self, x, y, r, z0, height):
        return self.extrude(self.circle_profile(x, y, r, z0), f"{height} mm")

    def keyhole(self, g, th):
        """Same as keyhole() in _mercedes.py: round entry + arc slot + round slot ends."""
        c, b, z0, hgt = g.lock_c, g.lock_deg / 2, -1.0, g.floor_t + 2.0
        w = g.post_neck_r + g.lock_clear
        tools = [self.cylinder(*self.polar(c, th - b), g.post_head_r + g.lock_clear, z0, hgt),
                 self.annulus_sector(c - w, c + w, th - b, th + b, f"{hgt} mm", (f"{z0} mm", z0))]
        tools += [self.cylinder(*self.polar(c, a), w, z0, hgt) for a in (th - b, th + b)]
        return tools

    def lock_post(self, g, th):
        x, y = self.polar(g.lock_c, th + g.lock_deg / 2)
        z1 = g.floor_t + g.lock_play
        z2 = z1 + (g.post_head_r - g.post_neck_r)
        return [self.cylinder(x, y, g.post_neck_r, -0.5, z1 + 0.5),
                self.loft(self.circle_profile(x, y, g.post_neck_r, z1), self.circle_profile(x, y, g.post_head_r, z2)),
                self.cylinder(x, y, g.post_head_r, z2, g.post_head_t)]

    # ---- decoration (polygons from decor.json, written by cad/parts/_decor.py) ----------------
    @staticmethod
    def _area(pts):
        return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2

    def decor_tools(self, specs, target):
        """Extrude every decoration polygon for one target; returns the new tool bodies."""
        bodies = []
        for spec in specs:
            if spec["target"] != target:
                continue
            z0 = spec["z0"]
            sk = self.comp.sketches.add(self.zplane(f"{z0} mm"))
            sk.isComputeDeferred = True
            lines = sk.sketchCurves.sketchLines
            for poly in spec["polys"]:
                for loop in [poly["outer"]] + poly["holes"]:
                    pts = [self.pt(sk, x, y, z0) for x, y in loop]
                    first = prev = lines.addByTwoPoints(pts[0], pts[1])
                    for q in pts[2:]:
                        prev = lines.addByTwoPoints(prev.endSketchPoint, q)
                    lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
            sk.isComputeDeferred = False
            # pick the sketch regions that are the polygons (not their holes)
            profs = [sk.profiles.item(i) for i in range(sk.profiles.count)]
            areas = [pr.areaProperties().area * 100.0 for pr in profs]
            chosen, used = adsk.core.ObjectCollection.create(), set()
            for poly in spec["polys"]:
                want = self._area(poly["outer"]) - sum(self._area(h) for h in poly["holes"])
                i = min((i for i in range(len(profs)) if i not in used), key=lambda i: abs(areas[i] - want))
                if abs(areas[i] - want) > 0.01 * want + 0.01:
                    raise RuntimeError(f"decor: no sketch region matches a {target} polygon ({want:.2f} mm2)")
                used.add(i)
                chosen.add(profs[i])
            e = self.f.extrudeFeatures.addSimple(chosen, adsk.core.ValueInput.createByString(f"{spec['z1'] - z0} mm"),
                                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            bodies += [e.bodies.item(i) for i in range(e.bodies.count)]
        return bodies

    def base(self, g):
        """Top face at z = 0; pockets: 45° ramps, vertical stop wall at pocket_y1."""
        sk = self.comp.sketches.add(self.zplane("-base_t"))
        sk.sketchCurves.sketchCircles.addByCenterRadius(self.pt(sk, 0, 0, -g.base_t), cm(g.base_d / 2))
        body = self.extrude(sk.profiles.item(0), "base_t")
        d = g.pocket_d
        tools = []
        for side in (1, -1):
            xa, xb = sorted((side * g.pocket_x0, side * g.pocket_x1))
            bot = self.rect_profile("-pocket_d", -d, xa, g.pocket_y0, xb, g.pocket_y1)
            top = self.rect_profile(None, 0.0, xa - d, g.pocket_y0 - d, xb + d, g.pocket_y1)
            tools.append(self.loft(bot, top))
        self.combine(body, tools, cut=True)
        if g.twist_lock:
            for th in COMPARTMENT_ANGLES:
                self.combine(body, self.lock_post(g, th), cut=False)
        if g.decor:
            self.combine(body, self.decor_tools(g.decor_specs, "base"), cut=True)
        body.name = "base"
        return body


def read_params(design):
    up = design.userParameters
    values = {}
    for name, (default, unit, comment) in PARAMS.items():
        p = up.itemByName(name)
        if p is None:
            p = up.add(name, adsk.core.ValueInput.createByString(f"{default} {unit}".strip()), unit, comment)
        values[name] = p.value * 10.0 if unit == "mm" else p.value  # lengths: internal cm -> mm
    return values


def load_decor():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "decor.json")) as f:
        return json.load(f)


def build(design):
    g = Geo(read_params(design))
    root = design.rootComponent
    tray = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    tray.name = "Tray (one print, in place)"
    tb = Builder(design, tray)
    g.decor_specs = load_decor() if g.decor else []
    tb.frame(g)
    tb.handle(g)
    rings = []
    for th in COMPARTMENT_ANGLES:
        for k in range(1, g.n_rings + 1):
            rings.append(tb.ring(g, k, th))
            adsk.doEvents()
    if g.decor:  # one set of tools, cut from every ring (kept until the last cut)
        tools = tb.decor_tools(g.decor_specs, "rings")
        for i, r in enumerate(rings):
            tb.combine(r, tools, cut=True, keep_tools=i < len(rings) - 1)
            adsk.doEvents()
    bcomp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
    bcomp.name = "Base"
    Builder(design, bcomp).base(g)
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
