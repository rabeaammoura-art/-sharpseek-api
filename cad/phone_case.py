#!/usr/bin/env python3
"""Plain TPU phone case from measurements (no trial print needed: generous cutouts, printable without supports).

    python cad/phone_case.py cad/phones/honor_x6b.json [out_dir]

Outputs <out_dir>/<stem>.3mf (one TPU part, back face on the bed), .stl and _back.png (flat view from outside).

Coordinates while building = "outside view": looking at the BACK of the phone, x to the right, y down from the top end.
The final mesh is mirrored in x (the part is printed back-down, so the outside is seen from below).

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
    A, B, C, R = cfg["A"], cfg["B"], cfg["C"], cfg["R"]
    cam = cfg["camera"]
    ox0, oy0, ox1, oy1 = -CLR - WALL, -CLR - WALL, B + CLR + WALL, A + CLR + WALL
    R_out = R + CLR + WALL
    outer = rrect(ox0, oy0, ox1, oy1, R_out)
    pocket = rrect(-CLR, -CLR, B + CLR, A + CLR, R + CLR)
    # z levels (multiples of 0.2 where it matters)
    z_c0 = round((TB + C - 1.4) / STEP) * STEP + EPS   # lip chamfer starts
    z_c1 = z_c0 + LIP                                  # chamfer ends (inset = LIP)
    z_top = round((TB + C + 0.6) / STEP) * STEP

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
        elif nt["side"] == "bottom":
            sec = rrect(nt["x0"], nz0, nt["x1"], z_top + 3.0, 1.2)                 # (x, z) plane
            m = mf.Manifold.extrude(cs(sec), L)
            M3 = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]], float)       # x = p, y = h, z = q
            cut = cut + m.transform(M3).translate((0, A + CLR - LIP - 1.0, 0))
    case = body - cut
    case = case.mirror((1, 0, 0))                              # outside view -> printer view
    mesh = case.to_mesh()
    tm = trimesh.Trimesh(np.array(mesh.vert_properties)[:, :3].astype(float), np.array(mesh.tri_verts), process=False)
    return tm, dict(z_top=z_top, z_c0=z_c0, z_c1=z_c1, outer=(ox1 - ox0, oy1 - oy0))


def write_3mf(tm, out, name):
    b = tm.bounds
    tm = tm.copy()
    tm.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    v, f = tm.vertices, tm.faces
    vs = "".join('<vertex x="%.5f" y="%.5f" z="%.5f"/>' % tuple(p) for p in v)
    ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t) for t in f)
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Application">BambuStudio-02.00.00.00</metadata>'
             '<resources><object id="1" type="model" name="%s"><mesh><vertices>%s</vertices><triangles>%s</triangles></mesh></object></resources>'
             '<build><item objectid="1" transform="1 0 0 0 1 0 0 0 1 160 160 0" printable="1"/></build></model>') % (name, vs, ts)
    ms = ('<?xml version="1.0" encoding="UTF-8"?><config><object id="1"><metadata key="name" value="%s"/><metadata key="extruder" value="1"/>'
          '</object><plate><metadata key="plater_id" value="1"/><model_instance><metadata key="object_id" value="1"/><metadata key="instance_id" value="0"/></model_instance></plate></config>') % name
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model); z.writestr("Metadata/model_settings.config", ms)


def preview(cfg, out):
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
        elif nt["side"] == "bottom":
            d.rectangle((*P(nt["x0"], A + CLR - LIP), *P(nt["x1"], A + off + 0.5)), fill=(255, 110, 20))
    im.save(out)


def main():
    cfg_path = Path(sys.argv[1]); out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("cad/out/phones")
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(cfg_path.read_text())
    tm, info = build(cfg)
    stem = cfg_path.stem
    tm.export(out_dir / f"{stem}.stl")
    write_3mf(tm, out_dir / f"{stem}.3mf", stem)
    preview(cfg, out_dir / f"{stem}_back.png")
    t2 = trimesh.Trimesh(tm.vertices, tm.faces, process=True)
    print(f"{stem}: watertight={t2.is_watertight} volume={t2.volume:.0f} mm3 (TPU ~{t2.volume * 1.21 / 1000:.1f} g solid)")
    print("bounds", (t2.bounds[1] - t2.bounds[0]).round(2).tolist(), info)


if __name__ == "__main__":
    main()
