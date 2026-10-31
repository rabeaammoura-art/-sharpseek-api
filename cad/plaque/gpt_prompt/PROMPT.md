# Newborn plaque — image-generation prompts (ChatGPT / GPT image)

Attach the images **in this order** in the same message as the prompt:

1. `1_layout_blueprint.png` — exact geometry (copy it)
2. `2_style_reference_arabic.png` or `2_style_reference_english.png` — exact style and colours
3. `3_shapes_sheet.png` — exact shapes of the 4 icons, the bear, moon, stars, heart
4. `4_mood_reference_ai_mockups.png` — mood only (cuteness); do **not** copy its layout

Fill the `{…}` placeholders, then paste **Prompt A** (Arabic edition) or **Prompt B** (English edition).

| placeholder | example (AR edition) | example (EN edition) |
|---|---|---|
| `{NAME}` | يوسف | YOUSEF |
| `{WEIGHT}` | ٣٫٤ كغم | 3.4 kg |
| `{LENGTH}` | ٥٠ سم | 50 cm |
| `{DATE}` | ١٢ / ٠٣ / ٢٠٢٦ | 12/03/2026 |
| `{TIME}` | ٠٤ : ٣٥ ص | 04:35 AM |

---

## Prompt A — Arabic edition (right-to-left)

```
Create ONE flat, perfectly front-on design illustration of a square newborn keepsake plaque.
Canvas 1:1 (2048x2048), plain light-grey background, the plaque fills about 92% of the canvas.
No perspective, no shadow, no 3D render, no mockup, no hands, no table, no extra decoration.

I attached 4 reference images. Follow them like this:
- Image 1 is the exact LAYOUT BLUEPRINT. Copy its geometry, proportions and positions exactly.
- Image 2 is the exact STYLE reference: flat shapes, same 4 colours, same look.
- Image 3 shows the exact SHAPES: redraw the 4 icons (baby scale, ruler, calendar, clock), the sleeping
  bear, the crescent moon, the stars and the heart exactly like that sheet.
- Image 4 is mood only (cute, soft). Do NOT copy its layout, animals or colours.

PRINTING RULES (this artwork becomes a 3D-printed plaque):
- EXACTLY 4 flat colours, no gradients, no shading, no textures, no glow, no outlines other than described:
  cream #F5ECD7 (background), dark blue #3E628A (frame, outlines, icons, text, bear eyes/nose),
  yellow #F0C446 (moon, stars, heart), tan #C8A078 (bear).
- Thick bold shapes only. No thin lines, no tiny details, no small decorative dots.

LAYOUT (percent of the plaque, origin top-left, plaque is a square with rounded corners, radius 10% of width):
1. FRAME: solid dark-blue border 4% of the width, inside the rounded edge.
2. SKY (top band, inside the frame): yellow crescent moon at left (centre 17% from left, 13% from top, radius 6%);
   4 yellow stars: (27%, 9%) small, (82%, 13%) large, (75%, 8%) small, (87%, 21%) small;
   one tiny dark-blue star at (11%, 27%).
3. BEAR: a tan sleeping teddy bear head peeking over the top edge of the cloud, centred horizontally
   (head centre 50% / 13%, diameter 13% of the width), two round ears with cream inner ears,
   cream oval muzzle, closed eyes drawn as two dark-blue arcs, dark-blue nose, two tan paws resting on the cloud.
4. NAME CLOUD: a cream cloud-shaped banner with a 0.5% dark-blue outline, spanning 17%-83% of the width and
   24%-37% from the top (5 round bumps on its top edge, the biggest one in the centre). Inside it, centred,
   the baby name in a bold rounded Arabic font (Kufi style), dark blue:  {NAME}
5. FOUR INFO BADGES in a 2x2 grid, each a rounded rectangle with a 0.5% dark-blue outline and NO fill (cream):
   each badge is 41% wide and 13% tall; right column spans 51%-93%, left column spans 7%-49%;
   top row spans 39%-52% from the top, bottom row spans 55%-68%.
   Inside each badge: the ICON at the left end (solid dark blue, height about 10%),
   and at the right a small label above a large value, both right-aligned, dark blue, bold Arabic.
   Right-to-left reading order:
     top-right    : label الوزن      value {WEIGHT}   icon: baby scale
     top-left     : label الطول      value {LENGTH}   icon: ruler
     bottom-right : label التاريخ    value {DATE}     icon: calendar
     bottom-left  : label الساعة     value {TIME}     icon: clock
6. FOOTPRINT PAD: an EMPTY rounded rectangle with a 0.5% dark-blue outline and cream inside,
   centred, spanning 29%-71% of the width and 72%-93% from the top, with one small yellow heart in its middle.
   Do not draw any footprints and do not write text in it.

TEXT RULES:
- Write ONLY the texts given above, exactly as written, correct Arabic letter joining, right-to-left.
- Use these exact digits as given (Arabic-Indic digits). Do not translate, do not add words, no watermark.
- If you cannot render an Arabic word perfectly, still place it and keep the same size and position.

Output: one clean image, nothing else.
```

