---
name: 3d-print-test
description: Printability test for a 3D model before printing (FDM, H2D): finds floating islands, overhangs over 45 degrees, features too thin, parts off the bed or too big, open meshes, tiny bed contact, and relays Bambu Studio slicer warnings. Use whenever the owner asks to check/test if a part is printable, "فحص للطباعة", "في مشاكل؟", or before sending any STL/3MF/zip for printing. If the test finds NO problems it runs /3d-cost on the same files automatically; with problems it stops and reports them.
argument-hint: "[STL/3MF files of ONE job] [--angle 45] [--min-feature 0.7] [--slice]"
---

# /3d-print-test — does this print, and where does it fail?

Arguments: $ARGUMENTS

The printer has not arrived (see CLAUDE.md): this is a **software check**, never say "it printed fine".

1. Toolchain: in a cloud (Linux) session `cad/setup.sh` once (skips what is installed).
2. Collect the files. All files of ONE multi-colour job go in ONE call (they print together, the check unions them). A zip: extract
   into a new empty scratchpad directory first and run with `python -I`-safe paths. 3MF works; STL is the most reliable.
3. Run: `.venv-cad/bin/python cad/print_test.py FILES --no-tower-note`
   - `--angle 45` overhang limit (steeper = more overhang tolerated; PLA 45 is the safe default), `--min-feature 0.7` (mm), `--bed 325x320x325`.
   - Add `--slice [--filament "Bambu PLA Basic @BBL H2D" ...] --tower-x X --tower-y Y --tower-w W` to also run the Bambu Studio CLI and
     turn its warnings (for example "floating regions") into problems. For time and money use `/3d-cost` (it asks for the filament).
   - Exit code 1 = at least one PROBLEM.
4. Read the result and answer in short Jordanian Arabic: problems first (with the place: Z range, x/y), then notes, then ONE fix per
   problem, then the next step. Do not edit the model unless the owner agrees (he wants to approve designs first).
5. **No problems (exit code 0) -> run `/3d-cost` on the same files, automatically** (owner's rule). Follow that skill: use the filament the
   owner named or the one already agreed for this job (PLA = PLA+ unless told otherwise) and ask only if none was given; multi-colour 3MF needs
   `--tower-x/--tower-y/--tower-width` (see cad/PRINTING_NOTES.md). If `cad/config/filament_prices.xlsx` is missing, still give time and
   grams and ask the owner for `3D_ZONE_TECH_Filament.xlsx` for the price. **Problems found -> do NOT run /3d-cost**: report them and the fix first.
   Then give one summary: test result + time + weight + cost.

## What each finding means and the usual fix
| finding | meaning | usual fix |
|---|---|---|
| open mesh / negative volume | slicer may drop or break parts | repair the mesh, flip normals |
| not on the bed (zmin != 0) | part floats or sinks | translate so zmin = 0 |
| bigger than the bed | cannot print | scale, split, or turn it; multi-colour also needs the prime tower room (see cad/PRINTING_NOTES.md) |
| floating island at Z | a region starts in the air (nothing below) | join it to the part below, add a rib, or support only there; a corner 0.2 mm away from the surface is enough to make one |
| overhang > angle, deep/tall | a ledge printed in the air (hook tips, bridges, undersides) | 45 degree slope, shorter ledge, or local support |
| overhang ~0.4 mm, small area | harmless rounding | ignore |
| features < min-feature | will vanish or print weak | thicken to 0.7 mm or more, or drop them |
| tiny bed contact | will peel off | brim/raft or a wider first layer |

## Calibration and limits
- Layer-by-layer check at 0.4 mm steps, plate-down orientation only. On the wrench key holder it agreed with the Bambu Studio warnings in three cases:
  hook without the 45 degree tip slope (problem), the first slope with a 0.24 mm gap (floating island), the fixed hook (clean).
- It does NOT check: warping, bridging quality, stringing, strength, cooling, real colour-change purge, or nozzle collisions. Say so when asked.
- Orientation other than the file's own is not tried: if the check fails, suggest re-orienting only after the owner agrees.
