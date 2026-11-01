# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

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
