# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

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
