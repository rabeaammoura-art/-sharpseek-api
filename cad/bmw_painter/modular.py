"""BMW painter wall art - 600 mm, 3 interlocking modules (hidden rear sliding dovetails).
usage: python modular.py <stl_dir_with__black_and__blue (the approved 5 mm model)> <out_dir>
The approved artwork is read back from the supplied STL/3MF master (section at z=1), scaled x2.0149 -> 600 mm, 3 mm thick."""
import sys, json, math
from pathlib import Path
import numpy as np, trimesh
from shapely import affinity
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union, nearest_points

# ------------------------------------------------------------------ parameters (mm)
W_TARGET = 600.0
T = 3.0                      # visible body thickness
G = 0.20                     # total seam gap on the front face (0.1 per module face)
SEAMS = [196.0, 452.0]       # x of the two seams (chosen in negative space / lowest crossing count)
PWA = 7.0                    # male pad block width (rear), measured from the seam
PWB = 9.0                    # female pad block width (pocket depth E + 0.3 + 2.7 mm end wall)
E = 6.0                      # tab length across the seam
ANG = 12.0                   # dovetail flank angle (deg)
A0 = 1.8                     # tab half thickness at the root
C = 0.25                     # clearance per surface
FLOOR = 1.5                  # material under the pocket
CAP = 1.5                    # material over the pocket
STOP = 1.5                   # end wall of the lowest pocket
PADD = 1.8                   # a pad may stick out at most this far beyond the line edges (keeps it behind the artwork)
MINPAD = 5.0                 # shortest useful pad along the seam
MINBOND = 25.0               # minimum overlap of a pad with the body below it (mm2)
BIN = 0.3                    # tab-to-stop clearance along y
B0 = A0 + E * math.tan(math.radians(ANG))       # tab half thickness at the tip
ZC = T + FLOOR + B0 + C                          # centre height of the dovetail
ZTOP = ZC + B0 + C + CAP                         # top of the pads
BED = (325.0, 320.0)

def load_master(stl_dir):
    out = {}
    for n in ("black", "blue"):
        m = trimesh.load(Path(stl_dir) / f"bmw_painter__{n}.stl")
        sec = m.section(plane_origin=[0, 0, 1], plane_normal=[0, 0, 1])
        p, _ = sec.to_2D(to_2D=np.eye(4))
        out[n] = unary_union(p.polygons_full)
    u = unary_union([out["black"], out["blue"]]); b = u.bounds; k = W_TARGET/(b[2]-b[0])
    f = lambda g: affinity.scale(affinity.translate(g, -b[0], -b[1]), k, k, origin=(0, 0))
    return f(out["black"]), f(out["blue"]), k

def crossings(U, BU, xs):
    H = U.bounds[3]
    ln = LineString([(xs, -1), (xs, H+1)]).intersection(U)
    parts = [ln] if ln.geom_type == "LineString" else list(ln.geoms)
    iv = []
    for p in parts:
        if p.is_empty: continue
        ys = sorted([p.coords[0][1], p.coords[-1][1]])
        blue_len = LineString([(xs, ys[0]), (xs, ys[1])]).intersection(BU).length
        iv.append([ys[0], ys[1], "blue" if blue_len > 0.5*(ys[1]-ys[0]) else "black"])
    return sorted(iv)

def pads_for(U, BU, xs):
    """one pad per crossing: the longest y-range around the crossing for which the whole band [xs-PWA, xs+PWB] stays inside the
    artwork grown by PADD (so the pad hides behind the lines)."""
    H = U.bounds[3]; Ud = U.buffer(PADD, join_style=2); out = []
    for y0, y1, col in crossings(U, BU, xs):
        yc = (y0+y1)/2; lo, hi = y0-PADD, y1+PADD
        for x in np.arange(xs-PWA, xs+PWB+0.01, 0.5):
            ln = LineString([(x, -1), (x, H+1)]).intersection(Ud); parts = [ln] if ln.geom_type == "LineString" else list(ln.geoms)
            ok = [tuple(sorted([q.coords[0][1], q.coords[-1][1]])) for q in parts if not q.is_empty]
            ok = [(a_, b_) for a_, b_ in ok if a_ <= yc <= b_]
            if not ok: lo, hi = 1, 0; break
            lo = max(lo, ok[0][0]); hi = min(hi, ok[0][1])
        if hi - lo >= MINPAD:
            bond = box(xs-PWA, lo, xs+PWB, hi).intersection(U).area
            if bond >= MINBOND: out.append((lo, hi, col))
    return out

