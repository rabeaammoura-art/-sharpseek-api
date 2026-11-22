"""Mizna v2: trace the owner's flat GPT picture (colour version) into 4 clean colour layers (mm), flat preview first.
Picture stays out of git.  python cad/mizna2/trace.py COLOUR.png  -> cad/out/mizna2/layers.pkl + flat2.png + overlay2.png"""
import pickle, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "coaster"))
sys.path.insert(0, str(HERE.parent))
import coaster as C  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

PAL = {"bg": (255, 255, 255), "body": (244, 220, 200), "brown": (91, 58, 34), "lilac": (210, 169, 214), "olive": (169, 140, 82)}
HEX = {"body": "#F4DCC8", "brown": "#5B3A22", "lilac": "#D2A9D6", "olive": "#A98C52"}
MINW = 0.7


def classify(img):
    a = img.astype(float)
    keys = list(PAL)
    d = np.stack([((a - np.array(PAL[k])) ** 2).sum(2) for k in keys])
    return np.array(keys)[d.argmin(0)]


def build(path):
    img = np.array(Image.open(path).convert("RGB"))
    lab = classify(img)
    plate = lab != "bg"
    ys, xs = np.nonzero(plate)
    # plate = biggest blob: use rows/cols with plate pixels
    cx, cy, rpx = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2, (xs.max() - xs.min()) / 2
    print("circle px", cx, cy, rpx)
    out = {}
    for k in ("brown", "lilac", "olive"):
        g = C.mask_to_mm(lab == k, cx, cy, rpx, up=3, smooth=2.4, clean=False)
        out[k] = g
    # thin parts (stems, marks): thicken so every feature >= MINW
    out["brown"] = out["brown"].buffer(0.14).simplify(0.02)   # stems/marks were ~0.5 mm
    # no overlap: brown wins over lilac/olive, lilac over olive
    out["lilac"] = out["lilac"].difference(out["brown"])
    out["olive"] = out["olive"].difference(out["brown"]).difference(out["lilac"])
    for k in ("lilac", "olive"):
        h = MINW / 2
        out[k] = out[k].buffer(-h).buffer(h).simplify(0.02)
    return out, (cx, cy, rpx)


def render(L, path, S=12):
    R = C.D / 2
    N = int(2 * R * S) + 40
    im = Image.new("RGB", (N, N), "#fff")
    d = ImageDraw.Draw(im)
    c = N / 2
    d.ellipse([c - R * S, c - R * S, c + R * S, c + R * S], fill=HEX["body"])
    for k in ("olive", "lilac", "brown"):
        m = Image.new("L", im.size, 0)
        md = ImageDraw.Draw(m)
        for p in getattr(L[k], "geoms", [L[k]]):
            if p.geom_type != "Polygon" or p.is_empty:
                continue
            md.polygon([(c + x * S, c - y * S) for x, y in p.exterior.coords], fill=255)
            for h in p.interiors:
                md.polygon([(c + x * S, c - y * S) for x, y in h.coords], fill=0)
        im.paste(HEX[k], mask=m)
    im.save(path)
    return im


if __name__ == "__main__":
    out = HERE.parent / "out" / "mizna2"
    out.mkdir(parents=True, exist_ok=True)
    L, (cx, cy, rpx) = build(sys.argv[1])
    pickle.dump(L, open(out / "layers.pkl", "wb"))
    im = render(L, out / "flat2.png")
    ref = Image.open(sys.argv[1]).convert("RGB").crop((int(cx - rpx), int(cy - rpx), int(cx + rpx), int(cy + rpx))).resize((im.width - 40, im.width - 40))
    base = Image.new("RGB", im.size, "#fff"); base.paste(ref, (20, 20))
    Image.blend(base, im, 0.5).save(out / "overlay2.png")
    for k, g in L.items():
        n = len(getattr(g, "geoms", [g]))
        print(k, "parts", n, "area", round(g.area, 1))
