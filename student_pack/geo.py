"""JSON <-> shapely helpers for motif files."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = Path(__file__).parent


def load_motifs(theme):
    from themes import THEMES
    th = THEMES[theme]
    data = json.loads((HERE / "motifs" / f"{th.get('variant_of', theme)}.json").read_text())
    out = {}
    for name, m in data.items():
        layers = {c: unary_union([Polygon(p["ext"], p["holes"]).buffer(0) for p in polys]) for c, polys in m["layers"].items()}
        for src, dst in th.get("remap", {}).items():          # fewer-colour variants merge colours
            if src in layers:
                layers[dst] = unary_union([layers[dst], layers[src]]) if dst in layers else layers[src]
                del layers[src]
        out[name] = dict(width=m["width_mm"], height=m["height_mm"], tab_x=m["tab_x_mm"], layers=layers)
    return out
