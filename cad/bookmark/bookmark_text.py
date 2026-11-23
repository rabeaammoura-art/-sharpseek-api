"""Clear TPU bookmark with a text readable from BOTH sides (owner 2026-11-23) -> Bambu Studio 3MF.

    python cad/bookmark/bookmark_text.py --text "واهدنا سبل السلام" --font FONT.ttf --hearts-pic COASTER_PICTURE.png --out OUT.3mf

45 x 160 x 2.0 mm, tassel hole, rounded edges. Layers (z up = front):
  TPU 0.4 | back text (mirrored, so it reads right from the back) 0.4 | red card 0.4 | front text 0.4 | TPU 0.4
The red card = rim around front + back text (1.2 mm) and hides each text from the other side. Hearts (same red) 0.4-1.6.
Printed face down (front on the smooth plate). Slots: 1 clear TPU (nozzle 2), 2 red, 3 text colour (nozzle 1).
Fonts and pictures are passed as arguments and stay out of git (licences unknown).
"""
import argparse, json, random, sys
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "coaster"))
import coaster                       # noqa: E402  (extrude, heart tracing helpers)
import newborn_plaque as npq         # noqa: E402  (HarfBuzz Arabic shaping)
from threemf import write_bambu_3mf  # noqa: E402

W, H, RC = 45.0, 160.0, 6.0
HOLE_Y, HOLE_R = 72.0, 2.5
Z = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0]
ROUND = 0.6
RIM = 1.2


def text_shapes(texts, font):
    """each text along the strip, centred; all scaled by ONE factor (same letter size on both faces)"""
    ts = []
    for text in texts:
        t = npq.shape_run(npq.Font(font), text, 20.0, "rtl", "Arab")[0]
        b = t.bounds
        ts.append(affinity.rotate(affinity.translate(t, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2), 90, origin=(0, 0)))
    s = min(min(104 / (t.bounds[3] - t.bounds[1]), 26 / (t.bounds[2] - t.bounds[0])) for t in ts)
    return [affinity.scale(t, s, s, origin=(0, 0)).buffer(0.2, 16) for t in ts]   # thin strokes -> ~1 mm and more


def heart_shape(pic):
    img = np.array(Image.open(pic).convert("RGB")).astype(float)[:, : Image.open(pic).size[0] // 2]
    cx, cy, r = coaster.find_circle(img)
    ys, xs = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    red = coaster.mask_to_mm(coaster.colour_masks(img)["red"] & ((xs - cx) ** 2 + (ys - cy) ** 2 < (r - 12) ** 2), cx, cy, r)
    h = min(red.geoms, key=lambda g: g.distance(Point(-15, 33)))
    c = h.centroid; h = affinity.translate(h, -c.x, -c.y); hb = h.bounds
    return affinity.scale(h, 1 / (hb[2] - hb[0]), 1 / (hb[2] - hb[0]), origin=(0, 0))


def rounded_body(outline):
    n = int(round(Z[-1] / 0.1)); slabs = []
    for i in range(n):
        za, zb = i * Z[-1] / n, (i + 1) * Z[-1] / n; zm = (za + zb) / 2
        d = max(0.0, ROUND - zm, zm - (Z[-1] - ROUND))
        inset = ROUND - np.sqrt(max(ROUND ** 2 - d ** 2, 0.0))
        slabs.append(coaster.extrude(outline.buffer(-inset, 32), za - (0.005 if i else 0), zb + (0.005 if i < n - 1 else 0)))
    return trimesh.boolean.union(slabs, engine="manifold")


def build(text, font, pic, text_back=None):
    body = box(-W / 2 + RC, -H / 2 + RC, W / 2 - RC, H / 2 - RC).buffer(RC, 32).difference(Point(0, HOLE_Y).buffer(HOLE_R, 32))
    inner = body.buffer(-2.6).difference(Point(0, HOLE_Y).buffer(HOLE_R + 4))
    front, back_read = text_shapes([text, text_back or text], font)
    back = affinity.scale(back_read, -1, 1, origin=(0, 0))      # mirrored so it reads right from the back
    card = unary_union([front, back]).buffer(RIM, 16)
    heart = heart_shape(pic)
    rnd = random.Random(3); hearts = []; free = prep(inner.difference(card.buffer(1.8))); occ = card
    for i, y0 in enumerate([64, 46, 28, 10, -8, -26, -44, -62]):
        sz = [5.6, 4.6, 5.2][i % 3]
        for _ in range(400):
            x = (16.6 if i % 2 else -16.6) + rnd.uniform(-0.6, 0.6); y = y0 + rnd.uniform(-2, 2)
            q = affinity.translate(affinity.rotate(affinity.scale(heart, sz, sz, origin=(0, 0)), rnd.uniform(-20, 20), origin=(0, 0)), x, y)
            if free.contains(q) and not occ.intersects(q.buffer(1.8)):
                hearts.append(q); occ = occ.union(q); break
    red = trimesh.boolean.union([coaster.extrude(card, Z[2], Z[3]), coaster.extrude(unary_union(hearts), Z[1], Z[4])], engine="manifold")
    ink = trimesh.util.concatenate([coaster.extrude(back, Z[1], Z[2]), coaster.extrude(front, Z[3], Z[4])])
    tpu = trimesh.boolean.difference([rounded_body(body), red, ink], engine="manifold")
    print(f"front text {front.bounds[3] - front.bounds[1]:.0f} mm, back text {back.bounds[3] - back.bounds[1]:.0f} mm long, card {card.bounds[2] - card.bounds[0]:.1f} mm wide, hearts {len(hearts)}")
    return [("clear_tpu", tpu, 1), ("red", red, 2), ("text", ink, 3)]


def face_down(m):
    m = m.copy()
    m.apply_transform(np.diag([-1.0, 1.0, -1.0, 1.0]))     # turn over around the long axis (a rotation, not a mirror)
    m.apply_translation((0, 0, Z[-1]))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True); ap.add_argument("--text-back", help="another text on the back (default: the same)"); ap.add_argument("--font", required=True); ap.add_argument("--hearts-pic", required=True)
    ap.add_argument("--text-colour", default="#1F5FA8"); ap.add_argument("--red", default="#C8102E")
    ap.add_argument("--out", required=True); ap.add_argument("--stl", action="store_true")
    a = ap.parse_args()
    parts = [(n, face_down(m), sl) for n, m, sl in build(a.text, a.font, a.hearts_pic, a.text_back)]
    for n, m, _ in parts:
        print(f"  part {n}: watertight={m.is_watertight} volume={m.volume:.0f} z {m.bounds[0][2]:.2f}-{m.bounds[1][2]:.2f}")
    cfg = json.loads((HERE.parent / "config" / "bambu_project_4fil_petg.config").read_text())
    cfg["filament_colour"] = ["#E8F1F5", a.red, a.text_colour, "#E07A1F"]
    cfg["filament_map_mode"], cfg["filament_map"] = "Manual", ["2", "1", "1", "1"]
    cfg["filament_type"] = ["TPU", "PLA", "PLA", "PLA"]
    cfg["sparse_infill_density"], cfg["sparse_infill_pattern"] = "100%", "zig-zag"
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    write_bambu_3mf(out, parts, (175.0, 160.0), out.stem, json.dumps(cfg, indent=4))
    if a.stl:
        for n, m, _ in parts:
            m.export(out.with_name(f"{out.stem}_{n}.stl"))
    print("->", out)


if __name__ == "__main__":
    main()
