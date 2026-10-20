# CAD → Fusion 360 → 3D print pipeline

| Step | Tool | Output |
|---|---|---|
| Design (code-based CAD) | [build123d](https://build123d.readthedocs.io) | `out/<part>.step` — open in Fusion 360 (solid body, editable) |
| Mesh | build123d | `out/<part>.stl` |
| Slice | PrusaSlicer 2.7 (CLI) | `out/<part>.gcode` + filament weight & print time |
| Slice (Bambu) | Bambu Studio CLI (Flathub) + official BBL profiles | `out/bambu/<part>/out.3mf` + print time & weight |
| Preview | matplotlib | `out/<part>.png` |

In Claude Code: `/3d-cost <files or zip>` slices with Bambu Studio and reports time + cost.

## Usage

```bash
./cad/setup.sh            # once per fresh machine/session
cd cad
make                      # build + slice + preview for test_bracket
make PART=my_part         # any parts/my_part.py that defines make() -> Part
make slice PROFILE=config/other.ini
make bambu PART=my_part BAMBU_ARGS=--support   # Bambu Studio, default H2D + Bambu ASA

# any STL, any Bambu printer/process/filament profile name:
../.venv-cad/bin/python bambu_slice.py --support --printer "Bambu Lab H2D 0.4 nozzle" \
    --process "0.20mm Standard @BBL H2D" --filament "Bambu ASA @BBL H2D 0.4 nozzle" part.stl
```

New part: add `parts/<name>.py` with a `make()` function returning a build123d `Part`.
Edit `config/printer_pla_0.2mm.ini` to match your printer (bed size, temps, gcode flavor).
In Fusion 360: *File → Open → Upload* the `.step` file.
