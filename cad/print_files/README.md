# Print files — newborn plaque (example name: يوسف / YOUSEF)

Open the `.3mf` files in Bambu Studio (H2D). Each plaque has 4 parts = 4 filament slots:

| slot | part | filament |
|---|---|---|
| 1 | base | PLA+ white (cream not in stock) |
| 2 | main (frame, text, icons) | PLA+ blue |
| 3 | accent (moon, stars, heart) | PLA+ yellow |
| 4 | animal (bear) | Walnut PLA |

Settings: 0.20 mm Standard, no supports, print flat as loaded.

- `standard_300/`: plaque Arabic + English (300 mm) and the stand feet (print 2).
- `lit_300/`: backlit plaque front (thin translucent base) + the LED box (306x306x25 mm).
- `test_150/`: the same at 150 mm for a first test print.

Other names/values: edit `cad/plaque/example_*.json` and run `python cad/newborn_plaque.py <file>.json`.
The 3MF files were sliced with the Bambu Studio CLI but not yet opened in the Bambu Studio app.

## Backlit "glow_cap" version (opaque base with openings, translucent coloured parts on top)

Files: `glow_cap_300/` and `test_150/glowcap_*` + `glow_box_*.stl` (shallow LED tray, 14 mm deep, USB-C slot).
Filaments (all PETG): slot 1 AD-PETG **opaque white**; slots 2, 3, 4 = AD-PETG **translucent** blue / yellow / orange (bear).
The frame band stays a plain raised band (it cannot glow). Wide openings keep thin base ribs so the bridges do not sag.
Measured (150 mm, PETG, prime tower on): plaque 2h33m + box 1h03m. A 300 mm plate with a prime tower does not fit
the H2D bed in my test (slicer reports a conflict), so 300 mm is untested in the slicer.
Checks: `python cad/check_plaque.py <json>`.
