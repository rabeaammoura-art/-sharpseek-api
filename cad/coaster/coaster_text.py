"""Clear TPU coaster with a name + a line of text sealed inside, face down (owner 2026-11-23).

    python cad/coaster/coaster_text.py --name "رانيا" --line "تطيل النظر بمحبة وتأمل" --font FONT.ttf --out OUT.3mf

Ø95 x 3.0 mm. Layers from the plate (= the front): TPU 0.4 | inlay 0.6 (text + decoration) | TPU 2.0 behind.
Decoration (--deco REF.3mf --deco-object N): branches / flowers taken from the owner's own plate 3MF (his design,
file stays out of git): its colour parts on the face, minus its text (black bits not hugging a flower are dropped). Rounded edges r 0.6. Mirrored in the
file so it reads right when turned over. Slots: 1 clear TPU (nozzle 2), 2 text colour (nozzle 1).
Then put the clear-TPU slicer settings in with bambu_slice.py + clear_tpu_settings.py (see that file).
Font files stay out of git (licences unknown).
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import coaster                       # noqa: E402
import newborn_plaque as npq         # noqa: E402
from threemf import write_bambu_3mf  # noqa: E402

D, ROUND, EDGE = 95.0, 0.6, 4.0
Z0, Z1, T = 0.4, 1.0, 3.0           # inlay between Z0 and Z1: 0.4 clear TPU in front (owner: keep the cover), 0.6 deep


def shaped(text, font):
    g = npq.shape_run(npq.Font(font), text, 20.0, "rtl", "Arab")[0]
    b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)


def layout(name, line, font, name_w=62.0, line_w=68.0, gap=4.0, grow=0.2, grow_line=0.38):
    n, l = shaped(name, font), shaped(line, font)
    sn = name_w / (n.bounds[2] - n.bounds[0]); n = affinity.scale(n, sn, sn, origin=(0, 0))
    sl = line_w / (l.bounds[2] - l.bounds[0]); l = affinity.scale(l, sl, sl, origin=(0, 0))
    hn, hl = n.bounds[3] - n.bounds[1], l.bounds[3] - l.bounds[1]
    total = hn + gap + hl
    n = affinity.translate(n, 0, total / 2 - hn / 2)
    l = affinity.translate(l, 0, -total / 2 + hl / 2)
    disc = Point(0, 0).buffer(D / 2 - EDGE, 256)
    while not disc.contains(unary_union([n, l]).buffer(grow_line)):       # shrink both until they fit the circle
        n = affinity.scale(n, 0.97, 0.97, origin=(0, 0)); l = affinity.scale(l, 0.97, 0.97, origin=(0, 0))
    return n.buffer(grow, 16), l.buffer(grow_line, 16)        # the small line needs more: its strokes are ~0.4 mm


def face_polys(model_xml, k):
    """part k (1-based) of an object_N.model: its faces lying on z = 0 -> shapely, seen from the front (x flipped)"""
    import re
    from shapely.geometry import Polygon
    objs = list(re.finditer(r'<object id="(\d+)"[^>]*>(.*?)</object>', model_xml, re.S))
    body = objs[k - 1].group(2)
    v = np.array(re.findall(r'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', body), float)
    t = np.array(re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', body), int)
    tri = v[t]
    keep = np.all(np.abs(tri[:, :, 2]) < 1e-6, axis=1)
    polys = [Polygon(p[:, :2] * np.array([-1, 1])).buffer(0.001) for p in tri[keep]]
    return unary_union(polys).buffer(-0.001)


def decoration(ref, obj):
    """{colour part name: geometry} from the owner's plate: olive, brown, accent and the black outlines of the flowers"""
    import zipfile
    xml = zipfile.ZipFile(ref).read(f"3D/Objects/object_{obj}.model").decode("utf-8")
    clean = lambda g: g.buffer(0.03, 8).buffer(-0.03, 8).simplify(0.02)     # merge the triangle soup into clean outlines
    black, olive, brown, accent = (clean(face_polys(xml, k)) for k in (2, 3, 4, 5))
    near = accent.buffer(1.2)
    bits = list(getattr(black, "geoms", [black]))
    outlines = unary_union([g for g in bits if g.intersects(near)])                  # flower outlines kept
    text_box = unary_union([g for g in bits if not g.intersects(near)]).bounds     # where the owner's text sat
    return {"black": outlines, "olive": olive, "brown": brown, "accent": accent}, text_box