---

## Prompt B — English edition (left-to-right)

```
Create ONE flat, perfectly front-on design illustration of a square newborn keepsake plaque.
Canvas 1:1 (2048x2048), plain light-grey background, the plaque fills about 92% of the canvas.
No perspective, no shadow, no 3D render, no mockup, no hands, no table, no extra decoration.

I attached 4 reference images: Image 1 = exact LAYOUT BLUEPRINT (copy geometry and positions exactly);
Image 2 = exact STYLE reference (flat shapes, same 4 colours); Image 3 = exact SHAPES to redraw (4 icons,
sleeping bear, crescent moon, stars, heart); Image 4 = mood only (do not copy its layout, animals or colours).

PRINTING RULES (this becomes a 3D-printed plaque): EXACTLY 4 flat colours, no gradients, no shading, no textures,
no glow: cream #F5ECD7 (background), dark blue #3E628A (frame, outlines, icons, text, bear eyes and nose),
yellow #F0C446 (moon, stars, heart), tan #C8A078 (bear). Thick bold shapes only, no thin lines, no tiny details.

LAYOUT (percent of the plaque, origin top-left, square with rounded corners, radius 10% of width):
1. FRAME: solid dark-blue border 4% of the width, inside the rounded edge.
2. SKY (top band inside the frame): yellow crescent moon at left (centre 17% / 13%, radius 6%);
   4 yellow stars: (27%, 9%) small, (82%, 13%) large, (75%, 8%) small, (87%, 21%) small;
   one tiny dark-blue star at (11%, 27%).
3. BEAR: tan sleeping teddy bear head peeking over the top edge of the cloud, centred horizontally
   (head centre 50% / 13%, diameter 13% of the width), round ears with cream inner ears, cream oval muzzle,
   closed eyes as two dark-blue arcs, dark-blue nose, two tan paws resting on the cloud.
4. NAME CLOUD: cream cloud-shaped banner with a 0.5% dark-blue outline, spanning 17%-83% of the width and
   24%-37% from the top (5 round bumps on top, biggest in the centre). Inside, centred, in a bold rounded
   sans-serif font (Nunito/Noto Sans Bold style), dark blue, the text:  {NAME}
5. FOUR INFO BADGES in a 2x2 grid, rounded rectangles with a 0.5% dark-blue outline, cream inside:
   each 41% wide and 13% tall; left column 7%-49%, right column 51%-93%; top row 39%-52% from the top,
   bottom row 55%-68%. Inside each badge: the ICON at the left end (solid dark blue, height about 10%),
   then to its right a small UPPERCASE label above a large value, left-aligned, dark blue, bold.
     top-left     : label WEIGHT   value {WEIGHT}   icon: baby scale
     top-right    : label LENGTH   value {LENGTH}   icon: ruler
     bottom-left  : label DATE     value {DATE}     icon: calendar
     bottom-right : label TIME     value {TIME}     icon: clock
6. FOOTPRINT PAD: an EMPTY rounded rectangle with a 0.5% dark-blue outline and cream inside, centred,
   spanning 29%-71% of the width and 72%-93% from the top, with one small yellow heart in its middle.
   Do not draw footprints and do not write text in it.

TEXT RULES: write ONLY the texts given above, exactly as written; do not add words, no watermark.
Output: one clean image, nothing else.
```

---

## Colour variants (replace the colour line in either prompt)

