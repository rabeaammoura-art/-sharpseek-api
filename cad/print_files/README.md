# Print files — newborn plaque (example name: يوسف / YOUSEF)

Open the `.3mf` files in Bambu Studio (H2D). Each plaque = 4 parts = 4 filament slots (colours of the PETG set):

| slot | part | filament |
|---|---|---|
| 1 | base | AD-PETG opaque white (PLA+ white also works for the standard plaque) |
| 2 | main (frame, text, icons, outlines) | blue (translucent AD-PETG for `glow_cap`) |
| 3 | accent (moon, stars, heart) | yellow |
| 4 | animal (bear) | Walnut PLA (standard) / translucent orange (`glow_cap`) |

Sizes: **150, 200, 280 mm**. 300 mm was dropped: with a prime tower it does not fit the H2D (see `cad/PRINTING_NOTES.md`).
In Bambu Studio keep the prime tower **narrow (about 14 mm) and to the right of the plaque**; the 3MF puts the plaque
4 mm from the left edge for that reason. 0.20 mm Standard, no supports, print flat as loaded.

| folder | what | note |
|---|---|---|
| `standard/` | raised plaque (Arabic/English) + `stand_foot_*` (print 2) | the normal one |
| `glow_cap/` | backlit plaque + shallow LED tray `glow_box_*` | translucent parts glow; frame does not |
| `rails_280/` | plaque with T-rails in the frame + `bridge` (print standing on its edge) + `bridge_leg` | needs an M3 bolt + nut; 280 mm only |
| `lit_280/` | thin translucent-base plaque + `lit_box_280` | older concept |

Measured with the Bambu Studio CLI (PETG, 14 mm tower, H2D, filament prices from the stock sheet), plaque only:

| size | standard | glow_cap |
|---|---|---|
| 150 mm | 2h09m, 61 g | 2h02m, 57 g |
| 200 mm | 2h54m, 100 g, 0.75 JOD | 3h47m, 99 g, 0.78 JOD |
| 280 mm | 5h30m, 204 g, 1.52 JOD | 6h14m, 187 g, 1.43 JOD |

Single colour (PETG white, 280 mm): feet x2 ~40 min each (32 g), glow box 2h30m (133 g), bridge 22 min + leg 31 min (26 g).
Nothing here has been print-tested yet (printer not delivered). The 3MF files were sliced with the CLI, not opened in the app.

Other names/values: edit `cad/plaque/example_*.json` and run `python cad/newborn_plaque.py <file>.json`
(Windows: see `cad/README_WINDOWS.md`).
