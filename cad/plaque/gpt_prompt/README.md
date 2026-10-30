# GPT prompt pack — newborn plaque (300 x 300 mm)

Goal: have ChatGPT (GPT image) draw **exactly** the plaque that `cad/newborn_plaque.py` builds,
so the look can be reviewed, approved and used for marketing before printing.

## Files

| file | what it is |
|---|---|
| `PROMPT.md` | the prompts (Arabic edition, English edition, colour variants, optional product photo) |
| `1_layout_blueprint.png` | zone sizes and positions in mm (attach #1) |
| `2_style_reference_arabic.png`, `2_style_reference_english.png` | the real generated design, flat colours (attach #2) |
| `3_shapes_sheet.png` | the 4 icons, bear, moon, stars, heart as drawn by the generator (attach #3) |
| `4_mood_reference_ai_mockups.png` | the earlier AI mock-ups, mood only (attach #4) |
| `layout.json` | the same geometry as numbers (mm), colours and fonts |

## How to use

1. Open a new ChatGPT chat with image generation.
2. Attach the 4 images in the order above (use the Arabic or the English style reference to match the edition).
3. Paste Prompt A or B from `PROMPT.md` with the `{…}` values filled in.
4. Ask for 4 variations and keep the closest one.

## Things to know

- Image models often break **Arabic text** (joining, digit order). If the Arabic comes out wrong, ask GPT to
  regenerate only the text, or keep the picture as a look reference only: the printable model always comes from
  the generator, which shapes Arabic correctly.
- The generated picture is a **reference**, not the print file. Final STL/3MF files come from
  `python cad/newborn_plaque.py cad/plaque/example_ar.json`.
- Animals other than the bear (bunny, elephant), the stand and the lit version are not part of this pack yet.
- This repository is public, so everything in this folder is public too.
