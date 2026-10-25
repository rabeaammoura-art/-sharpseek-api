# 3D ZONE TECH – Student Pack generator

Type a name + theme → tag, pencil name, 15 cm ruler and bottle tag as light multi-colour 3MF + STL.
Replaces the voxel/marching-cubes prototype: art is **vector-traced** (potrace), names come straight from the
**font outlines**, everything is plain polygons that are extruded into exact watertight solids (manifold3d).

```
pip install -r requirements.txt
python generate.py --name OSAYD --theme construction
python generate.py --pack OSAYD:construction SALLY:cat --slice     # two kids + Bambu Studio time/grams
python generate.py --list-themes
python tests/test_geometry.py && python tests/test_fusion_script.py
```

Output per kid (`out/<NAME>_<theme>/`): `<name>_<piece>.3mf` (one object, one part per colour, named by colour,
extruder = AMS slot, filament colours embedded), `<name>_<piece>.stl` (merged) + `_<colour>.stl`, a PNG preview,
`pack.json` (exact polygons + heights, used by the Fusion script) and `report.json` (sizes, volumes, checks).
3MFs are ~100–270 KB (old voxel ones: 3–14 MB, pixel-edged).

## Layer stack (as specified)
Base 1.6 mm in the outline colour over the full silhouette; each colour is then raised from 1.6 mm to its own height:
construction – black (outline) 2.2, yellow/orange 2.8, white 3.2; cat – pink (outline) 2.2, light pink 2.8, white 3.2,
black details 3.4. Pencil plate: base 10.4 mm, same raises on top (+8.8). Regions never overlap in XY (painter's
algorithm), every colour region is cleaned to ≥ 0.8 mm features (ruler ticks/numbers exempt, 0.5 mm lines).

## Pieces
| piece | size | notes |
|---|---|---|
| tag | 70 mm wide | motif above, name block below, hanging tab with Ø5 hole (≥ 2 mm wall) |
| bottle | 48 mm wide | round-dome motif, name below, Ø5 hole |
| pencil | 85 mm long, 10.4 mm plate | horizontal tunnel Ø7.7 mm along the length, **teardrop** apex up with a flat roof (roof z 9.6 → 0.8 mm wall), floor wall 1.35 mm → prints with no supports. ≥ 2 mm side walls along the whole length. **Confirm with calipers on the real pencils**; change `PENCIL_HOLE_D` in `layout.py` |
| ruler | 165 × 50 mm | 150 mm scale, 0 mark at x = 7.5 mm, a 0.5 mm line at **every** mm (generated, not traced; tests check each one), 2.0/3.0/4.2 mm tick lengths, numbers 0–15 Poppins Bold 3.2 mm |

Names use Poppins ExtraBold (`NAME_FONT` in `layout.py`; Bold for ruler numbers). Latin letters/digits only – Arabic
names would need a shaping engine (HarfBuzz) + an Arabic font: not done.
Long names shrink to fit; `generate.py` warns when letters get < 5 mm tall (e.g. 11 letters).

## Themes (`themes.py`)
Palette, heights, name rings and **crop boxes into `art/source_art_osayd_sally.png`**. `python trace.py` re-traces
those crops into `motifs/<theme>.json` (per-colour polygons, mm). To add a theme: add art, add a `THEMES` entry with
crop boxes, run `trace.py`, preview with `generate.py`. Cat is the original kitten (not a licensed character).

## Bambu Studio check (no printer yet)
`verify_slice.py` slices the 3MFs with the official H2D 0.4 profile, 0.20 mm Standard, Bambu PETG Basic, four AMS
filaments (JOD 8/kg, 0.10/kWh, 350 W). Results on 2026-10-25 (see `SLICE_RESULTS.md`): ~1 h and 14–30 g per piece, ~4 h /
~78 g per kid. **More than half of the filament is purge** (prime tower / flush, 6–11 g per piece) – reduce it in
Studio (flush multiplier, assign 2 colours per H2D nozzle, smaller tower) once the printer is here.

## Fusion 360
`fusion360/StudentPack/` – Scripts and Add-Ins → “+” → pick the folder → run → choose `out/<kid>/pack.json`.
One component per piece, one solid body per colour (named by colour), exact heights, real teardrop cut feature.
The logic is smoke-tested against a fake `adsk` API only; **run it once in Fusion** and tell me what breaks.

## Faster prints (all numbers sliced for the H2D, PETG, 0.20 mm; layer tops checked in the G-code)
Each colour change costs about 2 min (flush, wipe, nozzle wait), and every layer that holds several colours needs
them. The fix that works is to **share the changes between pieces**: `python generate.py --pack A:construction B:construction --plate`
writes one plate 3MF (all pieces of all kids of one theme, shelf-packed, prime tower parked on the right).

| plate | time | per kid |
|---|---|---|
| 4 pieces, one kid, separate plates (4 x 3MF) | ~4 h | 4 h |
| one plate, one kid | 2 h 58 | 2 h 58 |
| one plate, **two kids** (8 pieces, the most that fits) | 4 h 36 | **2 h 18** |

Smaller extras: `--set 'flush_multiplier=[0.3]'` saves ~15 min per plate (risk: colour bleed, test first); splitting the four
colours over the two H2D nozzles (`filament_maps` 1 2 1 2) saved ~14 min in the slicer but is unverified on the printer.
**Do not** change to 0.24 mm layers (white tops out at 3.08, black at 2.12) or switch the prime tower off (not verified).
The remaining time is mostly the design itself: raised colours in 8 layers (18 changes per piece) and the 12 mm pencil plates.
