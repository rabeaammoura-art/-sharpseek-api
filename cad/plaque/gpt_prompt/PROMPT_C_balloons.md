# Newborn plaque — improvement round "C" (balloons + soft colourways) — GPT image prompt

Goal: keep our plaque (cloud name banner, 4 info badges, sleeping bear) but give it the richer, softer look of the best
sellers on Etsy (hot-air balloons, small clouds, stars, soft colours) and get 3 colourways. We only use GPT's picture for
SHAPES and POSITIONS: names / numbers are re-typeset later with the real fonts (GPT letters are often wrong).

Attach in this order, in the same message:
1. `example_ar_glowcap_preview.png` — the current plaque (layout + style to keep; yours to edit)
2. `3_shapes_sheet.png` — exact shapes of the 4 icons, bear, moon, stars, heart (keep them exactly)

Fill `{COLOURWAY}` with one block from the table, send once per colourway.

| colourway | frame / text / icons | accent (moon, stars, balloons stripes) | bear |
|---|---|---|---|
| dusty blue | #6F8FB3 | #F0C446 | #C8A078 |
| sage green | #7FA08A | #E8B24A | #C8A078 |
| soft pink | #D98C9A | #F4C95D | #C8A078 |

(background / cream is always #F5ECD7)

## Prompt

```
Create ONE flat, perfectly front-on design illustration of a square newborn keepsake plaque.
Canvas 1:1 (2048x2048), plain light-grey background, the plaque fills about 92% of the canvas.
No perspective, no shadow, no 3D render, no mockup, no table, no hands.

I attached 2 images:
- Image 1 is our CURRENT plaque. KEEP its structure exactly: rounded-square frame, sleeping bear on top of a cloud-shaped
  name banner, 2x2 grid of info badges (weight, length, time, date) with the same 4 icons, empty rounded box at the bottom
  with a small heart. Do not move the badges or the name banner.
- Image 2 is the exact SHAPE sheet for the icons, bear, moon, stars, heart: redraw them exactly like that.

CHANGES (only these):
1. SKY BAND (the area above the name cloud, left and right of the bear): replace the single crescent moon + few stars by a
   soft nursery scene: 2 hot-air balloons on the left (one big, one small, different heights) and 1 big balloon on the
   right; each balloon = round body with 3 vertical stripes in two colours + a small basket + 2 straight thick ropes;
   2 small round clouds near the balloons; 4-5 chunky 5-point stars of different sizes; keep ONE crescent moon, small.
   Everything stays inside the frame and does NOT touch the bear, the name cloud or the badges (leave a clear gap).
2. DATE BADGE: make the date badge a pill shape (fully rounded ends) with a tiny heart on each side of the date.
3. COLOURS (EXACTLY 4 flat colours, no gradients, no shading, no texture, no glow):
   cream #F5ECD7 (background of the plaque and inside badges), {COLOURWAY: frame / text / icons colour},
   {COLOURWAY: accent colour} (moon, stars, balloon stripes, heart), tan #C8A078 (bear).
   Balloon stripes alternate between the accent colour and the frame colour. No white, no black, no grey.

PRINTING RULES (this artwork becomes a 3D-printed plaque 280 mm wide):
- Thick bold shapes only: every line / rope / gap at least 1.2% of the plaque width. No hairlines, no tiny dots,
  no small details, no outlines thinner than the current ones.
- Keep it simple and clean. Do not add any other decoration.

TEXT: keep the placeholder text readable; the name is  {NAME}  (bold rounded Kufi-style Arabic, dark colour of the frame).
The numbers are  ٣٫٤ كغم  /  ٥٠ سم  /  ٠٤:٣٥ ص  /  ١٢/٠٣/٢٠٢٦.  (The text will be re-typeset later, so shape and position matter most.)
```

## How we use the result

1. Send the picture to Claude Code (cloud/laptop session): "make the flat preview from this picture" -> `3d-picture-to-cad`
   flat 2D preview first (measure, clean parametric shapes, real-font text), overlaid on the picture, for the owner's marks.
2. Only after the owner says yes: 3D (`cad/newborn_plaque.py` layout), `/3d-print-test`, `/3d-cost`.
3. Things to check on GPT's picture: more than 4 colours, thin lines (< 1.2 % width), balloons touching the bear or the
   cloud, wrong shapes of icons, wrong Arabic letters (ignore, we retype).
