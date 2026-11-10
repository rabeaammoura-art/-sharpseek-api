# H2D slicing notes (measured with the Bambu Studio CLI) — for Claude

- Nozzle areas in the profile: left x 0-325, right x 25-350, y 0-320. **Effective** limit is smaller: a 14 mm prime tower
  works at x=290 (ends 304) but fails at x=306 (ends 320) on the left nozzle ("G-code in unprintable area").
  On the right nozzle a tower at x=334-348 is rejected ("outside the printable area").
- => **A 300 mm multi-colour plate + prime tower does not fit.** 280 mm + 14 mm tower fits (plate x 3-283, tower x=288).
  Measured 280 mm, PETG (AD-PETG white + 3 translucent), tower on: 5h30m, 204 g, 1.52 JOD.
- A narrow tower (14 mm) costs ~+12 min vs a 40 mm tower on the 150 mm plate (2h09 vs 1h55).
- Slices **without** a prime tower are unreliable for multi-colour (one run gave 21 million g). Always pass `--tower-x`.
- Useful `bambu_slice.py` flags: `--tower-x/--tower-y/--tower-width`, `--nozzle 1|2`. For 3MF input the wrapper sets
  all colours on one nozzle (Manual map), skirt off, brim off (they leave the bed beside a big plate), tower brim 0.
- JSON keys of the generator: `plate_x`, `plate_y` position the plate on the bed (default 162.5, 160).
- The GUI may place the tower differently from the CLI: re-check in Bambu Studio when the printer arrives.

- **Decision: largest size is now 280 mm** (300 + tower does not fit). Sizes 150 / 200 / 280. Rails need a frame band >= ~11 mm (280+).

## Estimates are noisy (measured)
- The same multi-colour 3MF sliced twice with identical flags gave 2h47m/62.0 g and 2h36m/59.8 g; an earlier run of the same
  geometry gave 2h02m/56.7 g. Treat multi-colour times as **ranges of about +-20 %**, not exact numbers. Single-colour parts are stable.
- Bambu Studio (GUI) is the reference once the printer is there.
- The generated 3MF now carries 4 filaments + slot colours + prime tower (templates `config/bambu_project_4fil_{pla,petg}.config`).
  Sliced directly with only its embedded settings (CLI): 150 mm standard, PLA, 1h49m / 62.5 g, no warnings.
- Windows: `bambu_slice.py` works with the installed Bambu Studio (commit eef8ef5 from the laptop session): 150 mm test 2h07m / 60.6 g vs ~2h09m on Linux.

## Largest coloured plaque (measured, CLI)
- One nozzle reaches about x=305 for the prime tower. The generator now places the plaque 4 mm from the left edge and the
  tower 3 mm right of it, as wide as the room allows (8-14 mm). `TOWER_LIMIT = 305` in `newborn_plaque.py`.
- 285 mm (tower 12 mm): 4h24m / 199.5 g (PLA). 290 mm (tower 8 mm): 4h37m / 207.6 g (PLA). 300 mm: no room (tried in Bambu Studio, failed).
- Bigger coloured plaques would need: two half-plates joined, or a single-colour print (no tower).

- **100 % infill through the CLI:** `--set sparse_infill_density=100%` alone fails ("Invalid parameter value(s)", 0h00m); add `--set sparse_infill_pattern=zig-zag`.