import manifold3d as m3
from collections import Counter

def cs_of(geom, clean=False):
    rings = []
    for pg in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        if pg.is_empty or pg.area < 0.05: continue
        rings.append(np.array(pg.exterior.coords)[:-1]); rings += [np.array(i.coords)[:-1] for i in pg.interiors]
    cs = m3.CrossSection(rings, m3.FillRule.EvenOdd)
    if clean: cs = cs.offset(-0.04, m3.JoinType.Round, 2.0, 16).offset(0.04, m3.JoinType.Round, 2.0, 16)
    return cs

def extrude(geom, z0, z1, clean=False):
    if geom.is_empty or geom.area < 0.05: return m3.Manifold()
    return m3.Manifold.extrude(cs_of(geom, clean), z1 - z0).translate((0, 0, z0))

def block(x0, x1, y0, y1, z0, z1):
    return m3.Manifold.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

def prism_xz(poly_xz, ya, yb):
    """polygon given in (x, z), extruded along y from ya to yb"""
    cs = m3.CrossSection([np.array(poly_xz, float)], m3.FillRule.EvenOdd)
    m = m3.Manifold.extrude(cs, yb - ya)          # X, Y(=z), Z(=y length)
    return m.rotate((90, 0, 0)).translate((0, yb, 0))

def to_tm(mf):
    me = mf.to_mesh()
    return trimesh.Trimesh(np.array(me.vert_properties)[:, :3], np.array(me.tri_verts), process=False)

def bad_pts(tm):
    r = trimesh.load(trimesh.util.wrap_as_stream(tm.export(file_type="stl")), file_type="stl")
    c = Counter(map(tuple, r.edges_sorted))
    return list({(round(r.vertices[i][0], 1), round(r.vertices[i][1], 1)) for k_, v in c.items() if v != 2 for i in k_})

def healed(geom, log):
    for _ in range(4):
        tm = to_tm(extrude(geom, 0, T)) if not geom.is_empty and geom.area > 0.05 else None
        if tm is None: return geom
        bp = bad_pts(tm)
        if not bp: return geom
        log.append(bp); geom = unary_union([geom] + [Point(x, y).buffer(0.8) for x, y in bp])
    return geom

def half(s, x):               # tab half thickness at x (root at the male face)
    xr = s - G/2
    return A0 + (B0 - A0) * (x - xr) / (E + G)

