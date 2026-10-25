"""JSON <-> shapely helpers for motif files."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = Path(__file__).parent


def load_motifs(theme):
    data = json.loads((HERE / "motifs" / f"{theme}.json").read_text())
    out = {}
    for name, m in data.items():
        layers = {c: unary_union([Polygon(p["ext"], p["holes"]).buffer(0) for p in polys]) for c, polys in m["layers"].items()}
        out[name] = dict(width=m["width_mm"], height=m["height_mm"], tab_x=m["tab_x_mm"], layers=layers)
    return out
