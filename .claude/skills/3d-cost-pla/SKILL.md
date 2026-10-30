---
name: 3d-cost-pla
description: Same as /3d-cost but priced with PLA (no filament question). Use when the user runs /3d-cost-pla or asks for a print time/cost estimate in PLA.
argument-hint: "[files or zip] [--no-support] [--price-kg N] [--kwh-price N]"
---

# /3d-cost-pla — print time and cost in PLA

Arguments: $ARGUMENTS

Follow the `3d-cost` skill exactly, with the filament already decided:
pass `--filament "Bambu PLA Basic @BBL H2D"` to `cad/bambu_slice.py` and do not ask which filament.
If the user also passed `--filament`, theirs wins.
