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

## Floating-ball spiral illusion

`designs/floating_ball.py` (all dimensions are constants at the top). Parts: `floating_base`, `floating_rotor`, `floating_ring`. `floating_assembly` is a preview only, not for printing.

Bought parts: one 608 bearing (8×22×7), one 40 mm ping-pong ball, some coins or washers to weigh down the base.

| Part | Supports | PLA | Time (0.2 mm) |
|---|---|---|---|
| base | none | ~25 g | ~2h15 |
| rotor | organic/tree (for the helix) | ~27 g | ~2h55 |
| ring | none | ~11 g | ~1h05 |

Assembly: press the bearing into the rotor hub from below → slide onto the base axle → glue the ring onto the top pin → glue the ball into the saddle so it sits dead centre. Flick it to spin.