def rounded_disc():
    outline = Point(0, 0).buffer(D / 2, 256)
    n = int(round(T / 0.1)); slabs = []
    for i in range(n):
        za, zb = i * T / n, (i + 1) * T / n; zm = (za + zb) / 2
        d = max(0.0, ROUND - zm, zm - (T - ROUND))
        inset = ROUND - np.sqrt(max(ROUND ** 2 - d ** 2, 0.0))
        slabs.append(coaster.extrude(outline.buffer(-inset, 64), za - (0.005 if i else 0), zb + (0.005 if i < n - 1 else 0)))
    return trimesh.boolean.union(slabs, engine="manifold")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--line", required=True); ap.add_argument("--font", required=True)
    ap.add_argument("--cover", type=float, default=0.4, help="clear TPU in front of the inlay")
    ap.add_argument("--depth", type=float, default=0.6, help="inlay thickness")
    ap.add_argument("--deco", help="owner's plate 3MF to take the branches / flowers from")
    ap.add_argument("--deco-object", type=int, default=3, help="which plate of that file (1, 2, 3)")
    ap.add_argument("--colour", default="#1F5FA8"); ap.add_argument("--out", required=True); ap.add_argument("--stl", action="store_true")
    a = ap.parse_args()
    global Z0, Z1
    Z0, Z1 = a.cover, a.cover + a.depth
    n, l = layout(a.name, a.line, a.font)
    deco, box = decoration(a.deco, a.deco_object) if a.deco else (None, None)
    if deco:   # text where the owner's text was, as big as fits, 1.2 mm of TPU from the branches / flowers
        g = unary_union([n, l]); b = g.bounds
        sc = min((box[2] - box[0]) / (b[2] - b[0]), (box[3] - box[1]) / (b[3] - b[1])) * 2.0   # start big, shrink to fit
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        n = affinity.translate(affinity.scale(n, sc, sc, origin=((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)), cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)
        l = affinity.translate(affinity.scale(l, sc, sc, origin=((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)), cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)
        keep_out = unary_union(list(deco.values())).buffer(1.2).union(Point(0, 0).buffer(D / 2 - EDGE).exterior.buffer(0.01).convex_hull.symmetric_difference(Point(0, 0).buffer(D / 2 - EDGE)))
        while unary_union([n, l]).intersects(keep_out):
            c = unary_union([n, l]).centroid
            n = affinity.scale(n, 0.98, 0.98, origin=c); l = affinity.scale(l, 0.98, 0.98, origin=c)
        print(f"owner's text box {box[2] - box[0]:.0f} x {box[3] - box[1]:.0f} mm at ({cx:.1f}, {cy:.1f})")
    txt = unary_union([n, l])
    for k, g in (("name", n), ("line", l)):
        thin = g.difference(g.buffer(-0.35).buffer(0.35))
        print(f"{k}: {g.bounds[2] - g.bounds[0]:.1f} x {g.bounds[3] - g.bounds[1]:.1f} mm, under 0.7 mm {thin.area:.2f} mm2")
    if deco:
        geo = {"black": unary_union([txt, deco["black"]]), "olive": deco["olive"], "brown": deco["brown"], "accent": deco["accent"]}
        taken = None
        for k in ("black", "accent", "olive", "brown"):          # no two colours on the same spot
            if taken is not None:
                geo[k] = geo[k].difference(taken)
            taken = geo[k] if taken is None else taken.union(geo[k])
        inks = [(k, coaster.extrude(geo[k].buffer(0), Z0, Z1), i) for i, k in enumerate(("black", "olive", "brown", "accent"), start=2)]
        for k, m, _ in inks:
            if not m.is_watertight:
                m.merge_vertices(); m.update_faces(m.nondegenerate_faces()); m.fix_normals()
            print(f"  ink {k}: watertight={m.is_watertight} volume={m.volume:.0f}")
        colours = ["#E8F1F5", "#141414", "#8F8B3A", "#B4703A", "#B9A3D6"]
    else:
        inks = [("text", coaster.extrude(txt, Z0, Z1), 2)]
        colours = ["#E8F1F5", a.colour, "#C8102E", "#E07A1F"]
    allink = trimesh.boolean.union([m for _, m, _ in inks], engine="manifold") if len(inks) > 1 else inks[0][1]   # merged: touching colours left open edges
    tpu = trimesh.boolean.difference([rounded_disc(), allink], engine="manifold")
    parts = [("clear_tpu", tpu, 1)] + inks
    parts = [(nm, coaster.mirror_x(m), s) for nm, m, s in parts]       # front on the plate: mirror so it reads right
    for nm, m, _ in parts:
        print(f"  part {nm}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    if len(colours) > 4:
        from threemf import widen_filaments
        cfg = widen_filaments(cfg, len(colours), (HERE.parent / "config" / "bambu_project_settings.config").read_bytes())
    cfg["filament_colour"] = colours
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2"] + ["1"] * (len(colours) - 1)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for nm, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{nm}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
