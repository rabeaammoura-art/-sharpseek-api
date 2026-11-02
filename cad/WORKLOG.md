# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

## 2026-11-02 (cloud) — base: arches measured, shorter base instead
- Arch windows under the base (`make_foot(arches=True)`): measured -4 g, +7 min -> off. Base length 0.8 -> 0.6 of the plaque width: 280: 1h04m / 60 g, 200: 0h43m / 38 g. Totals: 280 about 6h50m / 193 g / 1.35 JOD; 200 about 4h28m / 118 g / 0.86 JOD. Print files updated.

## 2026-11-02 (cloud) — backlit train: cut print time (owner: "time is our weak point", said many times)
- 0.24mm Standard profile instead of 0.20; tray now has 2 mm walls and an open back with three LED bars (73 -> 43 cm3); base is one long piece. 280: plaque 4h14 + tray 1h32 + base 1h24 = about 7h10m (was 8h18m). 200 mm: 2h38 + 1h07 + 0h56 = about 4h41m. Files in `cad/print_files/train_lit/` (280 and 200).
- Lesson: when the owner says time matters, optimise it without asking first. Still heavy: base (79 g at 280) - ideas: arch windows, lower tilt. Not print-tested.

## 2026-11-02 (cloud) — backlit train: one long base + print files
- Owner chose ONE long base (not two feet), slim: `make_foot(..., length=)` now builds a single 229 x 54 x 22 mm base (stability margin 20 mm). Light tray fixed to follow the full silhouette (it was following the plate with openings, 214 cm3 -> 72 cm3).
- Estimates (H2D, tower, +-20 %): plaque 4h37m / 81 g / 0.57 JOD; tray 2h12m / 79 g / 0.59; base 1h29m / 77 g / 0.55. Sum about 8h18m, 238 g, 1.71 JOD (LED strip extra). Files in `cad/print_files/train_lit/`.
- Left: owner feedback; the tray and base are heavy for what they are (could lighten); nothing print-tested.

## 2026-11-02 (cloud) — backlit (glow_cap) train
- `example_train_lit_ar.json`: layout train + glow_cap + theme `train_lit` (slots: PETG Blue opaque body, AD-PETG translucent white / yellow / orange-red for the bear; owner dislikes a black body for a baby). Added a flat track strip under the wheels (flat bottom edge), `make_lit_tray` (light tray that follows the outline, 14 mm deep, LED on its back panel, USB-C slot) and feet for it (`make_foot(size, thickness)`).
- Slice (280 mm, prime tower x=288, left nozzle): 4h37m / 81.4 g / 0.57 JOD (+-20 %). Tray and feet not sliced yet. Not print-tested.
- Preview used the wrong palette before (white outside); fixed: 3MF slot colours are now the train_lit ones.

## 2026-11-02 (cloud) — train: real stock colours + rounded name font
- Price sheet received again (git-ignored in `cad/config/filament_prices.xlsx`). Stock has NO cream, navy or tan: train theme now PLA+ Blue / PLA+ White / PLA+ Yellow / Wood PLA (bear). Horse: PLA+ Blue, White, Cyan, Yellow. Night theme updated the same way.
- Owner prefers the rounded name font of the picture: new kind `"name"` uses Baloo Bhaijaan 2 ExtraBold (`cad/fonts`, OFL) for Arabic names; values/labels keep Noto Kufi.
- Left: slicing estimate with prime tower (4 filaments: Blue, White, Yellow, Wood PLA), owner's feedback.

## 2026-11-02 (cloud) — "train" layout is now traced from the owner's flat picture
- The owner rejected hand-drawn shapes ("do not draw at all, trace this"). The Gemini flat picture of the train is traced with `cad/trace_layers.py` (options `cad/plaque/train_trace_opts.json`) -> `cad/plaque/train_layers.json`; `"layout": "train"` loads it (the old hand-drawn one is `layout_train_drawn`, unused). Name and the four values are re-drawn with the fonts (recessed in the cream); labels and icons stay as traced. Bear: tan slightly higher, its darker details lower (same filament).
- Result ~ 280 x 162 mm at size 280, 4 colours, watertight. Feet stand only. Not sliced yet.
- Rule from the owner: never invent shapes; trace the pictures they provide (ask Gemini for flat 4-colour versions).

