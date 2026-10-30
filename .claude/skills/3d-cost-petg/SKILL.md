---
name: 3d-cost-petg
description: Same as /3d-cost but priced with PETG (no filament question). Use when the user runs /3d-cost-petg or asks for a print time/cost estimate in PETG.
argument-hint: "[files or zip] [--no-support] [--price-kg N] [--kwh-price N]"
---

# /3d-cost-petg — print time and cost in PETG

Arguments: $ARGUMENTS

Follow the `3d-cost` skill exactly, with the filament already decided:
pass `--filament "Bambu PETG Basic @BBL H2D 0.4 nozzle"` to `cad/bambu_slice.py` and do not ask which filament.
If the user also passed `--filament`, theirs wins.