def build(BK, BU, out):
    U = unary_union([BK, BU]); H = U.bounds[3]
    edges = [0.0] + SEAMS + [W_TARGET]
    seam_pads = {s: pads_for(U, BU, s) for s in SEAMS}
    mods = []
    info = {"scale": W_TARGET/ (U.bounds[2]-U.bounds[0]), "seams": {}, "modules": [], "ties": []}
    for s in SEAMS: info["seams"][s] = [dict(y0=round(a, 2), y1=round(b, 2), colour=c) for a, b, c in seam_pads[s]]
    for i in range(3):
        xa = edges[i] + (G/2 if i > 0 else 0); xb = edges[i+1] - (G/2 if i < 2 else 0)
        bx = box(xa, -1, xb, H+1)
        bk, bu = BK.intersection(bx), BU.intersection(bx)
        # pads (planforms) of this module
        pads = []   # (kind, seam, y0, y1, colour, index)
        if i > 0:
            s = SEAMS[i-1]
            for j, (y0, y1, c) in enumerate(seam_pads[s]): pads.append(("female", s, y0, y1, c, j))
        if i < 2:
            s = SEAMS[i]
            for j, (y0, y1, c) in enumerate(seam_pads[s]): pads.append(("male", s, y0, y1, c, j))
        def pad_plan(kind, s, y0, y1):
            return box(s-G/2-PWA, y0, s-G/2, y1) if kind == "male" else box(s+G/2, y0, s+G/2+PWB, y1)
        # islands -> rear tie bars (hidden behind the lines)
        foot = unary_union([bk, bu])
        plan = unary_union([pad_plan(k, s_, a, b) for k, s_, a, b, c, j in pads]) if pads else None
        glue = foot if plan is None else unary_union([foot, plan.intersection(foot.buffer(0.01))])
        comps = sorted(list(foot.geoms) if hasattr(foot, "geoms") else [foot], key=lambda g: -g.area)
        # connectivity including pad bridging: a pad planform overlapping several components joins them
        ties = []
        groups = [[c] for c in comps]
        def merge_groups():
            changed = True
            while changed:
                changed = False
                for a_ in range(len(groups)):
                    for b_ in range(a_+1, len(groups)):
                        ga, gb = unary_union(groups[a_]), unary_union(groups[b_])
                        joined = False
                        if ga.intersects(gb): joined = True
                        elif plan is not None:
                            for pp in (plan.geoms if hasattr(plan, "geoms") else [plan]):
                                if pp.intersection(ga).area > 4 and pp.intersection(gb).area > 4: joined = True
                        if joined:
                            groups[a_] += groups[b_]; del groups[b_]; changed = True; break
                    if changed: break
        merge_groups()
        while len(groups) > 1:
            main = unary_union(groups[0])
            best = min(range(1, len(groups)), key=lambda g: main.distance(unary_union(groups[g])))
            other = unary_union(groups[best]); p1, p2 = nearest_points(main, other)
            ln = LineString([p1, p2])
            if ln.length < 0.01: ln = LineString([(p1.x-1, p1.y), (p1.x+1, p1.y)])
            d = ln.length; ux, uy = (p2.x-p1.x)/max(d, 1e-9), (p2.y-p1.y)/max(d, 1e-9)
            ext = LineString([(p1.x-ux*2.5, p1.y-uy*2.5), (p2.x+ux*2.5, p2.y+uy*2.5)])
            bar = ext.buffer(2.0, cap_style="flat")
            col = "blue" if bu.intersection(bar).area > 0.5*bar.intersection(foot).area else "black"
            ties.append((bar, col)); info["ties"].append(dict(module=i+1, at=[round(p1.x, 1), round(p1.y, 1)], gap=round(d, 2), colour=col))
            groups[0] += groups[best]; del groups[best]
        # ---------------- 3D
        heal_log = []
        fu = unary_union([bk, bu]); dab = healed(fu, heal_log).difference(fu)      # black/blue touching in one point -> tiny dab
        if not dab.is_empty: bk = unary_union([bk, dab])
        bk, bu = healed(bk, heal_log), healed(bu, heal_log)
        if heal_log: info.setdefault("healed_pinch_points", {})[str(i+1)] = heal_log
        body = {"black": extrude(bk, 0, T), "blue": extrude(bu, 0, T)}
        body_all = extrude(unary_union([bk, bu]), 0, T)
        parts = {"black": m3.Manifold(), "blue": m3.Manifold()}      # extras only (pads, tabs, ties)
        for bar, col in ties: parts[col] = parts[col] + extrude(bar, T-0.02, T + 2.2, clean=False)
        for kind, s, y0, y1, c, j in pads:
            lowest = (j == 0)
            if kind == "male":
                pb = block(s-G/2-PWA, s-G/2-0.03, y0, y1, T-0.02, ZTOP)
                xr, xt = s-G/2-0.5, s+G/2+E
                prof = [(xr, ZC-half(s, xr)), (xt, ZC-half(s, xt)), (xt, ZC+half(s, xt)), (xr, ZC+half(s, xr))]
                tab = prism_xz(prof, y0 + (STOP if lowest else 0) + BIN, y1)
                parts[c] = parts[c] + pb + tab
            else:
                pb = block(s+G/2+0.03, s+G/2+PWB, y0, y1, T-0.02, ZTOP)
                xm, xt = s+G/2-0.5, s+G/2+E+0.3
                prof = [(xm, ZC-half(s, xm)-C), (xt, ZC-half(s, xt)-C), (xt, ZC+half(s, xt)+C), (xm, ZC+half(s, xm)+C)]
                pocket = prism_xz(prof, (y0 + STOP) if lowest else (y0 - 1), y1 + 1)
                parts[c] = parts[c] + (pb - pocket)
        parts_extras_black, parts_extras_blue = parts['black'], parts['blue']
        parts = {c: body[c] + parts[c] for c in parts}
        all_m = body_all + (parts_extras_black + parts_extras_blue)
        mods.append(dict(i=i+1, xa=xa, xb=xb, parts=parts, all=all_m, pads=pads, ties=ties, foot=foot))
    return mods, info

