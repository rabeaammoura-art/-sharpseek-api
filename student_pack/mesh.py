"""Piece -> watertight solids (manifold3d) -> STL / 3MF (one object, one named part per colour).

Each colour part is an extrusion of its 2D region from the base height to the colour's own height; the outline
colour part additionally carries the full-silhouette base slab.  Pencil plates get the horizontal teardrop tunnel.
"""
import struct
import zipfile
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from layout import Piece, _polys
from themes import THEMES


def _rings(g):
    out = []
    for p in _polys(g):
        out.append(np.asarray(p.exterior.coords)[:-1])
        out += [np.asarray(r.coords)[:-1] for r in p.interiors]
    return out


def extrude(g, z0, z1):
    rings = _rings(g)
    if not rings or z1 <= z0:
        return None
    return Manifold.extrude(CrossSection(rings, FillRule.EvenOdd), z1 - z0).translate((0, 0, z0))


def tunnel_solid(piece: Piece):
    """Horizontal teardrop tunnel along +X through the whole plate (apex up, flat roof: prints without supports)."""
    t = piece.tunnel
    r, zc, roof = t["d"] / 2, t["zc"], t["roof_cut"]
    c = r / np.sqrt(2)
    tear = Point(0, zc).buffer(r, 96).union(Polygon([(-c, zc + c), (c, zc + c), (0, zc + r * np.sqrt(2))]))
    tear = tear.intersection(Polygon([(-r - 1, zc - r - 1), (r + 1, zc - r - 1), (r + 1, zc + roof), (-r - 1, zc + roof)]))
    L = piece.bounds[2] + 2
    prof = Manifold.extrude(CrossSection([np.asarray(tear.exterior.coords)[:-1]], FillRule.EvenOdd), L + 2).translate((0, 0, -1))
    # extrusion axis z -> world X, profile x -> world Y (centred on tunnel y), profile y -> world Z
    m = np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0]], float)
    return prof.transform(m).translate((0, t["y"], 0))


def solids(piece: Piece):
    """colour -> Manifold"""
    out = {}
    for color, g in piece.parts.items():
        s = extrude(g, piece.base, piece.tops[color]) if color != piece.outline else extrude(g, piece.base, piece.tops[color])
        if color == piece.outline:
            slab = extrude(piece.silhouette, 0, piece.base)
            s = slab if s is None else slab + s
        if s is not None:
            out[color] = s
    if piece.outline not in out:
        out[piece.outline] = extrude(piece.silhouette, 0, piece.base)
    if piece.tunnel:
        out[piece.outline] = out[piece.outline] - tunnel_solid(piece)
    return out


def to_arrays(m: Manifold):
    mesh = m.to_mesh()
    return np.asarray(mesh.vert_properties, np.float64)[:, :3], np.asarray(mesh.tri_verts, np.int64)


def order(piece):
    """AMS slot order: outline colour first, then by height."""
    th = THEMES[piece.theme]
    cols = list(th["heights"])
    return [piece.outline] + sorted([c for c in cols if c != piece.outline], key=lambda c: (th["heights"][c], c))


