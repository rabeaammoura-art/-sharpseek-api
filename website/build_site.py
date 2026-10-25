"""Build the website: preview images + price data from the Student Pack generator, then index.html (deployable) and artifact.html.

    python website/build_site.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "student_pack"))

from PIL import Image  # noqa: E402

import layout  # noqa: E402
import preview  # noqa: E402
import pricing  # noqa: E402
from themes import THEMES, resolve_theme  # noqa: E402

SAMPLE = {"construction": "OMAR", "cat": "LAYLA"}


def sheet(theme, name, out):
    tmp = HERE / "public" / "img" / "_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    ims = []
    for k in pricing.PIECES:
        p = layout.KINDS[k](theme, name)
        preview.piece_png(p, tmp / f"{k}.png", bg="#EEF1F7")
        ims.append(Image.open(tmp / f"{k}.png").convert("RGB"))
    tag, bottle, pencil, ruler = [ims[0], ims[3], ims[1], ims[2]]
    W = max(tag.width + bottle.width, pencil.width, ruler.width)
    top = Image.new("RGB", (W, tag.height + pencil.height + ruler.height), (238, 241, 247))
    top.paste(tag, (0, 0)); top.paste(bottle, (tag.width, 0))
    top.paste(pencil, (0, tag.height)); top.paste(ruler, (0, tag.height + pencil.height))
    top.thumbnail((1100, 1100))
    top.save(out, optimize=True)


def main():
    cat = json.loads((HERE.parent / "student_pack" / "catalog.json").read_text())
    p = pricing.load_prices()
    data = {"currency": "JOD", "premium": p["single_premium"], "step": p["round_up_to"], "themes": {}}
    labels = {"construction": ("إنشاءات", "حفّارة وقلّاب"), "cat": ("قطة", "قطة صغيرة بمخالب وردية")}
    for base in pricing.BASE_THEMES:
        entry = {"label": labels[base][0], "desc": labels[base][1], "sample": SAMPLE[base], "colours": {}}
        for c in (2, 3, 4):
            theme = resolve_theme(base, c)
            th = THEMES[theme]
            img = f"img/{base}-{c}.png"
            sheet(theme, SAMPLE[base], HERE / "public" / img)
            costs = {k: pricing.piece_cost(p, cat[pricing.key(base, c, k)]["seconds"], cat[pricing.key(base, c, k)]["grams"]) for k in pricing.PIECES}
            entry["colours"][str(c)] = {
                "pack": p["pack_price"][str(c)], "img": img, "costs": costs,
                "swatches": [{"name": n, "hex": th["filament_rgb"][n], "z": th["heights"][n]} for n in th["heights"]],
                "hours": round(sum(cat[pricing.key(base, c, k)]["seconds"] for k in pricing.PIECES) / 3600, 1)}
        data["themes"][base] = entry
    (HERE / "worker" / "pricing.json").write_text(json.dumps(data, ensure_ascii=False))     # the Worker recomputes every price from this
    page = (HERE / "site.src.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False))
    src = page.replace("__API__", "")                                  # preview build: no server
    (HERE / "artifact.html").write_text(src, encoding="utf-8")
    src = page.replace("__API__", "/api")
    full = ('<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n' + src + "\n</body>\n</html>\n")
    (HERE / "public" / "index.html").write_text(full, encoding="utf-8")
    for f in (HERE / "public" / "img" / "_tmp").glob("*"):
        f.unlink()
    (HERE / "public" / "img" / "_tmp").rmdir()
    print("built", sorted(x.name for x in (HERE / "public").rglob("*") if x.is_file()))


if __name__ == "__main__":
    main()
