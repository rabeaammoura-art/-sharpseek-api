---
name: 3d-cost-asa
description: Same as /3d-cost but priced with ASA (no filament question). Use when the user runs /3d-cost-asa or asks for a print time/cost estimate in ASA.
argument-hint: "[files or zip] [--no-support] [--price-kg N] [--kwh-price N]"
---

# /3d-cost-asa — print time and cost in ASA

Arguments: $ARGUMENTS

Follow the `3d-cost` skill exactly, with the filament already decided:
pass `--filament "Bambu ASA @BBL H2D 0.4 nozzle"` to `cad/bambu_slice.py` and do not ask which filament.
If the user also passed `--filament`, theirs wins.
