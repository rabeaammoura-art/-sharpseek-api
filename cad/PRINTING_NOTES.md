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
