# PLAYBOOK for an AI assistant (Gemini / any): turn a character sheet into a printable student pack

You do NOT design 3D models by hand. This repo is the designer. Your job is to (1) set up a "theme" entry that tells the
generator where each artwork sits on a GPT sheet and which colours it uses, (2) run it, (3) look at the preview PNG at full
size, (4) fix by editing the theme only, (5) deliver the .3mf. Never change the layer rules below.

## 0. Run it (no AI needed for existing themes)
    pip install -r requirements.txt            # Python 3.10+ ; Windows: use `py -m pip` / `py`
    python generate.py --name ADEL --theme football --pieces tag,pencil,ruler --plate --out out
    python generate.py --list-themes
`--plate` writes ONE 3MF with all pieces of the pack (PLA, 4 AMS slots). Open it in Bambu Studio (H2D). No bottle tag
(owner decision): always `--pieces tag,pencil,ruler`.

## 1. Fixed rules (owner decisions: do not change)
- Printer Bambu Lab H2D, 0.4 mm nozzle, PLA / PLA+, max **4 colours** per pack (AMS). Print time matters more than cost.
- Layer stack: base slab **1.6 mm** in the OUTLINE colour under the whole silhouette; colours then rise: outline colour
  top 2.2, mid colours 2.8, top colour 3.2 (heights dict in the theme). Ruler: everything flat, top 2.0 mm.
- Minimum feature **0.8 mm** (thinner lines are dropped). Sheet lines must be >= 1 mm wide at print size.
- Tag ~70 mm wide (kept 62-76 mm tall by `tag_fit`), 5 mm hanging hole, loop wall >= 2 mm.
- **Pencil topper** is NOT a flat plate: 85 mm long block, body 13.0 mm, total 14.6 mm, with a horizontal teardrop tunnel
  (circle Ø7.7 mm centred 6.0 mm above the plate, roof cut flat at z 10.4, open at both ends). The generator builds it.
- Ruler 165 x 50 mm, ticks every mm, numbers 0-15, flat 2.0 mm.
- Name text is generated in code (font Poppins ExtraBold, CAPITALS). Never ask the image model to draw the name.
- Registered characters (Disney, Sanrio, Marvel, Nintendo...) = personal gifts only: keep their art in `art_private/`
  (git-ignored), never commit it, never sell/advertise.

## 2. The sheet (what GPT must draw) - see DESIGN-KIT prompt
4 artworks on one white-background sheet: tag (large, empty name band below), bottle tag (skip), pencil strip (decoration at
both ends), ruler bar (decoration at both ends). 4 flat colours, thick sticker outline, no text, no loop. Colour of the
outline = the BASE colour of the whole pack (it is the black/navy/purple backing).

## 3. Add a theme (edit `themes.py`, then `python trace.py <theme>`)
Copy an existing theme as a template (e.g. `THEMES["spiderman_g"]`, `football`, `kitty`). Key fields:
- `art`: path of the sheet PNG. `outline`: the base colour name. `palette`: {name: ((R,G,B), printed_colour)} - list
  every colour seen on the sheet (use k-means on the sheet to find them) and map anti-aliased shades to the nearest
  printed colour; light colours that look like paper must be treated carefully (see flood note).
- `filament_rgb`, `heights`, `slots` (AMS order), `text_rings`, `ruler` (band/body/rim/ticks colours).
- `motifs`: for tag, pencil_l, pencil_r, ruler_l, ruler_r: `box=(x0,y0,x1,y1)` in sheet pixels, `scale` (mm per px:
  tag 70/box_width), `bg="flood"`, `seal=["bottom"]` for the tag (the name band is added by code), `tab_x_px` (loop x).
  Crop only the artwork: cut off the sheet's empty name band, outline bars and any hanging loop.
- Tools inside a motif: `erase=[(x0,y0,x1,y1)]`, `erase_poly`, `paint_poly=[(colour,[pts])]`, `move`, `insert`,
  `recolour_dark`, `halo/flag_ring`. Theme options: `tag_fit`, `tab_under_art`, `sil_close`, `thicken`, `webs`,
  `flag_rings`, `ink_only`, `art_ring`, `remap`.
- Flood note: the background is removed by flood fill from the crop border. Light shades touching the border can be
  eaten; draw an enclosing dark line or recolour them.
Then: `python trace.py <theme>` (writes motifs/<theme>.json) and `python generate.py --name TEST --theme <theme>`.

## 4. Review loop (mandatory)
Open `out/<NAME>_<theme>/<name>_tag.png`, `_pencil.png`, `_ruler.png` AT FULL SIZE (zoom into the loop, thin lines,
eyes, edges). Check: no floating bits, nothing <0.8 mm, loop not cut, name fits, pencil/ruler decorations present.
Fix only by editing the theme boxes/erase/paint, re-trace, repeat. Say honestly what is still not perfect.
`python tests/test_geometry.py` must pass.

## 5. Time/cost facts learned
- Time is driven by colour changes and the number of tiny coloured islands. Fewer, bigger regions = faster.
- All colours of a pack share the same 4 AMS slots; several packs with the same 4 colours print on one plate
  (`--pack A:theme B:theme --plate`), saving purge time.
- Flush multiplier 0.6 in Bambu Studio saves ~10 min and ~6 g per pack (watch white after black).
- Estimates from the CLI (`verify_slice.py`) are approximate; Bambu Studio's number is the reference.
