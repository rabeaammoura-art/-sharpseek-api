#!/usr/bin/env python3
"""Plain TPU phone case from measurements (no trial print needed: generous cutouts, printable without supports).

    python cad/phone_case.py cad/phones/honor_x6b.json [out_dir]

Outputs <out_dir>/<stem>.3mf (one TPU part, back face on the bed), .stl and _back.png (flat view from outside).

Coordinates while building = "outside view": looking at the BACK of the phone, x to the right, y down from the top end.
The mesh is NOT mirrored: printer frame = outside-view frame. Back-down on the bed, Bambu Studio's bottom view (key 2) shows the back like the phone (top up, camera top-left). NEVER mirror in x alone: that makes a mirror-image case.

Design rules (all printable without supports):
- back plate 1.6 mm, wall 1.6 mm, pocket = phone + 0.2 mm each side
- 45 degree staircase lip (0.2 mm steps) that overlaps the front by 1.2 mm and stands 0.6 mm above the glass
- camera = one big through cutout in the back plate (margin around the island)
- buttons / bottom = notches open to the top (a long closed slot would be a 45 mm TPU bridge and sag)
- outer back edge chamfered 0.6 mm in 3 steps (no elephant foot, each layer grows outward)
"""
import json, sys, zipfile
from pathlib import Path
import numpy as np
import manifold3d as mf
import trimesh
from shapely.geometry import box, Polygon
from shapely import set_precision

TB = 1.6        # back plate
WALL = 1.6
CLR = 0.2       # clearance per side
LIP = 1.2       # overlap over the front
STEP = 0.2
LOGO_T = 0.61    # logo layer thickness = pocket depth (3 layers of 0.2; 0.61 keeps the top face off the 0.6 plane)
EPS = 0.01       # keep step faces off the exact 0.2 mm planes (slicers cut at mid-layer; avoids coincident-plane artefacts)


def rrect(x0, y0, x1, y1, r):
    r = max(min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3), 0)
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, resolution=24) if r > 0 else box(x0, y0, x1, y1)


def cs(poly):
    rings = []
    geoms = list(poly.geoms) if hasattr(poly, "geoms") else [poly]
    for g in geoms:
        if g.geom_type != "Polygon" or g.area < 1e-4:
            continue
        g = set_precision(g.simplify(0.003), 0.001)
        rings.append(np.array(g.exterior.coords[:-1], float))
        for r in g.interiors:
            rings.append(np.array(r.coords[:-1], float))
    return mf.CrossSection(rings, mf.FillRule.EvenOdd)


def prism(poly, z0, z1):
    m = mf.Manifold.extrude(cs(poly), z1 - z0)
    return m.translate((0, 0, z0))


