"""Clear TPU coaster from a FLAT colour picture (owner 2026-11-23: monogram R + leafy branch), face down.

    python cad/coaster/coaster_picture.py PICTURE --out OUT.3mf [--stl]

Picture: a round flat design (background circle in one colour, inks in a few flat colours). Colours are fixed below
(black letter, olive leaves/berries, brown stems). Layers like coaster_text.py: TPU 0.4 (face, on the plate) |
inlay 0.6 | TPU 2.0, rounded edges, mirrored. Thin stems are thickened to >= 0.9 mm. Picture stays out of git.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from shapely import affinity
from shapely.geometry import Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import coaster, coaster_text as ct     # noqa: E402
from threemf import write_bambu_3mf    # noqa: E402

INKS = {  # name: (rgb, tolerance, slot colour)
    "black": ((15, 15, 15), 70, "#141414"),
    "olive": ((128, 130, 55), 45, "#8F8B3A"),
    "brown": ((160, 85, 30), 45, "#B4703A"),
}
ART_D = 88.0    # the picture's background circle -> this diameter (mm); keeps the art >= 3 mm inside the Ø95 edge


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("picture"); ap.add_argument("--out", required=True); ap.add_argument("--stl", action="store_true")
    ap.add_argument("--purple", action="store_true", help="letter + berries purple instead of black / olive")
    a = ap.parse_args()
    img = np.array(Image.open(a.picture).convert("RGB")).astype(float)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    tan = (abs(r - 205) < 30) & (abs(g - 172) < 30) & (abs(b - 128) < 35)
    ys, xs = np.nonzero(tan)
    cx, cy, rpx = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min()) / 2
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 < (rpx - 6) ** 2
    scale_r = rpx * ct.D / ART_D                       # mask_to_mm maps scale_r pixels to D/2 mm
    geo = {}
    for k, (rgb, tol, _) in INKS.items():
        m = (np.sqrt(((img - np.array(rgb)) ** 2).sum(2)) < tol) & inside
        sm = 1.6 if k == "brown" else 0.8             # stems: smoother trace (owner mark 2026-11-23: rough stem)
        geo[k] = coaster.mask_to_mm(m, cx, cy, scale_r, up=4 if k == "brown" else 2, smooth=sm, clean=False)
    # thin stems / stalks (~0.65 mm in the picture): +0.44 mm all round -> ~1.1 mm
    st = geo["brown"].buffer(0.22, 16)                                                   # even thickening
    geo["brown"] = st.buffer(0.35, 16).buffer(-0.35, 16).buffer(-0.25, 16).buffer(0.25, 16).simplify(0.03)   # close + open = smooth
    if a.purple:   # owner 2026-11-23: berries and the letter in purple (berries = small round olive blobs)
        ol = list(getattr(geo["olive"], "geoms", [geo["olive"]]))
        berry = lambda q: q.area < 15.0 and 4 * np.pi * q.area / q.length ** 2 > 0.75   # berries 6-11 mm2, leaves >= 21
        geo["purple"] = unary_union([geo["black"]] + [q for q in ol if berry(q)])
        geo["olive"] = unary_union([q for q in ol if not berry(q)])
        del geo["black"]
        print(f"berries -> purple: {sum(1 for q in ol if berry(q))}")
    taken = None
    for k in [c for c in ("black", "purple", "olive", "brown") if c in geo]:   # no two colours on one spot (leaves win over stems)
        if taken is not None:
            geo[k] = geo[k].difference(taken)
        taken = geo[k] if taken is None else taken.union(geo[k])
    for k, gg in geo.items():
        t = gg.difference(gg.buffer(-0.35).buffer(0.35))
        print(f"{k}: {len(getattr(gg, 'geoms', [gg]))} pieces, {gg.area:.0f} mm2, under 0.7 mm {t.area:.2f} mm2, bounds {[round(v, 1) for v in gg.bounds]}")
    order = [c for c in ("black", "purple", "olive", "brown") if c in geo]
    inks = [(k, coaster.extrude(geo[k].buffer(0), ct.Z0, ct.Z1), i) for i, k in enumerate(order, start=2)]
    allink = trimesh.boolean.union([m for _, m, _ in inks], engine="manifold")
    tpu = trimesh.boolean.difference([ct.rounded_disc(), allink], engine="manifold")
    parts = [(n, coaster.mirror_x(m), s) for n, m, s in [("clear_tpu", tpu, 1)] + inks]
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cols = {"black": "#141414", "purple": "#7B4FA0", "olive": "#8F8B3A", "brown": "#B4703A"}
    cfg["filament_colour"] = ["#E8F1F5"] + [cols[k] for k in order]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
