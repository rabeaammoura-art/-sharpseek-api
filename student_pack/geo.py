"""JSON <-> shapely helpers for motif files."""
import json
from pathlib import Path
import shapely
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).parent


def load_motifs(theme):
    from themes import THEMES
    th = THEMES[theme]
    data = json.loads((HERE / "motifs" / f"{th.get('variant_of', theme)}.json").read_text())
    out = {}
    for name, m in data.items():
        layers = {c: unary_union([Polygon(p["ext"], p["holes"]).buffer(0) for p in polys]) for c, polys in m["layers"].items()}
        for z in th.get("recolour_near", []):               # re-colour only the `src` strips within `dist` mm of an `near` shape inside a zone
            if z["motif"] != name or z["src"] not in layers or z["near"] not in layers:
                continue
            zone = box(*z["box"])
            near = layers[z["near"]].intersection(zone).buffer(z["dist"])
            moved = shapely.set_precision(layers[z["src"]].buffer(0).intersection(near.buffer(0)).intersection(zone), 0.002)
            if moved.is_empty:
                continue
            if z.get("grow"):                                # thin strokes (< 0.8 mm) would be dropped by the min-feature clean-up: thicken them
                moved = shapely.set_precision(moved.buffer(z["grow"], join_style=1).intersection(zone), 0.002)
            if z.get("smooth"):                              # even out the traced edge: close small dents, drop thin spurs and tiny stray pieces
                s_ = z["smooth"]
                moved = moved.buffer(s_, join_style=1).buffer(-s_ * 1.8, join_style=1).buffer(s_ * 0.8, join_style=1).intersection(zone)
                parts = [p for p in (moved.geoms if hasattr(moved, "geoms") else [moved]) if p.geom_type == "Polygon" and p.area >= z.get("min_area", 1.0)]
                moved = shapely.set_precision(unary_union(parts), 0.002) if parts else Polygon()
            for c in list(layers):
                if c != z["dst"]:
                    layers[c] = shapely.set_precision(layers[c].buffer(0).difference(moved), 0.002)
            layers[z["dst"]] = shapely.set_precision(unary_union([layers[z["dst"]].buffer(0), moved]) if z["dst"] in layers else moved, 0.002)
        io = th.get("ink_only")
        if io:                                              # light backing: keep the dark ink only where it is an outline / line of the artwork; the rest (the dark backing blob) becomes the light base colour
            ink = io["ink"]; base = io["base"]
            if ink in layers:
                others = unary_union([layers[c].buffer(0) for c in layers if c != ink and c != base])
                black = layers[ink].buffer(0)
                keep = black.intersection(others.buffer(io.get("reach", 1.1), join_style=1))
                keep = keep.buffer(0.3, join_style=1).buffer(-0.3, join_style=1)
                keep = unary_union([p for p in (keep.geoms if hasattr(keep, "geoms") else [keep]) if p.area >= io.get("min_area", 2.0)])
                blob = black.difference(keep)
                lt = layers[base].buffer(0) if base in layers else Polygon()
                rw = io.get("ring", 0.9)
                ring = lt.buffer(rw, join_style=1).difference(lt).intersection(blob.buffer(0.01))
                layers[ink] = shapely.set_precision(unary_union([keep, ring]), 0.002)
                layers[base] = shapely.set_precision(unary_union([lt, blob]).difference(ring), 0.002)
        for z in th.get("webs", []):                         # small spider webs drawn in code (white lines on the black backing)
            if z["motif"] != name:
                continue
            import math
            from shapely.geometry import LineString, Point as _P
            for cx, cy, r in z["at"]:
                w = z.get("w", 0.4)
                parts = []
                for i in range(7):
                    a = math.radians(i * 360 / 7 + z.get("rot", 15))
                    parts.append(LineString([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a))]).buffer(w, cap_style=1))
                for f in (0.45, 0.78):
                    pts = []
                    for i in range(7):                         # scalloped ring: straight chords sagging inwards between the spokes
                        a0 = math.radians(i * 360 / 7 + z.get("rot", 15)); a1 = math.radians((i + 1) * 360 / 7 + z.get("rot", 15)); am = (a0 + a1) / 2
                        pts += [(cx + f * r * math.cos(a0), cy + f * r * math.sin(a0)), (cx + 0.86 * f * r * math.cos(am), cy + 0.86 * f * r * math.sin(am))]
                    pts.append(pts[0])
                    parts.append(LineString(pts).buffer(w, cap_style=1, join_style=1))
                web = unary_union(parts)
                for c in list(layers):
                    layers[c] = shapely.set_precision(layers[c].buffer(0).difference(web), 0.002)
                layers[z["colour"]] = shapely.set_precision(unary_union([layers[z["colour"]].buffer(0), web]) if z["colour"] in layers else web, 0.002)
        for z in th.get("flag_rings", []):                    # smooth border drawn in code: [art] [gap of backing] [ring of `colour`] around everything inside the zone
            if z["motif"] != name:
                continue
            zone = box(*z["box"])
            parts = []
            for c in layers:
                for p in (layers[c].buffer(0).geoms if hasattr(layers[c].buffer(0), "geoms") else [layers[c].buffer(0)]):
                    if p.is_empty:
                        continue
                    if z.get("black") == c:                    # the dark stripe shares its colour with the backing: take only what lies inside the zone
                        parts.append(p.intersection(zone))
                    elif zone.contains(p.centroid) and p.area < z.get("max_area", 400):
                        parts.append(p)
            body = unary_union([p for p in parts if not p.is_empty]).buffer(1.2, join_style=1).buffer(-1.2, join_style=1)
            inner = body.buffer(z["gap"], join_style=1)
            ring = body.buffer(z["gap"] + z["width"], join_style=1).difference(inner)
            ring = ring.buffer(-0.25, join_style=1).buffer(0.25, join_style=1)
            for c in list(layers):
                layers[c] = shapely.set_precision(layers[c].buffer(0).difference(ring), 0.002)
            layers[z["colour"]] = shapely.set_precision(unary_union([layers[z["colour"]].buffer(0), ring]) if z["colour"] in layers else ring, 0.002)
        for src, dst in th.get("remap", {}).items():          # fewer-colour variants merge colours
            if src in layers:
                layers[dst] = unary_union([layers[dst], layers[src]]) if dst in layers else layers[src]
                del layers[src]
        for z in th.get("fill_gaps", []):                    # close narrow gaps between the colours inside a zone (they would print as base-colour slivers)
            if z["motif"] != name:
                continue
            zone = box(*z["box"]); r = z["radius"]
            cols_ = [c for c in z["priority"] if c in layers]
            allg = unary_union([layers[c].buffer(0) for c in layers])
            gap = allg.buffer(r, join_style=1).buffer(-r, join_style=1).difference(allg).intersection(zone)
            if gap.is_empty:
                continue
            for c in cols_:
                take = gap.intersection(layers[c].buffer(0).buffer(r * 1.6, join_style=1))
                if take.is_empty:
                    continue
                layers[c] = shapely.set_precision(unary_union([layers[c].buffer(0), take]), 0.002)
                gap = gap.difference(take)
        for z in th.get("thicken", []):                     # thicken thin strokes of one colour inside a zone (lines under the 0.8 mm print limit)
            if z["motif"] != name or z["colour"] not in layers:
                continue
            zone = box(*z["box"]); lay = layers[z["colour"]].buffer(0)
            add = shapely.set_precision(lay.buffer(z["amount"], join_style=1).intersection(zone).difference(lay), 0.002)
            if add.is_empty:
                continue
            layers[z["colour"]] = shapely.set_precision(unary_union([lay, add]), 0.002)
            for c in list(layers):
                if c != z["colour"]:
                    layers[c] = shapely.set_precision(layers[c].buffer(0).difference(add), 0.002)
        for f in th.get("fill_specks", []):                  # tiny holes of `colour` inside a zone take that colour (yellow specks inside the mouth, between outlines ...)
            if f["motif"] != name or f["colour"] not in layers:
                continue
            zone, lay, filled = box(*f["box"]), layers[f["colour"]].buffer(0), []
            polys = []
            for p in (lay.geoms if hasattr(lay, "geoms") else [lay]):
                keep = [r for r in p.interiors if not (Polygon(r).area < f["max_area"] and Polygon(r).representative_point().within(zone))]
                filled += [Polygon(r) for r in p.interiors if Polygon(r).area < f["max_area"] and Polygon(r).representative_point().within(zone)]
                polys.append(Polygon(p.exterior, keep))
            if filled:
                fill = shapely.set_precision(unary_union(filled), 0.002)
                layers[f["colour"]] = shapely.set_precision(unary_union(polys), 0.002)
                for c in list(layers):
                    if c != f["colour"]:
                        layers[c] = shapely.set_precision(layers[c].buffer(0).difference(fill), 0.002)
        out[name] = dict(width=m["width_mm"], height=m["height_mm"], tab_x=m["tab_x_mm"], layers=layers)
    return out