def build(cfg):
    global CLR, LIP
    CLR = cfg.get("clearance", 0.2)        # pocket clearance per side (first real print, 2026-11-25: 0.2 was a touch loose -> 0.1)
    lc = cfg.get("lip", {})
    LIP = lc.get("inset", 1.2)             # how far the front lip overlaps the screen (the owner's proven iPhone case: 2.37 mm)
    lip_above = lc.get("above", 0.6)       # how far it stands above the glass (proven case: 1.1 mm)
    A, B, C, R = cfg["A"], cfg["B"], cfg["C"], cfg["R"]
    cam = cfg["camera"]
    ox0, oy0, ox1, oy1 = -CLR - WALL, -CLR - WALL, B + CLR + WALL, A + CLR + WALL
    R_out = R + CLR + WALL
    outer = rrect(ox0, oy0, ox1, oy1, R_out)
    pocket = rrect(-CLR, -CLR, B + CLR, A + CLR, R + CLR)
    # z levels (multiples of 0.2 where it matters)
    z_c0 = round((TB + C - LIP - 0.2) / STEP) * STEP + EPS   # lip chamfer starts (45 deg staircase, ends 0.2 below the glass plane)
    z_c1 = z_c0 + LIP                                  # chamfer ends (inset = LIP)
    z_top = round((TB + C + lip_above) / STEP) * STEP

    # outer body with chamfered back edge
    body = None
    parts = []
    for i, inset in enumerate((0.6, 0.4, 0.2)):
        parts.append(prism(outer.buffer(-inset), 0 if i == 0 else i * STEP + EPS, (i + 1) * STEP + EPS))
    parts.append(prism(outer, 0.6 + EPS, z_top))
    body = parts[0]
    for p in parts[1:]:
        body = body + p

    # cavity: straight part, staircase chamfer, lip throat
    cav = [prism(pocket, TB, z_c0)]
    n = int(round(LIP / STEP))
    for i in range(1, n + 1):
        cav.append(prism(pocket.buffer(-STEP * i), z_c0 + STEP * (i - 1), z_c0 + STEP * i))
    cav.append(prism(pocket.buffer(-LIP), z_c1, z_top + 1.0))
    # camera through-hole in the back plate
    E, F, G, H, M = cam["E"], cam["F"], cam["G"], cam["H"], cam["margin"]
    camhole = prism(rrect(E - M, F - M, E + G + M, F + H + M, cam.get("radius", 8.0)), -1.0, TB + 0.01)
    cut = cav[0]
    for c in cav[1:]:
        cut = cut + c
    cut = cut + camhole

    # notches open to the top: rounded rectangle in the side plane, extruded through the wall + lip
    nz0 = TB + 1.5
    L = WALL + CLR + LIP + 2.0
    for nt in cfg.get("notches", []):
        if nt["side"] == "left":
            sec = rrect(nt["from_top"], nz0, nt["to_top"], z_top + 3.0, 1.2)       # (y, z) plane
            m = mf.Manifold.extrude(cs(sec), L)
            M3 = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)       # x = h, y = p, z = q
            cut = cut + m.transform(M3).translate((-CLR - WALL - 1.0, 0, 0))
        elif nt["side"] == "right":                                                # right edge seen from the back
            sec = rrect(nt["from_top"], nz0, nt["to_top"], z_top + 3.0, 1.2)       # (y, z) plane
            m = mf.Manifold.extrude(cs(sec), L)
            M3 = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)
            cut = cut + m.transform(M3).translate((B + CLR + WALL + 1.0 - L, 0, 0))
        elif nt["side"] == "bottom":
            sec = rrect(nt["x0"], nz0, nt["x1"], z_top + 3.0, 1.2)                 # (x, z) plane
            m = mf.Manifold.extrude(cs(sec), L)
            M3 = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], float)       # x = p, y = h, z = q
            cut = cut + m.transform(M3).translate((0, A + CLR - LIP - 1.0, 0))
    # optional flush logo on the back: pocket in the plate + two colour parts (navy, orange) of the same shape
    logo = {}
    lg = cfg.get("logo")
    if lg:
        import pickle
        import shapely
        from shapely import wkb
        from shapely.affinity import affine_transform
        navy, orange, foot, uc, vc = [wkb.loads(x) if isinstance(x, bytes) else x for x in pickle.load(open(lg["polys"], "rb"))]
        sc = lg.get("scale", 0.85)
        T = [sc, 0, 0, -sc, lg["cx"] - sc * uc, lg["cy"] + sc * vc]      # reading view (v up) -> outside view (y down)

        def lp(g):
            g = affine_transform(g, T).buffer(-0.02, join_style=2).buffer(0.02, join_style=2).simplify(0.004)
            return shapely.set_precision(g, 0.001)
        navy_p, orange_p, foot_p = lp(navy), lp(orange), lp(foot)
        # "cover": clear TPU laid over the logo (first layer(s) from the bed). 0 = logo flush with the outside face.
        cover = lg.get("cover", 0.0)
        thick = lg.get("thickness", 0.6)
        z0 = cover + EPS if cover else 0.0
        z1 = z0 + (thick if cover else LOGO_T)
        cut = cut + prism(foot_p, z0 if cover else -1.0, z1)       # sealed: an enclosed pocket, filled exactly by the colour parts
        logo = {"Logo_navy": (prism(navy_p, z0, z1), 2), "Logo_orange": (prism(orange_p, z0, z1), 3)}
        logo_polys = (navy_p, orange_p)
    else:
        logo_polys = None

    # optional colour sheet sealed inside the back plate, behind the logo (clear TPU outside 0.6 | colour 0.4 | clear TPU inside):
    # inset from the phone outline and away from the camera cutout so a stiff PETG sheet never reaches the bending edges
    pk = cfg.get("pink")
    pink_poly = None
    if pk:
        import shapely
        E, F, G, H, M = cam["E"], cam["F"], cam["G"], cam["H"], cam["margin"]
        cm = pk.get("cam_margin", 3.0)
        cam_box = rrect(E - M - cm, F - M - cm, E + G + M + cm, F + H + M + cm, cam.get("radius", 8.0) + cm)
        pink_poly = shapely.set_precision(rrect(0, 0, B, A, R).buffer(-pk.get("inset", 5.0)).difference(cam_box).simplify(0.003), 0.001)
        if lg and lg.get("cover"):
            pz0, pz1 = z0, z1          # same band as the logo; the logo footprint stays free of pink (the logo sits IN the pink)
            pink_poly = shapely.set_precision(pink_poly.difference(foot_p).simplify(0.003), 0.001)
        else:
            pz0, pz1 = LOGO_T, LOGO_T + pk.get("thickness", 0.4)
        cut = cut + prism(pink_poly, pz0, pz1)                   # pocket = exactly the part volume
        logo["Pink_PETG"] = (prism(pink_poly, pz0, pz1), 4)

    def to_tm(m):
        mesh = m.to_mesh()   # printer frame = outside-view frame (x right, y down, z into the phone): Bambu Studio 'bottom view' (key 2) shows the back exactly like the phone
        return trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3].astype(float), np.array(mesh.tri_verts), process=False)
    tm = to_tm(body - cut)
    extras = [(name, to_tm(m), ext) for name, (m, ext) in logo.items()]
    return tm, dict(z_top=z_top, z_c0=z_c0, z_c1=z_c1, outer=(ox1 - ox0, oy1 - oy0), logo_polys=logo_polys, pink_poly=pink_poly), extras


