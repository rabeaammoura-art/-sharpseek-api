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
            layers[z["src"]] = shapely.set_precision(layers[z["src"]].buffer(0).difference(moved), 0.002)
            layers[z["dst"]] = shapely.set_precision(unary_union([layers[z["dst"]].buffer(0), moved]) if z["dst"] in layers else moved, 0.002)
        for src, dst in th.get("remap", {}).items():          # fewer-colour variants merge colours
            if src in layers:
                layers[dst] = unary_union([layers[dst], layers[src]]) if dst in layers else layers[src]
                del layers[src]
        out[name] = dict(width=m["width_mm"], height=m["height_mm"], tab_x=m["tab_x_mm"], layers=layers)
    return out
