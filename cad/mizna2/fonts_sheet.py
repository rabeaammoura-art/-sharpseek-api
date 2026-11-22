"""Contact sheet: the Mizna text in several Arabic fonts on the traced coaster art (flat 2D, no 3D)."""
import pickle, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from shapely import affinity
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import newborn_plaque as npq
import importlib.util
_s = importlib.util.spec_from_file_location("mz_trace", HERE / "trace.py"); T = importlib.util.module_from_spec(_s); _s.loader.exec_module(T)
L = pickle.load(open(HERE.parent / "out" / "mizna2" / "layers.pkl", "rb"))
orig = [p for p in L["brown"].geoms]
text = [p for p in orig if -14 < p.centroid.y < 24.5 and abs(p.centroid.x) < 36]
rest = [p for p in orig if p not in text]
tb = unary_union(text).bounds
tit = unary_union([p for p in text if p.centroid.y > 0.5]).bounds
sub = unary_union([p for p in text if p.centroid.y <= 0.5]).bounds
print("title bbox", [round(v, 1) for v in tit], "sub bbox", [round(v, 1) for v in sub])
F = Path("/usr/share/fonts/truetype/noto"); M = HERE.parent / "fonts"
CANDS = [("Noto Naskh", F / "NotoNaskhArabic-Bold.ttf", F / "NotoNaskhArabic-Regular.ttf"),
         ("Noto Kufi", M / "NotoKufiArabic-Bold.ttf", M / "NotoKufiArabic-Regular.ttf"),
         ("Baloo Bhaijaan", M / "BalooBhaijaan2-ExtraBold.ttf", M / "NotoKufiArabic-Regular.ttf"),
         ("Noto Sans Arabic", F / "NotoSansArabic-Bold.ttf", F / "NotoSansArabic-Regular.ttf"),
         ("Noto Nastaliq", F / "NotoNastaliqUrdu-Bold.ttf", F / "NotoNastaliqUrdu-Regular.ttf")]


def fit(txt, path, box):
    f = npq.Font(path)
    g, _ = npq.shape_run(f, txt, 100, "rtl", "Arab")
    x0, y0, x1, y1 = box
    a, b, c, d = g.bounds
    s = min((x1 - x0) / (c - a), (y1 - y0) / (d - b))
    g = affinity.scale(g, s, s, origin=(0, 0))
    a, b, c, d = g.bounds
    return affinity.translate(g, (x0 + x1) / 2 - (a + c) / 2, (y0 + y1) / 2 - (b + d) / 2)


tiles = []
for name, bold, reg in CANDS:
    Lx = dict(L)
    Lx["brown"] = unary_union(rest + [fit("مزنة", bold, tit), fit("رِقَّةً كالمطر", reg, sub)])
    tiles.append((name, T.render(Lx, HERE.parent / "out" / "mizna2" / "tmp.png", S=6)))
orig_im = T.render(L, HERE.parent / "out" / "mizna2" / "tmp.png", S=6)
tiles.insert(0, ("GPT (the picture)", orig_im))
w = tiles[0][1].width
sheet = Image.new("RGB", (w * 3, (w + 40) * 2), "#fff")
d = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(tiles):
    x, y = (i % 3) * w, (i // 3) * (w + 40)
    sheet.paste(im, (x, y + 40))
    d.text((x + 20, y + 10), f"{i}: {n}", fill="#000", font=ImageFont.load_default(size=22))
sheet.save(HERE.parent / "out" / "mizna2" / "fonts_sheet.png")
