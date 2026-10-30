---
name: 3d-cost
description: Estimate 3D print time and cost with Bambu Studio (official Bambu Lab profiles, H2D). Asks which filament (ASA, PLA, PETG, ...) unless it is given. Use when the user asks how long or how much a print will take, or runs /3d-cost with STL/3MF/zip files. Shortcuts: /3d-cost-pla, /3d-cost-petg, /3d-cost-asa.
argument-hint: "[files or zip] [--no-support] [--filament NAME] [--price-kg N] [--kwh-price N]"
---

# /3d-cost — print time and cost

Arguments: $ARGUMENTS

0. **Filament.** Decide the filament before slicing:
   - If `--filament` was passed, or the user named one in the request or arguments
     (ASA, PLA, PETG, ABS, TPU, ...), use it and do not ask.
   - Otherwise ASK the user with AskUserQuestion which filament to price
     (options: ASA, PLA, PETG, other) and wait for the answer. Never silently default to ASA.
   - Map the answer to an official H2D 0.4 profile name for `--filament`:

     | user says | `--filament` value |
     |---|---|
     | ASA | `Bambu ASA @BBL H2D 0.4 nozzle` |
     | PLA | `Bambu PLA Basic @BBL H2D` |
     | PLA matte / silk / sparkle | `Bambu PLA Matte @BBL H2D` / `Bambu PLA Silk @BBL H2D` / `Bambu PLA Sparkle @BBL H2D` |
     | PETG | `Bambu PETG Basic @BBL H2D 0.4 nozzle` |
     | PETG translucent (for lit plaques) | `Bambu PETG Translucent @BBL H2D 0.4 nozzle` |
     | ABS | `Bambu ABS @BBL H2D` |
     | TPU | `Bambu TPU 95A HF @BBL H2D 0.4 nozzle` |
     | PC | `Bambu PC @BBL H2D 0.4 nozzle` |

     For anything else, list the matching names from the Bambu profiles
     (`find` in the flatpak `profiles/BBL/filament` for `H2D`) and ask which one.
   - **Prices always come from the stock sheet** `cad/config/filament_prices.xlsx`
     (3D ZONE TECH landed prices in JOD/kg, incl. shipping & customs). `bambu_slice.py` reads it
     itself and prices each filament slot by type: PLA/PLA Basic/Matte -> PLA+, PLA Silk -> Silk PLA,
     PETG -> PETG, PETG Translucent -> AD-PETG, ASA, ASA-CF, TPU -> TPU 95A. Do not pass
     `--price-kg` unless the user gives a price for this run. If the sheet is missing (it is
     git-ignored because the repo is public, so a fresh session may not have it), ask the user to
     upload `3D_ZONE_TECH_Filament.xlsx` and copy it there. Quote the prices the script prints.
1. Make sure the toolchain is installed: `cad/setup.sh` (skips what is already there).
2. Collect the models. If a zip was uploaded or given, extract it into a new empty
   directory in the scratchpad. Use every `.stl` (also inside the zip). If no file was
   given, use the most recent upload.
   A multi-colour `.3mf` from `cad/newborn_plaque.py` is sliced as one plate: pass `--filament`
   once per colour slot (4 for the plaque: base, main, accent, animal), all with the chosen
   filament unless the user names different ones. Plates also include a pair of stand feet
   (`stand_foot_<size>.stl`, print x2) — slice one and double it.
3. Slice them all in one call, with supports unless the user said `--no-support`:
   ```bash
   .venv-cad/bin/python cad/bambu_slice.py --support <extra args> file1.stl file2.stl ...
   ```
   Pass through any `--printer`, `--process`, `--filament`, `--plate`, `--price-kg`,
   `--kwh-price`, `--watts` the user gave. Defaults: H2D 0.4 nozzle, 0.20mm Standard,
   the filament chosen in step 0, landed prices from the stock sheet, 0.10 JOD per kWh, 350 W.
   Report costs in JOD (دينار).
4. If a part reports a "floating regions" warning without supports, re-run it with `--support`.
   If a part FAILS because it does not fit the plate, say so (give its size from
   `prusa-slicer --info`) instead of guessing numbers.
5. Reply in the user's language with a short table: part, time, grams, cost; then the
   total line, and how many copies the user needs (e.g. screw caps x4, left + right side)
   if the file names or notes make that clear. State the filament used and the prices read from the sheet so the user can
   check them, and list the `out.3mf` paths.