## 2026-11-02 (cloud) — horse stands on a rocker runner
- Owner: "why not keep it a rocker?" -> `make_rocker_runner` (horse layout only): curved runner 220 x 50 mm (14 mm below the plate edge, 8 mm grip) with a 4.2 mm slot along the top; the flat plaque slides in and rocks (CoM about 90 mm above the bottom, curvature radius about 300 mm -> self-centring). Exports `rocker_runner_<size>.stl`, print lying on its side. Single colour PLA+ estimate: 1h29m / 78.7 g / 0.60 JOD.
- Warning from the slicer: "floating cantilever" (the 8 mm slot ceiling bridges across the arc); not print-tested. Sideways stability of a 4 mm plate in a 50 mm runner is unverified.
- Left: owner feedback; a bigger flat picture of the horse for a cleaner head; estimate of the plaque itself with the prime tower.

## 2026-11-02 (cloud) — "horse" layout traced from the owner's mock-up (rocking horse)
- Owner sent a Gemini image of a rocking horse (layered cream horse, blue mane/tail, navy saddle with the name, curved navy rocker carrying the 4 info columns) and asked not to simplify ideas. Hand-drawn shapes were too crude, so `cad/trace_layers.py` now converts a picture into colour layers (nearest palette colour, glow absorbed, smoothed, contourpy polygons) -> `cad/plaque/horse_layers.json`; `"layout": "horse"` (theme `horse`: navy / cream / blue / yellow) loads it and re-draws the name and info text with the real fonts.
- First result looks like the picture but the head/muzzle are rough (source crop is only ~620 px). Better: ask Gemini for a big flat front view of the horse alone, trace again.
- Open problem: a flat plate cannot stand on the curved rocker edge -> needs a stand decision (feet slot does not fit a curved bottom). Not sliced, not discussed with the owner yet.

## 2026-11-01 (cloud) — "train" layout (owner picked this design from a Gemini mock-up)
- Round "night" layout was rejected ("looks bad"). Owner sent a Gemini image: steam engine pulling 4 wagons (date, time, length, weight cards), dome with the name, sleeping bear, moon, stars, pedestal slab. Built as `"layout": "train"` (`cad/plaque/example_train_ar.json`, theme `train`: navy / cream / yellow / tan). Bear kept, smoke cloud kept.
- Flat shapes only, 4 colours, text and icons recessed in cream (no extra colour changes). Size 280 gives about 285 x 190 mm. Meshes watertight. Feet stand only. Not sliced yet (no time/cost), stock colours for cream/tan are placeholders in THEME_FILAMENTS.
- Left: owner feedback on the preview, slicing estimate with tower (plate is ~5 mm wider than `size`, tower still fits at 280), print_files, optional lit/glow check of this layout.

## 2026-11-01 (cloud) — new "night" layout (round, moon, sleeping baby, hanging tags)
- Owner liked an AI mock-up (round plaque on an oval pedestal, crescent moon, name cloud, 4 hanging star/tag cards with strings, sleeping character). Built as `"layout": "night"` (example `cad/plaque/example_night_ar.json`, theme `night`: navy / white / yellow / skin). Decisions: baby instead of bear, strings kept, no bow, pedestal kept, simple 4 colours.
- Feet stand only (round shape has no straight side bands for rails). Meshes watertight; 280 mm and glow_cap 200 mm generate. Text on the tags is small: use size >= 200. Not sliced/cost-checked yet; footprint pad is the ellipse on the right cloud; owner has not yet seen/approved the preview.
- Left: owner feedback on the look, stock colours for the night theme (navy / skin), slicing estimate with tower, regenerate print_files.

## 2026-11-01 (cloud) — state of the project
- Sizes: any up to ~290 mm coloured (max with prime tower); 150/200/250/280 proven. 300 mm fails in Bambu Studio (no room for the tower). Test file for 290 mm sent to the owner; result pending.
- 3MF now carries 4 filaments + slot colours + prime tower; Bambu Studio opens it with the 4 colours (confirmed by the owner). Estimates vary +-20 % run to run.
- Six colour themes (blue, pink, green, purple+gold, sky, black+gold) built; baby boy / girl characters built (small, may be enlarged); owner to choose.
- Stands: slotted feet (default), rails + bridge with folding leg (280 mm), clip, easel. Nothing print-tested (printer not delivered).
- Windows: `cad/bambu_slice.py` works with the installed Bambu Studio (laptop session, commit eef8ef5).

## 2026-11-01 (laptop) — Windows slicing test
- Slicing the 150 mm plaque with the embedded 3MF settings: 1h58m / 64.8 g (standard), 2h45m / 63.0 g (glow_cap); no warnings.
