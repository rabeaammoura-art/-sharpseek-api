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
        for src, dst in th.get("remap", {}).items():          # fewer-colour variants merge colours
            if src in layers:
                layers[dst] = unary_union([layers[dst], layers[src]]) if dst in layers else layers[src]
                del layers[src]
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