| theme | cream background | main (frame, icons, text) | yellow accent | animal |
|---|---|---|---|---|
| blue (default) | #F5ECD7 | #3E628A | #F0C446 | #C8A078 |
| green | #F5ECD7 | #5B8A72 | #F0C446 | #B9C3CC |
| pink | #F8ECE4 | #D9808C | #F4D28A | #F3E6D8 |
| purple | #F5ECD7 | #8E739F | #F0C446 | #E8B8C4 |

## Optional — product photo for marketing (after the flat design is approved)

Attach the approved flat design as the only image, then paste:

```
Use the attached flat design as the exact artwork of a 3D-printed newborn keepsake plaque.
Show it as a realistic product photo: the plaque stands upright on a light wooden shelf, leaning back about
12 degrees, soft daylight from the left, shallow depth of field, a blurred cosy nursery in the background.
The artwork must stay exactly the same (layout, colours, text). The shapes are slightly raised from the
cream base, matte plastic (PLA). No hands, no extra objects except a small plant in the blurred background.
```

---

## Backlit — coloured parts glow (thick opaque base, translucent PETG parts)

Attach the approved flat design as the only image, then paste:

```
Use the attached flat design as the exact artwork of a real BACKLIT 3D-printed newborn keepsake plaque (300 x 300 mm).
Show it as a realistic product photo in a dark cosy nursery at night: the plaque stands upright on a light wooden shelf,
leaning back about 12 degrees, seen from the front and slightly from the left. The only light in the room is the plaque.

How it is built and how it must look (very important):
- The cream background is a THICK, OPAQUE, matte white-cream plastic plate. It does NOT glow and does not let any light through:
  it stays plain cream, only faintly lit by the glow of the coloured parts next to it.
- ALL the coloured parts are made of TRANSLUCENT coloured plastic (PETG) set through the thick plate, and an LED behind the plate
  makes them glow in their own colour, like stained glass or neon: the frame, the cloud outline, the name text, the badge outlines,
  the icons, and the numbers glow deep saturated blue; the crescent moon, the stars and the heart glow warm yellow;
  the bear glows soft amber-orange. The glow is bright and even inside each shape, with a soft colour halo bleeding slightly
  onto the cream plate and onto the wall and shelf around the plaque.
- The cream-coloured details (bear muzzle and inner ears) are opaque and stay unlit.
- The coloured parts are raised about 1 mm above the plate, with crisp clean edges. A slim matte white box about 25 mm deep is visible
  behind and under the plaque with a thin white USB-C cable going to the shelf.

The artwork must stay exactly the same: layout, shapes, and all text (do not change any letter or digit).
Shallow depth of field, a blurred crib and a small plant in the background. No hands, no logo, no watermark.
```

Filaments from stock (all PETG, so the layers bond): base AD-PETG Opaque White; blue AD-PETG Translucent Blue;
yellow AD-PETG Translucent Yellow; bear AD-PETG Translucent Orange.

---

## Real render from the 3MF file (glow_cap), several angles

Attach `glowcap_plaque_en_300.3mf` (or the Arabic one), then paste:

```
Render the attached 3D model as a realistic product photo set. Use the model's real geometry and proportions exactly;
do not change any shape, letter or digit.

Parts: base = opaque cream-white; main (frame, name outline, text, icons, badge outlines) = translucent blue;
accent (moon, stars, heart) = translucent yellow; animal (bear) = translucent orange. The coloured parts are raised about
1.2 mm above the base, matte PETG plastic with very subtle 3D-printing layer lines.

Scene: the plaque stands upright on a light wooden shelf, leaning back about 12 degrees, a slim matte white box about 14 mm deep
behind it with a thin white USB-C cable, a blurred cosy nursery in the background (crib, small plant), soft daylight.

Give me 6 separate images of the same plaque, all in the same scene:
1. Front view, straight on, switched OFF in daylight.
2. Front view, straight on, switched ON in a dark room: only the translucent parts glow in their own colour (the frame stays unlit),
   the cream base stays dark, with a soft colour halo on the wall and shelf.
3. Three-quarter view from the left (about 45 degrees), switched ON.
4. Three-quarter view from the right (about 45 degrees), switched ON.
5. Close-up of the name cloud, text and the first two badges, switched ON, showing the raised edges and the glow.
6. Side view from the right showing the thickness of the plaque, the raised parts and the box behind, switched OFF.

Keep the same camera distance, lighting and background style across the images. No hands, no logo, no watermark.
```

Tip: if GPT returns only one image, send "continue with image 2", then 3, 4, 5, 6.
