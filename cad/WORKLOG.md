# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

## 2026-11-02 (cloud) — Bambu Studio "Partial purging volume set to 0" warning: left as is
- The owner opened `glowcap_plaque_ar_200.3mf` in Bambu Studio (screenshot): H2D, 4 PETG filaments, 0.24mm Standard, tower right of the plaque: all OK, plus an orange warning about the purging volume (the 3MF carries one 4x4 flush matrix, the H2D has two nozzles). Doubling the matrix (32 values) made the CLI slice give absurd results (5 million hours), so it was reverted. Keep the 16-value matrix (200 mm lit: 3h42m / 107 g). The warning is harmless while all colours print on the left nozzle (filament map all 1). Do not touch the flush matrix without re-slicing.

## 2026-11-02 (cloud) — backlit original plaque marked FINAL
- Owner: keep the bear-head bridge (16.7 mm at 150 mm) as is. Lit plaque (`cad/print_files/glow_cap/`) is final: plaque 3MF (ar/en, 150/200/280), `glow_box_*`, `back_leg_*` (M3 x 12 screw + M3 nut + cord). Laptop copy: GitHub Desktop -> Fetch/Pull origin in `D:\github\-sharpseek-api` (a cloud session cannot write to the laptop; Remote Control does not support Windows). Next: stand for the plain plaque (no box).

## 2026-11-02 (cloud) — original lit plaque re-verified and regenerated
- Owner asked if the lit plaque was ready from the start: regenerated `glowcap_plaque_{ar,en}_{150,200,280}.3mf` with the current generator (tower placement, 4-filament settings), `check_plaque.py` OK (no leaks, watertight); bridge 12.6 mm at 200/280, 16.7 mm at 150 (risk). 200 mm slice at 0.24 mm: 3h41m / 107 g / 0.83 JOD (others from the README, 0.20 mm: 150 2h02m, 280 6h14m). Nothing print-tested.

## 2026-11-02 (cloud) — original plaque, backlit: folding leg on a screw + nut (decision)
- Owner (said: forget the train, work on the original "Yousef" plaque; guaranteed solutions, no untested mechanisms): stand for the backlit box = a flat leg on an M3 screw. `make_lit_box(..., leg=True)` adds a 14 mm boss high on the back panel (0.82 x size from the bottom) with a hex pocket for an M3 nut (opens to the cavity), a 3.4 mm screw hole through boss + back panel and a 2.5 mm cord hole below it. `make_back_leg(size)`: bar 14 x 4 mm, length 0.82 x size from pivot to foot (flush with the bottom edge when folded), opens 24 degrees, plaque leans 12 degrees, foot about 96 mm behind (280). Sizes 150/200/280 in `cad/print_files/glow_cap/` (`glow_box_*`, `back_leg_*`).
- Slice (0.24 mm, PETG): box 280 = 2h20m / 125 g; leg 280 = 14 min / 10 g. Fastest of the three stand options (leg ~ +14 min; separate slotted base ~ +45-60 min; wedge box 1-2 h+).
- Rejected/shelved (see STANDS.md): feet, rails, easel, clip, slotted pockets with print-in-place leg, hooks, flexible hinge, foot lip. Research notes: slot base clearance 0.2-0.4 mm is the proven range; PETG living hinges fail < 1000 cycles.
- Plain (non-lit) original plaque stand: still open (no box -> no boss); not decided.

## 2026-11-02 (cloud) — owner looking for an older plaque: standard bear plaque preview
- Owner forgot which chat had a plaque designed before the train; likely the standard bear + 4 boxes plaque. Added `cad/plaque/example_ar_preview.png` (from `example_ar.json`, 280). Waiting for the owner's picture to confirm.

## 2026-11-02 (cloud) — base now a real-looking track, plaque UPRIGHT (no tilt)
- Owner: the ladder looked like a fence/comb (my invention: wide sleepers + a tail behind the rear rail). Rebuilt `make_track_base`: two thin 5 mm rails on top of 14 narrow close sleepers (6 mm wide, 2.5 mm high, pitch ~12.7), sleepers stick out 12 mm equally beyond both rails (owner: a bit wider), no tail; centre sleepers left out for the USB-C cable. Rails 22 mm apart, base 171 x 51 mm (centre of mass +-25 mm inside).
- Owner: NO tilt at all -> `LIT_TILT = 0` (feet stands still use TILT 12). Locked fit (tray vs base) 0 mm3 interference; +-1.5 mm lift/push collides (locked). Preview: `cad/plaque/train_lit_assembled_preview.png`.
- Open risk: upright 285 mm plaque on a 35 mm deep base (centre of mass +-17 mm inside) may tip if bumped; to judge with the printer. Renders of the assembly (three.js in headless Chromium, plain lighting, not photoreal): `cad/plaque/train_lit_render_front.png` / `_back.png`. Plaque tongues (printed in the plaque 3MF) not re-checked against the pins at 0 tilt (same geometry as before, tray check only). print_files not regenerated, no re-slice.

