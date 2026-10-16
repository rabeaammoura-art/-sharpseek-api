# CAD → Fusion 360 → 3D print pipeline

| Step | Tool | Output |
|---|---|---|
| Design (code-based CAD) | [build123d](https://build123d.readthedocs.io) | `out/<part>.step` — open in Fusion 360 (solid body, editable) |
| Mesh | build123d | `out/<part>.stl` + `out/<part>.3mf` (import into Bambu Studio) |
| Check | PrusaSlicer 2.7 (CLI) | fit on bed + filament weight & print time (estimate only) |
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
Default profile: `config/bambu_h2d_asa_0.2mm.ini` — Bambu Lab H2D, ASA, 0.2mm layers, bed 325x320x325.
`build.py` warns if a part does not fit that volume.

**Printing on the H2D:** the PrusaSlicer G-code is for estimates only and will not run on a Bambu printer.
Import `out/<part>.3mf` (or `.step`) into Bambu Studio, pick the H2D + ASA profile there, and print.
ASA shrinks ~0.5%: leave clearance on mating features (fit holes/clips ~0.2–0.3mm oversize).
In Fusion 360: *File → Open → Upload* the `.step` file.
