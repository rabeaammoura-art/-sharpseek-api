---
name: print-test
description: Pre-print simulation for ANY STL/3MF/zip, run after /3d-cost and before printing. Checks that the print will succeed (thin features, warping, stability) AND that the printed part works as designed - gaps/clearances between mating parts and print-in-place joints re-computed as the printer will really make them (best..worst case), hinges turned through their range, sliding joints slid. Use when the user runs /print-test or asks "will it print", "will it assemble", "will the hinge work / jam", "is the clearance right".
argument-hint: "[files or zip] [--assembly] [--filament NAME] [--load N] [--png out.png]"
---

# /print-test — will it print, and will the printed part work?

Arguments: $ARGUMENTS

Generic: works on any STL or 3MF (also inside a zip). It does NOT repeat `/3d-cost`: bed fit, supports, time and cost
stay there. Code: `cad/print_test.py`; printer error numbers: `cad/config/printer_profile.json`.

1. **Filament.** Use `--filament` / the one named (PLA, PETG, ASA, ABS, PC, TPU). If `/3d-cost` was just run in this
   conversation reuse its filament; otherwise ASK (AskUserQuestion). Never silently default.
2. Toolchain: `cad/setup.sh` (installs what is missing; needs `trimesh networkx shapely rtree scipy matplotlib`).
3. Collect the models like `/3d-cost` (extract zips into a new empty scratchpad dir; use every `.stl` / `.3mf`; else the latest upload).
4. **Run two kinds of checks:**
   - **Print files** (what goes to the printer), all in one call:
     `.venv-cad/bin/python cad/print_test.py --filament <NAME> --png <scratchpad>/pt.png file1 file2 ...`
     This checks mesh health, features too thin to print, warping, stability, strength, and any print-in-place joint
     inside a single file (separate shells = pin and hole, hinge, etc.).
   - **Fits between separate parts** need the parts in their ASSEMBLED positions in ONE file. For the newborn plaque
     with `"stand": "rails"`: `.venv-cad/bin/python cad/export_assembly.py <plaque.json> --out <scratchpad>`, then
     `.venv-cad/bin/python cad/print_test.py --assembly --filament <NAME> <scratchpad>/assembly_*.3mf`.
     For any other design, ask the user for (or generate) an assembly file; if there is none, say plainly that fits
     between loose files cannot be checked and run only the first kind.
   Pass through `--load N` (sideways force at the top, default 10 N; ask what the part carries when strength matters),
   `--profile`, `--fill`. Exit code 2 = at least one FAIL (not a tool error).
5. **Reply in the user's language, short:** per part a verdict (✅ OK / ⚠️ WARN / ❌ FAIL), then ONLY the WARN/FAIL rows with
   the concrete fix; one line for everything that passed. For each fit row give: designed gap → printed best..worst gap,
   and the design gap the tool recommends. Show the PNG when it exists.
6. FAIL = "do not print yet" + what to change (offer to edit the generator, e.g. `RAIL_TOL`, `CLEARANCE` in
   `cad/newborn_plaque.py`, and re-run). Only OK/WARN = safe to print, with the warnings to watch.

**Be honest about certainty.** While `calibrated` is false in the printer profile (it is, until the H2D arrives and a test piece
is measured with calipers), fit verdicts are RANGES from public reports, not promises: "undecided" means it depends on the real
printer. After measuring, put the real numbers in `printer_profile.json` and set `calibrated: true`. Also not covered:
impact, creep, heat, slicer-specific behaviour, travel beyond 28 mm for sliding joints, hinge axes not parallel to x/y/z.