## 2026-11-02 (cloud) — owner's explainer picture matched to the build; USB-C slot 14x8; wavy edge option
- Owner's picture = the same lit train design. Checked: "كغم" already correct, date is only an example, hooks/slide-left as built, body stays PETG blue (owner choice), LED layout left for later. Picture has a wavy (cloud) bottom edge, the build has a flat track strip.
- Done: tray USB-C slot enlarged to 14 x 8 mm (z 3-11). New JSON key `"track": false` removes the flat strip (wavy traced edge), default stays true.
- `track: false` first left the two hook tongues floating (not under wheels). Fixed by owner's choice: tongues/pins moved under two wheels (big engine wheel and 3rd wagon wheel, `WHEELS_LOCK_U`), applied to plaque, tray back tabs and base hooks via `keys=(xL, xR)` (pair no longer exactly symmetric, ~2 mm). Example JSON now has `"track": false`.
- Left: `cad/print_files/train_lit` NOT regenerated/re-sliced yet; fit check (entry/lock/interference) not re-run for the new positions; sleepers are no longer under the hooks (hooks sit on the rails, fine).
- Printer still at customs (owner, 2 Nov). Nothing print-tested.

## 2026-11-02 (cloud) — hook locking: Γ pins into L-shaped keyhole slots, slide 8 mm left
- Owner's spec (drew an upside-down L): four hooks, each on a long rail only; they ENTER holes in the plaque and the tray; lower the parts, then slide left/right. Built: base = ladder (two rails, six even sleepers + tail) with 4 hooks (stem + 3 mm pin + 6 mm head); plaque: two 18 mm tongues, 10.3 mm below the plaque, with an L-shaped keyhole slot (wide entry leg 6.8, narrow leg 3.4, slide 8 mm); tray: two back tabs (3 mm thick) with the same slots, and cut-outs in the lowest wall for the tongues. Everything is defined in a tray frame and mapped with `pin_frame()` (tilt 12 degrees, tray hangs on the pins).
- Software fit (`scratchpad/fit2.py`): zero interference at entry / halfway / locked, collision at the ends of the slot and for lift/pull/push. Base 280: 0h40m / 19 g; 200: 0h35m / 15 g. Totals about 6h34m (280) and 4h22m (200). Plaque not re-sliced after the slots (should be about the same).
- Not print-tested; pin 3 mm in PETG and the 0.2 mm slot play to be checked on the printer.
- Owner rule learned: do NOT edit before the owner confirms a drawing/understanding when they say so; they draw what they mean.

## 2026-11-02 (cloud) — base: posts clear of the rails, peg in the rear half
- Owner: the locking nubs must be 2 in front + 2 behind at equal places (not one on a sleeper and one on a rail), one holding the plaque, one the back. Slot moved 8 mm back so the posts stand between the rails; peg now in the rear half of the slot floor (tray hole at tray depth 1.4-8.0), the plaque's tongue pocket in the front half. Base depth 62 mm. Base 280: 0h46m / 24 g, 200: 0h40m / 20 g. Totals about 6h38m / 4h26m. Fit check: no interference.
- Also: `scratchpad/render` (three.js in headless Chromium) can make clean renders of any STL; not photoreal.

## 2026-11-02 (cloud) — locking for BOTH tray and plaque + even sleepers
- Owner: locking must hold the back (tray) AND the plaque; sleepers evenly spaced. Done: 6 even sleepers (pitch (L-12)/5), locks at +-1.5 pitch (`lock_x`); tray: 2 key holes + 2 tongue cut-outs; plaque: 2 tongues (12 mm) in its opaque base layer, 5.3 mm below the plaque; base: pegs + pockets. Slot floor made perpendicular to the tilted slot (fixed a 1388 mm3 interference). Assembly check script in scratchpad (tray/plate/base interference < 3 mm3).
- Base 280: 0h44m / 22 g, 200: 0h37m / 18 g. Totals about 6h36m (280), 4h23m (200). Not print-tested.

## 2026-11-02 (cloud) — base = ladder (two rails + fused sleepers + locking blocks)
- Owner's last-try spec: two long beams, cross beams fused with them, locking protrusion on top. `make_track_base`: rails 7 mm wide, 6 sleepers 12 mm, two of them (at +-key_x) carry the slot walls + a 6 mm peg. Floor 5 mm. Base 280: 0h43m / 21 g, 200: 0h36m / 17 g (the slab+rails version was 1h00m / 51 g). Totals about 6h35m (280) and 4h24m (200).
- Not print-tested; peg/hole fit and rigidity of the ladder to be checked on the printer.

## 2026-11-02 (cloud) — base = slab + two rails (as in the owner's explainer picture)
- Owner sent a product explainer (front plaque + LED + hollow back; plaque slides into the rails of a track base; one colour is enough). Base profile is now a thin slab (8 mm) with two rails that are the walls of the slot; sleepers off. Base 280: 1h00m / 51 g, 200: 0h42m / 33 g. Totals about 6h52m (280) and 4h27m (200).
- Tray + base lock with two 6 mm pegs. Not print-tested.

## 2026-11-02 (cloud) — railway-track base with locking pegs
- Owner's idea: base shaped like a railway track and locked to the tray. Done: two rails on the rear deck + two 6 mm pegs in the slot floor that enter two holes in the tray's lowest wall (`key_x`). Sleepers (cross grooves) measured +12 min -> optional (`sleepers=True`). Base 280: 1h11m / 62 g (plain was 1h04m). Totals about 6h57m (280) and 4h32m (200).
- Not print-tested; peg/hole fit (6.0 vs 6.6 mm) to be checked on the printer.

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