def write_3mf(tm, out, name, extras=(), body_colour=None):
    """Bambu-native 3MF (same writer as the coasters): case = filament slot 1 (clear TPU, right nozzle), extras = [(name, mesh, slot)].
    All parts share one shift so the colour parts sit exactly in the pocket."""
    sys.path.insert(0, str(Path(__file__).parent))
    from threemf import write_bambu_3mf
    b = tm.bounds
    shift = [-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]]
    parts = []
    for pn, m, ex in [(name + "_case_TPU", tm, 1)] + list(extras):
        m = m.copy(); m.apply_translation(shift); parts.append((pn, m, ex))
    cfg = json.loads((Path(__file__).parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = [body_colour or "#E8F1F5", "#1E34A0", "#FF6E14", "#F4A6C6" if any(e == 4 for _, _, e in extras) else "#FFFFFF"]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    write_bambu_3mf(Path(out), parts, (175.0, 160.0), name, json.dumps(cfg, indent=4))


def preview(cfg, out, info=None):
    """Flat view of the BACK from outside with all cutouts (to scale)."""
    from PIL import Image, ImageDraw
    A, B, R, cam = cfg["A"], cfg["B"], cfg["R"], cfg["camera"]
    S = 6.0; pad = 40
    W, H = int((B + 2 * (CLR + WALL)) * S) + 2 * pad, int((A + 2 * (CLR + WALL)) * S) + 2 * pad
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    off = CLR + WALL
    P = lambda x, y: (pad + (x + off) * S, pad + (y + off) * S)
    def rr(x0, y0, x1, y1, r, **k): d.rounded_rectangle((*P(x0, y0), *P(x1, y1)), radius=r * S, **k)
    rr(-off, -off, B + off, A + off, R + off, fill=(205, 232, 238), outline=(28, 52, 160), width=3)
    rr(-CLR, -CLR, B + CLR, A + CLR, R + CLR, fill=(255, 255, 255), outline=(150, 150, 150), width=2)
    E, F, G, Hh, M = cam["E"], cam["F"], cam["G"], cam["H"], cam["margin"]
    rr(E - M, F - M, E + G + M, F + Hh + M, cam.get("radius", 8), fill=(0, 0, 0))
    for nt in cfg.get("notches", []):
        if nt["side"] == "left":
            d.rectangle((*P(-off - 0.5, nt["from_top"]), *P(LIP, nt["to_top"])), fill=(255, 110, 20))
        elif nt["side"] == "right":
            d.rectangle((*P(B + CLR - LIP, nt["from_top"]), *P(B + off + 0.5, nt["to_top"])), fill=(255, 110, 20))
        elif nt["side"] == "bottom":
            d.rectangle((*P(nt["x0"], A + CLR - LIP), *P(nt["x1"], A + off + 0.5)), fill=(255, 110, 20))
    pp = (info or {}).get("pink_poly")
    if pp is not None:
        for q in (pp.geoms if hasattr(pp, "geoms") else [pp]):
            d.polygon([P(x, y) for x, y in q.exterior.coords], fill=(250, 214, 228))
            for r in q.interiors:
                d.polygon([P(x, y) for x, y in r.coords], fill=(255, 255, 255))
    lp = (info or {}).get("logo_polys")
    if lp:
        for g, col in zip(lp, ((28, 52, 160), (255, 110, 20))):
            for q in (g.geoms if hasattr(g, "geoms") else [g]):
                if q.geom_type != "Polygon":
                    continue
                d.polygon([P(x, y) for x, y in q.exterior.coords], fill=col)
                for r in q.interiors:
                    d.polygon([P(x, y) for x, y in r.coords], fill=(250, 214, 228) if pp is not None else (255, 255, 255))
    im.save(out)


def load_cfg(path):
    cfg = json.loads(Path(path).read_text())
    if "extends" in cfg:
        base = load_cfg(Path(path).parent / cfg["extends"])
        base.update({k: v for k, v in cfg.items() if k != "extends"})
        cfg = base
    return cfg


def check_orientation(tm, cfg):
    """Fail loudly if the case is a mirror image: the camera cutout must be a hole where the config puts it (x small = left seen
    from the back) and solid at the mirrored spot. Printer frame = outside-view frame, so this is a plain coordinate test."""
    cam = cfg["camera"]
    b = tm.bounds
    cx, cy = (b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2
    dx, dy = cam["E"] + cam["G"] / 2 - cfg["B"] / 2, cam["F"] + cam["H"] / 2 - cfg["A"] / 2
    z = 0.1     # below the colour sheet and the logo pockets (first layer), so the plate is solid except at the camera cutout
    from shapely.geometry import Polygon, Point
    sec = tm.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    region = None
    for loop in sec.discrete:                       # even-odd fill of the section: robust, unlike ray tests on a 600k-face mesh
        pg = Polygon(loop[:, :2]).buffer(0)
        region = pg if region is None else region.symmetric_difference(pg)
    inside = [region.contains(Point(cx + dx, cy + dy)), region.contains(Point(cx - dx, cy + dy)), region.contains(Point(cx + dx, cy - dy))]
    if inside[0] or not inside[1] or not inside[2]:
        raise SystemExit(f"ORIENTATION CHECK FAILED (mirror image?): camera spot solid={inside[0]}, mirrored spots solid={inside[1:]}")


def main():
    cfg_path = Path(sys.argv[1]); out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("cad/out/phones")
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_cfg(cfg_path)
    tm, info, extras = build(cfg)
    check_orientation(tm, cfg)
    stem = cfg_path.stem
    tm.export(out_dir / f"{stem}.stl")
    for n, m, e in extras:
        m.export(out_dir / f"{stem}_{n}.stl")          # same coordinates as the case STL (for print_test)
    write_3mf(tm, out_dir / f"{stem}.3mf", stem, extras, cfg.get("body_colour"))
    preview(cfg, out_dir / f"{stem}_back.png", info)
    t2 = trimesh.Trimesh(tm.vertices, tm.faces, process=True)
    print(f"{stem}: watertight={t2.is_watertight} volume={t2.volume:.0f} mm3 (TPU ~{t2.volume * 1.21 / 1000:.1f} g solid)")
    for n, m, e in extras:
        t3 = trimesh.Trimesh(m.vertices, m.faces, process=True)
        print(f"  {n}: slot {e} watertight={t3.is_watertight} volume={t3.volume:.0f} mm3")
    print("bounds", (t2.bounds[1] - t2.bounds[0]).round(2).tolist(), {k: v for k, v in info.items() if k not in ("logo_polys", "pink_poly")})


if __name__ == "__main__":
    main()
