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
   - Prices differ per filament: if the user has not given `--price-kg` for this filament,
     use 8 JOD/kg, say so in the reply, and invite them to correct it.
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
   the filament chosen in step 0, 8 JOD per kg, 0.10 JOD per kWh, 350 W. Report costs in JOD (دينار).
4. If a part reports a "floating regions" warning without supports, re-run it with `--support`.
   If a part FAILS because it does not fit the plate, say so (give its size from
   `prusa-slicer --info`) instead of guessing numbers.
5. Reply in the user's language with a short table: part, time, grams, cost; then the
   total line, and how many copies the user needs (e.g. screw caps x4, left + right side)
   if the file names or notes make that clear. State the filament used and the assumed prices so the user can
   correct them, and list the `out.3mf` paths.
