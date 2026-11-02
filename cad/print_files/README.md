# Print files — newborn plaque (example name: يوسف / YOUSEF)

Open the `.3mf` files in Bambu Studio (H2D). Each plaque = 4 parts = 4 filament slots. The 3MF now carries the 4 filaments,
the slot colours and the prime tower (narrow, 6 mm right of the plaque), so Studio opens it ready; only swap in your real spools.
`standard/`, `rails_280/` default to **PLA** (PLA Basic profile); `glow_cap/` and `lit_280/` default to **PETG**.

| slot | part | standard (PLA) | glow_cap / lit (PETG) |
|---|---|---|---|
| 1 | base | PLA+ white | AD-PETG opaque white |
| 2 | main (frame, text, icons, outlines) | PLA+ blue | AD-PETG translucent blue |
| 3 | accent (moon, stars, heart) | PLA+ yellow | AD-PETG translucent yellow |
| 4 | animal (bear) | Walnut PLA | AD-PETG translucent orange |

Sizes: **150, 200, 280 mm**. 300 mm was dropped: with a prime tower it does not fit the H2D (see `cad/PRINTING_NOTES.md`).
In Bambu Studio keep the prime tower **narrow (about 14 mm) and to the right of the plaque**; the 3MF puts the plaque
4 mm from the left edge for that reason. 0.20 mm Standard, no supports, print flat as loaded.

| folder | what | note |
|---|---|---|
| `standard/` | raised plaque (Arabic/English) + `stand_foot_*` (print 2) | the normal one |
| `glow_cap/` | backlit plaque + LED box `glow_box_*` + folding leg `back_leg_*` | translucent parts glow; the box has a boss with an M3 nut pocket, the leg (14 x 4 mm) is screwed on with an M3 x 12 screw and opens 24 degrees; closed, it ends flush with the bottom edge; a stop cord goes through the two small holes |
| `rails_280/` | plaque with T-rails in the frame + `bridge` (print standing on its edge) + `bridge_leg` | needs an M3 bolt + nut; 280 mm only |
| `lit_280/` | thin translucent-base plaque + `lit_box_280` | older concept |

Measured with the Bambu Studio CLI (PETG, 14 mm tower, H2D, filament prices from the stock sheet), plaque only. PLA is faster: the 150 mm standard plaque takes 1h43m / 60 g in PLA vs 2h04m / 60 g in PETG.

| size | standard | glow_cap |
|---|---|---|
| 150 mm | 2h09m, 61 g | 2h02m, 57 g |
| 200 mm | 2h54m, 100 g, 0.75 JOD | 3h47m, 99 g, 0.78 JOD |
| 280 mm | 5h30m, 204 g, 1.52 JOD | 6h14m, 187 g, 1.43 JOD |

Single colour (PETG white, 280 mm): feet x2 ~40 min each (32 g), glow box 2h30m (133 g), bridge 22 min + leg 31 min (26 g).
Nothing here has been print-tested yet (printer not delivered). The 3MF files were sliced with the CLI, not opened in the app.

Other names/values: edit `cad/plaque/example_*.json` and run `python cad/newborn_plaque.py <file>.json`
(Windows: see `cad/README_WINDOWS.md`).

**Backlit stand (final decision, original plaque):** the closed box carries a thick boss high on the back (hex pocket for an M3 nut from the cavity, screw hole through the back panel); the leg `back_leg_<size>` is a flat bar 14 x 4 mm, 0.82 x size long (pivot to foot), printed flat without supports (280: 14 min, 10 g). Hardware: M3 x 12 screw + M3 nut (+ optional nylon washer) + a short cord. The plaque leans back 12 degrees, the foot lands about 96 mm behind (280). Not print-tested.

Re-verified 2026-11-02 (current generator, glow_cap, ar + en, 150/200/280): all meshes watertight, no light leaks, no base island under 4 mm2; largest bridge 12.6 mm at 200/280 but 16.7 mm at 150 (watch it). Measured with 0.24mm Standard + tower: 200 mm lit plaque = 3h41m / 107 g / 0.83 JOD.

**STATUS (2026-11-02): the backlit original plaque (`glow_cap/`: plaque 3MF + `glow_box_*` + `back_leg_*`) is FINAL.** The 16.7 mm bridge at the bear's head on the 150 mm size is accepted as is (owner's decision). Next: plain plaque stand (no box).

All 3MF files (18) were regenerated on 2026-11-02 with the flush-volume matrix for both H2D nozzles, so Bambu Studio no longer shows the orange "Partial purging volume set to 0" warning. Checked: every file has 4 filaments, the prime tower, the 32-value flush matrix; the 200 mm lit plaque (3h41m / 107 g) and the 200 mm plain plaque (2h29m / 111 g) slice normally.

**Measured in Bambu Studio (2026-11-02, owner's screenshots), 200 mm backlit plaque, 0.24 mm Standard:** both nozzles (Studio's own grouping: 1+2 left, 3+4 right) = 3h55m / 110.9 g; all colours on the left nozzle = 4h05m / 112.4 g. So the real slicer saves ~10 min with two nozzles (my CLI test said the opposite, so trust Studio). Leave the grouping on Optimal ("Set to Optimal"). Studio's purge volumes are colour based (150-625 mm3 per change, left nozzle), higher than the 280 assumed by the CLI, so CLI estimates are about 5 % low.
