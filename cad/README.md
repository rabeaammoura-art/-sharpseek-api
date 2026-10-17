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

## Spinning-spiral illusions

`designs/spiral.py` holds the shared base, rotor and top ring. Anything rotationally symmetric glued on the spin axis looks still while the spiral sweeps through it, so it seems to float.

Bought parts for every variant: one 608 bearing (8×22×7) and some coins or washers to weigh down the base. The rotor's helix needs organic/tree supports; every other part prints without.

### Floating flame (`designs/floating_flame.py`)

A glowing candle flame hovering inside the spiral. A standard 38 mm LED tea light (CR2032, built-in flicker) sits inside the flame and spins with it, so no wires cross the bearing.

| Part | Filament | PLA/PETG | Time (0.2 mm) |
|---|---|---|---|
| flame_base | any (black) | ~31 g | ~2h50 |
| flame_rotor | any (black) | ~37 g | ~3h55 |
| flame_ring | any (black) | ~11 g | ~1h00 |
| flame_shell | translucent orange/natural | ~13 g | ~1h20 |
| flame_cup | translucent orange | ~12 g | ~1h10 |

Assembly: press the bearing into the rotor hub from below → slide onto the base axle → glue the ring onto the top pin → glue the shell into the rotor's saddle → switch the tea light on, drop it into the cup and push the cup into the shell. `flame_assembly` is a preview only. Measure your tea light first: `TEALIGHT_*` at the top of the file.

### Floating ball (`designs/floating_ball.py`)

The original: a 40 mm ping-pong ball glued into the saddle. Parts: `floating_base`, `floating_rotor`, `floating_ring` (`floating_assembly` is a preview).
