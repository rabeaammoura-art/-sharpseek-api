"""Flat GPT coaster picture (tan plate, black text, olive leaves, brown stems, one accent colour) -> 3MF like Mizna v3.
95 x 3 mm, face down, 1 mm coloured face layer, body = pocketed 3 mm plate.  Pictures stay OUT of git.
  python cad/mizna2/from_picture.py PICTURE.png OUTNAME [pink|lavender|cream|none]   -> cad/out/names/OUTNAME.3mf (+ preview png)
Slots: 1 body tan (external spool, nozzle 2) | 2 black | 3 olive | 4 brown/copper | 5 accent (nozzle 1 = AMS)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "coaster")); sys.path.insert(0, str(HERE.parent))
import coaster as C  # noqa: E402
from threemf import write_bambu_3mf  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

PAL = {"plate": (200, 164, 120), "black": (22, 22, 22), "olive": (140, 140, 58), "brown": (178, 108, 52)}
ACC = {"pink": ((244, 163, 152), "#F2A6A0"), "lavender": ((170, 145, 205), "#B9A3D6"), "cream": ((255, 243, 224), "#FFF3E0")}
HEX = {"plate": "#C8A578", "black": "#141414", "olive": "#8F8B3A", "brown": "#B4703A"}
FACE, T, MINW = 1.0, 3.0, 0.7


def main(pic, name, accent):
    img = np.array(Image.open(pic).convert("RGB"))
    nonwhite = (img.min(2) < 245)
    ys, xs = np.nonzero(nonwhite)
    cx, cy, rpx = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min()) / 2
    yy, xx = np.mgrid[:img.shape[0], :img.shape[1]]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 < (rpx * 0.985) ** 2
    pal = dict(PAL)
    if accent != "none":
        pal["accent"] = ACC[accent][0]
    keys = list(pal)
    d = np.stack([((img.astype(float) - np.array(pal[k])) ** 2).sum(2) for k in keys])
    lab = np.array(keys)[d.argmin(0)]
    lab[~inside] = "outside"
    black = lab == "black"
    near_black = binary_dilation(black, iterations=2)
    layers = {}
    for k in keys[1:]:
        m = (lab == k) & (~near_black if k != "black" else True)
        layers[k] = C.mask_to_mm(m, cx, cy, rpx, up=3, smooth=2.0, clean=False)
    # clean-up: black thickened a bit (thin outlines / strokes), small bits dropped, no overlaps (black > accent > olive > brown)
    layers["black"] = layers["black"].buffer(0.15).buffer(-0.05).simplify(0.02)
    order = ["black"] + (["accent"] if "accent" in layers else []) + ["olive", "brown"]
    done = None
    for k in order:
        g = layers[k]
        if done is not None:
            g = g.difference(done)
        if k != "black":
            h = MINW / 2 - 0.1
            g = g.buffer(-h).buffer(h)
            g = unary_union([p for p in getattr(g, "geoms", [g]) if p.area > 0.8])
        layers[k] = g.simplify(0.02)
        done = layers[k] if done is None else unary_union([done, layers[k]])
    hexes = dict(HEX)
    if "accent" in layers:
        hexes["accent"] = ACC[accent][1]
    # 3D
    disc = Point(0, 0).buffer(C.D / 2, 128)
    body = disc.difference(unary_union([layers[k] for k in order]))
    meshes = {"plate": C.trimesh.boolean.union([C.extrude(body, 0, FACE), C.extrude(disc, FACE, T)], engine="manifold")}
    for k in order:
        meshes[k] = C.extrude(layers[k], 0, FACE)
    seq = ["plate"] + order
    parts = [(k, C.mirror_x(meshes[k]), i + 1) for i, k in enumerate(seq)]
    N = len(parts)
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = [hexes[k] for k in seq]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2"] + ["1"] * (N - 1)
    cfg["filament_type"] = ["PLA"] * N
    if N > 4:
        for k, v in list(cfg.items()):
            if isinstance(v, list) and len(v) == 4 and k.startswith(("filament", "nozzle_temp", "hot_plate", "cool_plate", "textured", "eng_plate", "supertack", "fan", "close_fan", "overhang_fan", "slow_down", "required_nozzle", "reduce_fan", "full_fan", "additional_", "activate_air", "temperature", "pre_start", "no_slow", "override_process", "impact", "volumetric", "long_retr", "retraction_dist", "chamber_temp", "during_print", "complete_print", "cooling_", "counter_", "hole_", "diameter_limit", "circle_comp")) and k not in ("filament_colour", "filament_map", "filament_type"):
                v.extend([v[-1]] * (N - 4))
    if "filament_self_index" in cfg:
        cfg["filament_self_index"] = [str(i) for i in range(1, N + 1)]
    out = HERE.parent / "out" / "names"
    out.mkdir(parents=True, exist_ok=True)
    f3 = out / f"{name}.3mf"
    write_bambu_3mf(f3, parts, (175.0, 160.0), name, json.dumps(cfg, indent=4))
    for n, m, _ in parts:
        m.export(out / f"{name}_{n}.stl")
        print(f"  {n}: watertight {m.is_watertight}  z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    # preview
    S, R = 10, C.D / 2
    Nn = int(2 * R * S) + 40
    im = Image.new("RGB", (Nn, Nn), "#fff"); dr = ImageDraw.Draw(im); c = Nn / 2
    dr.ellipse([c - R * S, c - R * S, c + R * S, c + R * S], fill=hexes["plate"])
    for k in reversed(order):
        m = Image.new("L", im.size, 0); md = ImageDraw.Draw(m)
        for p in getattr(layers[k], "geoms", [layers[k]]):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            md.polygon([(c + x * S, c - y * S) for x, y in p.exterior.coords], fill=255)
            for h in p.interiors:
                md.polygon([(c + x * S, c - y * S) for x, y in h.coords], fill=0)
        im.paste(hexes[k], mask=m)
    im.save(out / f"{name}_preview.png")
    print("->", f3)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "none")
