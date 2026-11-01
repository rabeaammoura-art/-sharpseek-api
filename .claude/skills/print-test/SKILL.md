---
name: print-test
description: Pre-print simulation for ANY STL/3MF/zip - checks the print will succeed (mesh health, bed fit, overhangs/bridges/floating islands, thin features, warping, stability) and that the part will hold (cantilever stress, tipping). Run after /3d-cost and before printing. Use when the user runs /print-test, or asks "will it print", "is it strong enough", "is it safe to print".
argument-hint: "[files or zip] [--filament NAME] [--load N] [--no-support] [--png out.png]"
---

# /print-test — will it print, and will the part hold?

Arguments: $ARGUMENTS

Generic: works on any STL or 3MF (also inside a zip), not tied to a specific part. It is a fast Python
simulation (`cad/print_test.py`), not a slicer run, so use it right after `/3d-cost` and before sending to the printer.

1. **Filament.** Use `--filament` / the one the user named (PLA, PETG, ASA, ABS, PC, TPU). If it is not given and
   `/3d-cost` was just run in this conversation, reuse that one. Otherwise ASK (AskUserQuestion). Never silently default.
2. Toolchain: `cad/setup.sh` (skips what is installed). The script needs `trimesh networkx shapely rtree matplotlib` (in `cad/requirements.txt`).
3. Collect the models like `/3d-cost` does (extract zips into a new empty scratchpad dir; use every `.stl` / `.3mf`; else the latest upload).
4. Run (from the repo root; one call for all files):
   ```bash
   .venv-cad/bin/python cad/print_test.py --filament <NAME> --png <scratchpad>/pt.png file1 file2 ...
   ```
   Pass through what the user gave: `--load N` (sideways force at the top, default 10 N; ask what the part really
   carries if strength matters, e.g. a stand under a plaque), `--no-support` (stricter overhang rules),
   `--angle`, `--tower`, `--fill`. Exit code 2 = at least one FAIL (not an error of the tool).
5. Reply in the user's language: per part a verdict (✅ OK / ⚠️ WARN / ❌ FAIL), then ONLY the rows that are WARN/FAIL with
   the concrete fix (use the script's advice, adapted to the part). Say what each result means in plain words; one line for
   everything that passed. Show the PNG when it exists (red = overhang that needs support).
6. If any part FAILs, say clearly "do not print yet" and what to change; offer to modify the generator
   (`cad/newborn_plaque.py` etc.) and re-run. If everything is OK/WARN: "safe to print", with the warnings to watch (brim, bed temp...).

Be honest about limits: these are screening estimates (layer-bond strength taken as 50 % of in-plane, handling load only),
and it does NOT check fits/clearances between separate parts, impact, creep, heat or slicer-specific behaviour.
