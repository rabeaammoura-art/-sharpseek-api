# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

## 2026-11-03 (cloud) — wrench key holder restarted from zero: wrench body traced from the picture
- Owner rejected the first by-eye build (wrong proportions: I had assumed a 2000 px wide picture, it is 2345 px). Deleted it (still in git history). New: `cad/wrench/` — `trace_wrench.py` extracts outline + orange band from the reference by colour masks (json committed), `wrench.py` builds layers (border, plate, orange band, screws, recessed 18-tooth ring), STEP/STL/renders in `cad/wrench/out/`, `cad/wrench_render3d.py` = lit three.js render in headless Chromium.
- Left (in order): owner approval of the body, then hooks (ball-tip, from the trace positions), split into printable parts, workshop (also traced layer by layer), brake disc/drum variants, validation. Nothing print-tested.

## 2026-11-03 (cloud) — wrench key holder: owner's order of work (hooks LAST, do not forget them)
- Owner: leave the hooks for the very end but do not forget them. Open hook issues: shorter and wider than the picture, ball too small from the front, curl should be slimmer. Proposed order (NOT yet approved by the owner, who said do nothing without his permission): split into printable parts, workshop (layer by layer), brakes, then hooks. Ring top edge and render shadows fixed (commits 0fd9d3a, 3d7755b).

## 2026-11-03 (cloud) — wrench key holder shrunk to 300 mm (same proportions)
- Owner: a long non-square piece fits the H2D up to 300-310 mm, so no split into parts. `LENGTH_MM=300` (310 possible), size 300 x 68.8 mm, Z: border 2 + plate to 5 mm, band +1, hooks 6 mm. Splitting is dropped. Hooks need rework at this size (stem only 5.5 mm wide: now one 2.4 mm hole each, pilot 1.8): still LAST on the list. Next steps need owner approval.

## 2026-11-03 (cloud) — version 2 = 300 mm wrench + workshop (traced), version 1 untouched
- Owner: keep the first version intact, make a second with the workshop; colours black/white/orange only (white instead of grey, orange instead of red), disc included, trace from the picture (no GPT drawing needed), and asked about raising the workshop (4 cm too small). Built `cad/wrench/workshop/` (trace + parametric disc/caliper, `--stretch`); both 1.0 and 1.5 rendered, owner to choose. Left: owner's choice of stretch, real font for WORKSHOP, parametric gear, relief heights per element, slicing/time, hooks (last), nothing print-tested.

## 2026-11-03 (cloud) — version 3 idea: fish-skeleton hooks on the wrench (preview only, owner has the designers' OK to adapt)
- Owner found two MakerWorld designs (fish-skeleton wall hook, 30 cm customisable wrench) and said the designers allow adapting parts but not selling the piece as is. Wrench design rejected as a body (too slim, no room for the workshop). Fish hooks: side profile is a J (stem on the wall 6 mm wide x 7.6 thick, curl standing out 29.4 mm, 33 mm hang); printed in the same job as the plate, no screws, no supports. `cad/wrench/workshop/v3_fish_hooks.py` builds v3 (v2 + 5 hooks at scale 0.8: 4.8 mm wide, 23.4 mm out, 27 mm hang; stem thickness = plate 5 mm); the profile json is third-party-derived and kept OUT of the repo (`--profile`). Fixed a bug (hook went 12 mm behind the wall). v3 is a local preview, not committed as files; waiting for the owner's OK. Whole piece 300 x 116 x 23.4 mm.

## 2026-11-03 (cloud) — clean vector workshop (owner: my traced drawing and the other one each have good and bad parts)
- Owner's notes on the traced workshop: lifts and roof outline good; car had no headlights, disc muddy, jerry cans wrong/unclear, "more" (not yet sent). Plan approved: wrench body from the found wrench + workshop + fish hooks at scale 1.0 (not modified, owner: if strong do not change) + optional text.
- New `cad/wrench/workshop/vector_workshop.py`: workshop redrawn as clean 2D shapes (3 colours) with layout measured on the reference; kept the traced lifts + house outline; real font lettering, parametric gear, clear jerry cans, 6 spanners, cabinet, car with orange headlights, ceiling lamp, filters, clean disc + caliper; `S` = vertical stretch (1.5 default idea). Previews in `cad/wrench/workshop/vector_preview/` (flat S1.5, S1.0 + overlay on the reference). Next: owner's feedback on the flat drawing, THEN extrude to 3D (min feature 0.7 mm), then the new wrench body, fish hooks (scale 1.0), text, slicing/time.