def mir(tm):
    """The modules are printed FRONT FACE DOWN (z=0 is the front, rear pads on top). Seen from the front (from below) the art would be
    mirrored, so every exported mesh is mirrored in x: the printed/assembled model then reads correctly from the front."""
    t = tm.copy(); v = t.vertices.copy(); v[:, 0] = W_TARGET - v[:, 0]; t.vertices = v; t.faces = t.faces[:, ::-1]; return t

def bad_edges(tm):
    r = trimesh.load(trimesh.util.wrap_as_stream(tm.export(file_type="stl")), file_type="stl")
    c = Counter(map(tuple, r.edges_sorted)); return sum(1 for v in c.values() if v != 2), len(r.split(only_watertight=False))

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from threemf import build_project_settings, write_bambu_3mf
    BK, BU, k = load_master(sys.argv[1]); out = Path(sys.argv[2]); (out / "stl").mkdir(parents=True, exist_ok=True); (out / "3mf").mkdir(exist_ok=True)
    mods, info = build(BK, BU, out); U = unary_union([BK, BU])
    rep = {"scale_factor": round(k, 5), "overall_mm": [round(v, 2) for v in U.bounds[2:]], "body_mm": T, "seams_x": SEAMS, "gap_front_mm": G,
           "dovetail": dict(tab_len=E, flank_deg=ANG, root_thickness=round(2*A0, 2), tip_thickness=round(2*B0, 2), clearance_per_surface=C, pad_height_above_body=round(ZTOP-T, 2), pad_width_male=PWA, pad_width_female=PWB, zc=round(ZC, 2), top_z=round(ZTOP, 2)),
           "modules": [], "pairs": [], "pads": info["seams"], "ties": info["ties"]}
    tpl = (Path(__file__).resolve().parents[1] / "config" / "bambu_project_4fil_pla.config").read_bytes()
    cols = ["#141414", "#1535C8", "#1A1A1A", "#1A1A1A"]
    mfs, tms, glob_parts = [], [], []
    for m in mods:
        allm = m["all"]; mfs.append(allm)
        tmb, tmu, tma = mir(to_tm(m["parts"]["black"])), mir(to_tm(m["parts"]["blue"])), mir(to_tm(allm)); tms.append(tma)
        x0 = float(tma.bounds[0][0]); shifted = {}
        for name, tm in (("black", tmb), ("blue", tmu), ("all", tma)):
            if len(tm.faces) == 0: continue
            t2 = tm.copy(); t2.apply_translation([-x0, 0, 0]); shifted[name] = t2
            t2.export(out / "stl" / (f"module{m['i']}__{name}.stl" if name != "all" else f"module{m['i']}.stl"))
            if name != "all": glob_parts.append((f"m{m['i']}_{name}", tm.copy(), 1 if name == "black" else 2))
        # print-ready 3MF (front face on the bed, prime tower above the piece in Y)
        b = shifted["all"].bounds; mid = ((b[0][0]+b[1][0])/2, (b[0][1]+b[1][1])/2)
        pl = []
        for name, slot in (("black", 1), ("blue", 2)):
            if name in shifted:
                t3 = shifted[name].copy(); t3.apply_translation([-mid[0], -mid[1], 0]); pl.append((name, t3, slot))
        write_bambu_3mf(str(out / "3mf" / f"module{m['i']}_print.3mf"), pl, center=(162.5, 110.0), name=f"module{m['i']}",
                        project_settings=build_project_settings(tpl, cols, (150.0, 255.0, 30.0)))
        sz = (b[1]-b[0]); nbad, nbod = bad_edges(tma)
        # pad bond area (planform on the body) and joint contact area
        bonds = []
        for kind, s_, y0, y1, c, j in m["pads"]:
            pp = box(s_-G/2-PWA, y0, s_-G/2, y1) if kind == "male" else box(s_+G/2, y0, s_+G/2+PWB, y1)
            bonds.append(round(pp.intersection(m["foot"]).area, 1))
        rep["modules"].append(dict(module=m["i"], global_x0=round(x0, 3), x_from=round(m["xa"], 2), x_to=round(m["xb"], 2), size_xyz_mm=sz.round(2).tolist(), fits_H2D=bool(sz[0] <= BED[0] and sz[1] <= BED[1]),
            volume_cm3=round(float(tma.volume)/1000, 2), grams_pla_est=round(float(tma.volume)*1.24/1000*0.9, 1), watertight=bool(tma.is_watertight), bad_edges_after_stl_export=nbad, shells=nbod,
            pads=len(m["pads"]), pad_bond_area_mm2_min=min(bonds) if bonds else None, rear_ties=len(m["ties"])))
        print(rep["modules"][-1])
    # assembled 3MF (display file: 600 mm is larger than one plate)
    allb = trimesh.util.concatenate([t for _, t, _ in glob_parts]).bounds; mid = ((allb[0][0]+allb[1][0])/2, (allb[0][1]+allb[1][1])/2)
    for _, t, _ in glob_parts: t.apply_translation([-mid[0], -mid[1], 0])
    write_bambu_3mf(str(out / "bmw_painter_600_assembled.3mf"), glob_parts, center=(162.5, 105.0), name="bmw_painter_600_assembled",
                    project_settings=build_project_settings(tpl, cols, (150.0, 255.0, 30.0)))
    trimesh.util.concatenate(tms).export(out / "bmw_painter_600_assembled.stl")
    # clearances / interference
    for a_, b_ in ((0, 1), (1, 2), (0, 2)):
        inter = (mfs[a_] ^ mfs[b_]).volume(); gap = mfs[a_].min_gap(mfs[b_], 5.0)
        rep["pairs"].append(dict(pair=f"M{a_+1}-M{b_+1}", interference_mm3=round(inter, 4), min_gap_mm=round(gap, 3)))
    # front face
    front = unary_union([m["foot"] for m in mods]); rep["front_face"] = dict(area_original=round(U.area, 1), area_assembled=round(front.area, 1), lost_to_seam_mm2=round(U.area-front.area, 2),
        extra_mm2=round(front.difference(U).area, 3), seam_hairline_mm=G)
    thin = {}
    for w in (1.2, 2.0, 3.0):
        op = U.buffer(-w/2, join_style=1).buffer(w/2, join_style=1); thin[f"area_pct_thinner_than_{w}mm"] = round(100*(U.area-op.area)/U.area, 2)
    rep["thin_feature_audit"] = thin
    import math as _m
    flank = _m.hypot(E, B0-A0)
    rep["joint_contact"] = {str(s): round(2*flank*sum(b-a-BIN-(STOP if n_ == 0 else 0) for n_, (a, b, _) in enumerate(pads_for(U, BU, s)))*1.0, 0) for s in SEAMS}
    (out / "validation.json").write_text(json.dumps(rep, indent=1, default=str)); print(json.dumps({k_: rep[k_] for k_ in ("pairs", "front_face", "thin_feature_audit", "joint_contact")}, indent=1))
