# CAD → Fusion 360 → 3D print pipeline

| Step | Tool | Output |
|---|---|---|
| Design (code-based CAD) | [build123d](https://build123d.readthedocs.io) | `out/<part>.step` — open in Fusion 360 (solid body, editable) |
| Mesh | build123d | `out/<part>.stl` |
| Slice | PrusaSlicer 2.7 (CLI) | `out/<part>.gcode` + filament weight & print time |
| Preview | matplotlib | `out/<part>.png` |

## Usage

```bash
./cad/setup.sh            # once per fresh machine/session
cd cad
make                      # build + slice + preview for test_bracket
make PART=my_part         # any parts/my_part.py that defines make() -> Part
make slice PROFILE=config/other.ini
```

New part: add `parts/<name>.py` with a `make()` function returning a build123d `Part`.
Edit `config/printer_pla_0.2mm.ini` to match your printer (bed size, temps, gcode flavor).
In Fusion 360: *File → Open → Upload* the `.step` file.

## Projects

- **Mercedes tray**: a collapsible 3-compartment serving tray, printed in place on a Bambu H2D.
  See [MERCEDES_TRAY.md](MERCEDES_TRAY.md). The final files are in `release/mercedes_tray/`, and the
  Fusion 360 script is in `fusion/MercedesTray/`. Rebuild and re-verify everything with `make mercedes`.
