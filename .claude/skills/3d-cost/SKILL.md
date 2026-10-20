---
name: 3d-cost
description: Estimate 3D print time and cost with Bambu Studio (official Bambu Lab profiles, default H2D + Bambu ASA). Use when the user asks how long or how much a print will take, or runs /3d-cost with STL/3MF/zip files.
argument-hint: "[files or zip] [--no-support] [--filament NAME] [--price-kg N] [--kwh-price N]"
---

# /3d-cost — print time and cost

Arguments: $ARGUMENTS

1. Make sure the toolchain is installed: `cad/setup.sh` (skips what is already there).
2. Collect the models. If a zip was uploaded or given, extract it into a new empty
   directory in the scratchpad. Use every `.stl` (also inside the zip). If no file was
   given, use the most recent upload.
3. Slice them all in one call, with supports unless the user said `--no-support`:
   ```bash
   .venv-cad/bin/python cad/bambu_slice.py --support <extra args> file1.stl file2.stl ...
   ```
   Pass through any `--printer`, `--process`, `--filament`, `--plate`, `--price-kg`,
   `--kwh-price`, `--watts` the user gave. Defaults: H2D 0.4 nozzle, 0.20mm Standard,
   Bambu ASA, 8 JOD per kg, 0.10 JOD per kWh, 350 W. Report costs in JOD (دينار).
4. If a part reports a "floating regions" warning without supports, re-run it with `--support`.
   If a part FAILS because it does not fit the plate, say so (give its size from
   `prusa-slicer --info`) instead of guessing numbers.
5. Reply in the user's language with a short table: part, time, grams, cost; then the
   total line, and how many copies the user needs (e.g. screw caps x4, left + right side)
   if the file names or notes make that clear. State the assumed prices so the user can
   correct them, and list the `out.3mf` paths.
