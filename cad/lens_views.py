"""All-round render sheet of the W115 lens (RH, plus LH front). Usage: python lens_views.py"""
from PIL import Image, ImageDraw, ImageFont

import lens_render as L

VIEWS = [  # (label, elev, azim)
    ("Front – from behind the car", 0, -90),
    ("Front 3/4 – inboard side", 20, -130),
    ("Front 3/4 – outboard (amber) side", 20, -50),
    ("Inside (back) – straight", 0, 90),
    ("Inside 3/4 – from above", 45, 55),
    ("Inside 3/4 – amber side", 30, 130),
    ("Top (plan) – shows the wrap", 89.9, -90),
    ("Bottom", -89.9, -90),
    ("Inboard end – rib profile", 0, 180),
    ("Outboard end (amber)", 0, 0),
    ("Front 3/4 – from below", -25, -115),
    ("Car-side view (amber from the side)", 5, -15),
]


def main():
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    W, H, cols = 760, 520, 3
    tiles = []
    t, c = L.load("RH")
    for label, e, a in VIEWS:
        tiles.append((f"RH · {label}", L.render(t, c, e, a, size=(W, H - 40))))
    t, c = L.load("LH")
    tiles.append(("LH · Front – from behind the car", L.render(t, c, 0, -90, size=(W, H - 40))))
    tiles.append(("LH · Front 3/4", L.render(t, c, 20, -50, size=(W, H - 40))))
    tiles.append(("LH · Inside 3/4", L.render(t, c, 40, 125, size=(W, H - 40))))
    rows = -(-len(tiles) // cols)
    sheet = Image.new("RGB", (W * cols, H * rows), "white")
    dr = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(tiles):
        x, y = (i % cols) * W, (i // cols) * H
        sheet.paste(im, (x, y + 40))
        dr.text((x + 14, y + 8), label, fill="black", font=font)
        dr.rectangle([x, y, x + W - 1, y + H - 1], outline=(220, 220, 220))
    out = L.OUT / "all_views.png"
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