def write_stl(path, V, F, name="3D ZONE TECH"):
    tri = V[F]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    rec = np.zeros(len(F), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri.reshape(-1, 9)
    with open(path, "wb") as f:
        f.write(name.encode().ljust(80, b" ")); f.write(struct.pack("<I", len(F))); f.write(rec.tobytes())


def slot_order(theme):
    """AMS slot order for a theme (same for every piece, so a mixed plate shares filaments): outline colour first, then by height."""
    th = THEMES[theme]
    cols = list(th["heights"])
    return [th["outline"]] + sorted([c for c in cols if c != th["outline"]], key=lambda c: (th["heights"][c], c))


def write_plate_3mf(path, items, filament_type="PETG"):
    """items = [(piece, solids, name, (x, y))] with (x, y) = lower-left of the piece on the plate (mm; the group should be
    centred on (128, 128), verify_slice.py moves it onto the real plate).  One 3MF object per item, one part per colour
    (named by colour, extruder = slot of the colour in the theme's slot order).  Pieces of different themes get their
    slots numbered one after the other, so a mixed plate needs up to 4 x themes filaments."""
    import json
    slots, slot_hex = {}, []
    for piece, sol, name, xy in items:
        th = THEMES[piece.theme]
        for c in slot_order(piece.theme):
            if (piece.theme, c) not in slots:
                slots[(piece.theme, c)] = len(slots) + 1
                slot_hex.append(th["filament_rgb"][c])
    objs, objects_xml, cfg_objs, builds = [], [], [], []
    nid = 1
    for piece, sol, name, (x, y) in items:
        asm = nid; nid += 1
        comps, parts = [], []
        for c in slot_order(piece.theme):
            if c not in sol:
                continue
            V, F = to_arrays(sol[c])
            vs = "".join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{z:.4f}"/>' for a, b, z in V)
            ts = "".join(f'<triangle v1="{a}" v2="{b}" v3="{cc}"/>' for a, b, cc in F)
            pid = nid; nid += 1
            objs.append(f'<object id="{pid}" name="{name}_{c}" type="model"><mesh><vertices>{vs}</vertices><triangles>{ts}</triangles></mesh></object>')
            comps.append(f'<component objectid="{pid}"/>')
            parts.append(f'<part id="{pid}" subtype="normal_part"><metadata key="name" value="{c}"/>'
                         f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>'
                         f'<metadata key="extruder" value="{slots[(piece.theme, c)]}"/></part>')
        objects_xml.append(f'<object id="{asm}" name="{name}" type="model"><components>' + "".join(comps) + '</components></object>')
        builds.append(f'<item objectid="{asm}" transform="1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0" printable="1"/>')
        cfg_objs.append(f'<object id="{asm}"><metadata key="name" value="{name}"/><metadata key="extruder" value="1"/>' + "".join(parts) + '</object>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Application">3D ZONE TECH student pack</metadata><resources>' + "".join(objs) + "".join(objects_xml) +
             '</resources><build>' + "".join(builds) + '</build></model>')
    inst = "".join(f'<model_instance><metadata key="object_id" value="{o}"/><metadata key="instance_id" value="0"/>'
                   f'<metadata key="identify_id" value="{o}"/></model_instance>'
                   for o in [int(m) for m in __import__("re").findall(r'<item objectid="(\d+)"', model)])
    model_cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>' + "".join(cfg_objs) +
                 '<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value=""/><metadata key="locked" value="false"/>'
                 '<metadata key="filament_map_mode" value="Manual"/><metadata key="filament_maps" value="' + " ".join("1" * len(slot_hex)) + '"/>'
                 + inst + '</plate></config>')
    project = json.dumps({"filament_colour": slot_hex, "filament_type": [filament_type] * len(slot_hex),
                          "filament_settings_id": [""] * len(slot_hex)})
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct); z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model); z.writestr("Metadata/model_settings.config", model_cfg)
        z.writestr("Metadata/project_settings.config", project)
    return slots


def arrange(pieces, gap=8.0, max_w=200.0, center=(128.0, 128.0)):
    """Shelf-pack piece footprints; returns lower-left (x, y) per piece, the group centred on `center`."""
    order = sorted(range(len(pieces)), key=lambda i: -pieces[i].size[1])
    pos, x, y, row_h, used_w = {}, 0.0, 0.0, 0.0, 0.0
    for i in order:
        w, d, _ = pieces[i].size
        if x > 0 and x + w > max_w:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        pos[i] = (x, y); x += w + gap; row_h = max(row_h, d); used_w = max(used_w, x - gap)
    total_h = y + row_h
    return [(pos[i][0] + center[0] - used_w / 2, pos[i][1] + center[1] - total_h / 2) for i in range(len(pieces))]


def write_3mf(path, piece: Piece, sol, name, plate_xy=(128.0, 128.0), filament_type="PETG"):
    """Single piece: one object, one part per colour (named by colour, extruder = AMS slot)."""
    w, d, _ = piece.size
    return write_plate_3mf(path, [(piece, sol, name, (plate_xy[0] - w / 2, plate_xy[1] - d / 2))], filament_type)


def export_piece(piece: Piece, outdir, stem):
    """Writes <stem>.3mf, <stem>.stl (all colours merged) and <stem>_<colour>.stl; returns a stats dict."""
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    sol = solids(piece)
    write_3mf(outdir / f"{stem}.3mf", piece, sol, stem)
    cols = [c for c in slot_order(piece.theme) if c in sol]
    allm = Manifold.batch_boolean(list(sol.values()), 0)   # union (the parts only touch face to face)
    V, F = to_arrays(allm)
    write_stl(outdir / f"{stem}.stl", V, F)
    stats = {"colours": cols, "volume_mm3": {}, "tris": {}}
    for c, m in sol.items():
        V2, F2 = to_arrays(m)
        write_stl(outdir / f"{stem}_{c}.stl", V2, F2)
        stats["volume_mm3"][c] = round(m.volume(), 1)
        stats["tris"][c] = len(F2)
        assert m.status().name == "NoError", (stem, c, m.status())
    stats["size_mm"] = [round(x, 2) for x in piece.size]
    return stats