## 2026-11-03 (cloud) — vector workshop: car taken from the owner's second picture, stretch chosen 1.25
- Owner: take ONLY the car from the other drawing; I pick the stretch. `trace_car.py` traces the white car (dark windscreen/grille/lights = holes, mirrors, roof arc; the floating bar above it dropped); the json stays local (the picture's origin is unknown, repo is public); `vector_workshop.py <ref> <out> <S> <car_trace.json>`. Stretch 1.25: house ratio about 2.4:1, close to the other drawing (2.5:1), details keep their size without big empty gaps; 1.5 left too much empty wall, 1.0 too low. Preview `vector_preview/vector_S1.25_car2.png`. Next: owner's OK on the flat drawing, then 3D, new wrench body, fish hooks 1.0, text.

## 2026-11-03 (cloud) — workshop approved flat, now in 3D; skill `3d-picture-to-cad` created
- Owner approved the clean vector workshop (lifts redrawn clean with details, car symmetric from his second picture, stretch 1.25) and asked for a skill so the mistake (auto-traced details, 3D before 2D approval) is not repeated: `.claude/skills/3d-picture-to-cad/SKILL.md` (+ line in CLAUDE.md). Plan approved: 1 workshop 3D (done: `workshop_v4.py`, black base + white/orange +0.8, min feature 0.7 mm), 2 new wrench body from the found wrench (300 mm, plain: NO text, the word WORKSHOP may change later), 3 fish hooks at scale 1.0, 5 3MF in 3 colours + slicer estimate. Next: step 2, show before 3.

## 2026-11-03 (cloud) — v5: new body (found wrench outline) + clean workshop + fish-profile hooks; 3MF + slice
- `cad/wrench/workshop/v5_new_body.py`: body from the found wrench's silhouette (300 mm, straight handle 15 mm tall, 12-point ring, border + plate + orange band, plain: no text/screws), workshop v4 sitting on the handle (shelf now reaches the ground line), 5 J hooks (fish side profile, scale 1.0, x = -80..80 pitch 40) with a 45 deg underside slope under the tip because printed plate-down the tip is an 11 mm cantilever; the slope must reach the J floor (a corner 0.24 mm away made a floating island = slicer warning). Piece 300 x 109 x 29.3 mm, all watertight, Z starts at 0.
- `make_3mf.py`: 3-colour Bambu 3MF (1 black, 2 white, 3 orange), PLA template, tower at (150, 230, w 30). CLI estimate PLA 0.20 mm, no support: 1h45m, 51.2 g (black 45.8, white 2.1, orange 3.3); body+workshop alone 1h16m / 42.4 g, hooks add about 30 min (tall layers). Cost NOT computed: price sheet missing (ask the owner for `3D_ZONE_TECH_Filament.xlsx`). The 3MF and renders are NOT in the repo (third-party-derived); inputs stay local (`--outline`, `--profile`, `--car-trace`). Nothing print-tested.

## 2026-11-03 (cloud) — v5 update: jaw mirrored (short prong at the bottom), workshop 1.25x uniform
- Owner: the short jaw prong goes at the bottom (mirrored the body about the handle's centre line, `FLIP`), and the total height (109) was too small -> whole workshop 1.25x uniform (`--ws-scale`, about the house bottom line): workshop 187 mm wide (equals the straight handle), piece now 300 x 124.3 x 29.3 mm. Disc plate now rests on the border layer (z 2) instead of starting in the air at z 5. CLI estimate PLA 0.20 mm, no support, tower on: 2h01m, 64.2 g (black 57.2, white 3.2, orange 3.7), no slicer warnings. Cost still needs the price sheet. Nothing print-tested.

## 2026-11-03 (cloud) — v6: owner-approved picture applied to the design, word changed to "Aldawayme"
- Flow that worked: flat picture (mock) -> owner's marks -> picture again -> design once. Decisions: handle 20 mm (widened downward, eased into the necks), ring head +15 % (piece 302.4 mm long), disc 75 % (now a parameter `disc_scale` of the vector workshop, default 1.0), ONE continuous orange line (lower jaw prong -> around the jaw slot -> U-turn at the upper prong -> handle top edge -> 240 deg around the ring head); the ring wall is only 3-5 mm so around the ring head there is no plate level: the line runs on the border level (1.4 mm) and the plate is cut away there (otherwise scalloped slivers made the line look dashed). Word: `text` parameter of the vector workshop (Noto Sans Bold, cap height 36 view units, stripes follow the word's width).
- `cad/wrench/workshop/v6_final.py` (inputs local: outline, hook profile, car trace). Piece 302.4 x 129.3 x 29.3 mm, all watertight, Z from 0. CLI PLA 0.20 mm, no support, tower on: 2h09m, 67.8 g (black 61.0, white 2.9, orange 3.9), no warnings; cost needs the price sheet. Nothing print-tested; the 3MF is not in the repo (third-party-derived).

## 2026-11-03 (cloud) — v6: wall screw holes added (owner: "you forgot the screw holes")
- Two countersunk holes on the handle's centre line at x = -100 and +100 mm (200 mm apart): through hole 4.2 mm, 45 deg countersink 8.5 mm head (2.2 mm deep), for 4 mm wall screws (plugs needed in plasterboard). The orange line keeps 0.6 mm clear of the heads. Picture shown first, then built in `v6_final.py` (`SCREW_XS/SCREW_D/SCREW_HEAD_D`). The touching border/plate shells shared the hole edges (non-manifold STL), so body black is now ONE fused solid. All parts watertight, size 302.4 x 129.3 x 29.3.
- Owner asked for NO print test / cost rerun this time: `/3d-print-test` and `/3d-cost` were NOT re-run after this change (the holes only remove a little material; earlier run: 0 problems, 2h09m, 67.8 g). Nothing print-tested.

## 2026-11-03 (cloud) — price sheet received; Aldawayme piece costed
- Owner uploaded `3D_ZONE_TECH_Filament.xlsx` to this cloud session (copied to `cad/config/filament_prices.xlsx`, git-ignored; `openpyxl` installed in `.venv-cad`). Ran the full flow on the v6 piece: `/3d-print-test` = 0 problems, then CLI cost with the sheet (PLA Basic priced as PLA+): 2h09m, 67.8 g. The money figure was given to the owner in chat only (the repo is public). Studio's estimate is usually ~5 % higher than the CLI.

## 2026-11-03 (cloud) — skill `3d-print-test` (printability check), the "سكيل فحص" the owner meant
- "سكيل" = skill (I first read it as scale and searched the wrong thing; no record of it in the repo or the other sessions I could read). Built `cad/print_test.py` + `.claude/skills/3d-print-test/SKILL.md` (+ line in CLAUDE.md): layer-by-layer (0.4 mm) plate-down check for open mesh, off-bed, too big, tiny bed contact, floating islands, overhangs over 45 deg, features thinner than 0.7 mm; optional `--slice` relays Bambu Studio warnings. Calibrated on the hooks: no slope -> problem, first slope (0.24 mm gap) -> floating island (same as the slicer warning), fixed hook -> clean. Whole v6 piece: 0 problems, 8 s; notes: five 0.4 mm overhangs, thin tapers of the orange line at Z 3. Also `make_3mf.py --scale` (optional, default 1.0).
- Owner's rule added to the skill: test with no problems -> run `/3d-cost` automatically on the same files; with problems stop and report first.

## 2026-11-03 (cloud) — little-prince lamp at 150 mm: files built
- Owner chose size 150 (X/Y x1.5, height unchanged) and the option-4 diffuser. `cad/lamp150.py`: diffuser (white disc 118 mm x 1.34 + black relief 0.67, 2 colours, ar/en) -> `cad/print_files/lamp_150/diffuser_{ar,en}.3mf` (own geometry, committed); case 150x150x80 and stand 105x105x5 from the owner's licensed 3MF are written to a scratch dir only (NOT committed: public repo, third-party design).
- CLI estimates (PLA, 0.2 mm, no support, no tower): case 2h52m/95 g, diffuser 0h26m/20 g, stand 0h28m/24 g = about 3h46m / 139 g per lamp. 200 mm (x2 XY): case 4h56m, diffuser 0h42m, stand 0h47m = about 6h25m. Uniform 2x incl. height would be 5.8x the original case time. Nothing print-tested (printer not here). Open: LED choice and fit of the larger case/stand, diffuser fit tolerance in the case opening, real values in the JSONs.

## 2026-11-02 (cloud) — little-prince lamp (Bambu 3MF from the owner): diffuser to carry name/date/weight/time/length
- 3MF has 3 plates: light case (~100x100x80), led stand (disc 70x70x5), light diffuser (disc ~79 mm x 1.34 mm, logo relief 0.67 mm). Owner holds the licence to modify. Decided: remove the logo, two versions (full Arabic / full English); layout via GPT prompt `cad/plaque/gpt_prompt/diffuser_layouts_PROMPT.md` (6 options). Owner chose GPT option 4 (bear on top) with the decoration as in the picture, test values (changeable), bigger text. Built `cad/diffuser.py` (+ `cad/plaque/diffuser_ar.json` / `diffuser_en.json`, previews in `cad/plaque/diffuser/`): bear/stars/icons traced from the picture, text from fonts. Left: owner's yes on the preview, then write the relief into the lamp 3MF (diffuser plate, white disc 1.34 + black relief 0.67).

## 2026-11-02 (cloud) — plaque fixing in the backlit box (nuts + screws) built; leg hinge found wrong
- Owner chose option A: two hex nuts planted in the back of the plaque (frame band, left/right) + screws from the back through two posts in the box. `fix_spec/fix_points/hexagon` in `newborn_plaque.py`; M3 for >= 250 mm, M2 below (the frame band scales with the size: 11.2 / 8 / 6 mm). Checked: pockets inside the band (walls 2.7 / 1.85 / 0.85 mm), no light leaks, watertight, zero plaque/box interference; 200 mm plaque 3h42m / 107 g, box + leg 1h40m / 81 g. Regenerated plaque 3MFs (ar/en), `glow_box_*`, `glowcap_box_and_leg_*`.
- Owner asked "are you sure about the leg motion?": a simulation showed (1) the screw axis is perpendicular to the back -> the leg turns in the back's plane, it cannot prop the plaque; (2) the leg is 2.8 mm too short. Fix proposed (drawing shown, awaiting yes): bracket with two ears + horizontal M3 pin on the boss, M3x5x5 brass insert (owner has 200 pcs, Temu) pressed in with a soldering iron (owner has one), leg +2.8 mm. Lesson: never call a mechanism "right" before simulating it; label claims "simulated" / "tested".
- Research (printed screws): printed threads only from about M8 up, PETG, 4-6 walls, 0.3 mm clearance; M3 printed is unreliable; metal nuts/inserts for repeated use. Twist-lock / bayonet printed designs exist (to test later on coupons).

## 2026-11-02 (cloud) — backlit set: box + leg now also as a ready 3MF
- Owner: "why is the box not in the file?" The plaque 3MF only had the plaque; box and leg were STL only. `newborn_plaque.py` now also writes `glowcap_box_and_leg_<size>.3mf` (box and leg side by side, one colour, no tower) next to the plaque 3MF; copied to `cad/print_files/glow_cap/` for 150/200/280. CLI: 200 = 1h37m / 80 g, 280 = 2h32m / 135 g. One file with plaque + box would not fit one plate (box ~ plaque size, bed 325 mm).

## 2026-11-02 (cloud) — first real Bambu Studio slice (owner, laptop): two nozzles win
- Owner opened `glowcap_plaque_ar_200.3mf` in Studio: the orange purging warning disappears after opening Purging volumes -> OK (Studio auto-calculates colour-based flush volumes, left extruder 150-625 mm3). Slice: 3h55m / 110.9 g with Studio's auto grouping (1+2 left, 3+4 right); 4h05m / 112.4 g with all colours on the left nozzle. Two nozzles save ~10 min (my CLI test claimed the opposite: trust Studio). CLI estimates are ~5 % low (flush volumes). Open: does a freshly opened regenerated file still warn? (owner to check); does 280 mm get two nozzles (tower position)? Owner still to send a Studio-saved 3MF (`test_fixed.3mf`) as ground truth if the warning persists.

## 2026-11-02 (cloud) — purging warning really fixed in all 3MFs
- Owner: no more warning in any file. The earlier "absurd estimate" (5 million hours) was a random CLI glitch, NOT caused by the 32-value flush matrix (re-tested: the doubled matrix slices fine twice, 3h41m / 107 g). Re-applied the `threemf.py` change and regenerated all 18 print 3MFs (standard, glow_cap, rails_280, lit_280, train_lit; ar/en). Verified each: 32 flush values, 4 filaments, tower on. Lesson: a single odd CLI result is not proof; re-run before reverting.

## 2026-11-02 (cloud) — two nozzles tested: no gain
- Owner asked why we do not use both H2D nozzles. Added `--nozzle-map 1,1,2,2` to `cad/bambu_slice.py` and sliced the 200 mm plaques with the plate at x=27..227 (the right nozzle cannot reach x<25). Lit (PETG): one nozzle 3h41m, maps 1,1,2,2 = 3h50m, 1,2,2,1 = 3h46m, 1,1,2,1 = 3h43m. Plain (PLA): one nozzle 2h30m, 1,1,2,2 = 2h29m. The time is dominated by the big base layers, not by colour swaps, so the second nozzle gives nothing (estimates) and costs plate position freedom; keep everything on the left nozzle. Re-test on the real printer (the slicer's estimate of nozzle switching may differ).

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
