# Teddy + heart lithophane lamp (v4)

Built from the original STLs (`teddy_rear_heart_LED.stl`, `heart_front_lithophane.stl`) by `build_v4.py`:

    python build_v4.py <dir with the two original STLs> <photo.jpg> out/

What v4 does
- **Removable lithophane**: 0.25 mm clearance, fixed teddy flange (7.5 x 4 mm, inside the pocket wall) + white C-lip on the
  lithophane (bridge over the flange, skirt around its inner end) = labyrinth against light leaks; 4 snap tabs
  (barbs hook behind the flange, 0.4 mm engagement); finger notch in the ring lip at the cleft. Straight pull toward the viewer.
- **Hollow body**: 2.0 mm wall, vertical pillars (dia 6, pitch 28 mm) + diamond beams (45 deg, every 40 mm) inside, 3 mm walls
  around the LED recess / pocket / cable path, 2 mm vent hole in the base trench. Set sparse infill to 0%.
- **Cable**: sealed back; dia 12 mm channel to the base and a 12 x 5 mm open-bottom trench to the rear edge.
- Smooth fillet around the heart ring, micro-slits filled, new photo relief, smile, paw pads (from v3).

Files: `out/teddy_rear_heart_LED_v4.stl`, `out/heart_front_lithophane_v4.stl`, previews `out/preview_*.png`, `out/lithophane_photo.jpg`.
`verify_v4.py` = read-only checks; `slice_check.py` = Bambu Studio slicing check (H2D, PLA, 5 wall loops, 0% infill).
Older scripts (`run_*.py`, `litho.py`, `v4_lattice_study.py`) are earlier attempts / the lattice design study.

## Chest-heart version (Manus files, fixed here) - out/manus_fix/
`fix_manus.py <original 200 mm bear stl> <manus lid v2 stl> out/manus_fix/` rebuilds from the original bear (never modified):
pocket = smooth heart prism (0.3 mm side clearance, flat floor y=78), LED recess 33 x 7 mm, 12 mm cable channel starting
3 mm behind the floor, 12 x 5 mm trench to the rear edge, 2 pins; lid = exact Manus front surface + uniform 2.0 mm shell,
rim on the floor plane, 2 bosses with 6 mm bores. Files: `teddy_body_chest_led_v3.stl`, `chest_heart_lid_v3.stl`.
Print weight (Bambu Studio, H2D, PLA, 0.20 mm, tree supports): body 15% default 12h46m/473 g; gyroid 8% 10h15m/334 g;
lightning 10% 7h11m/192 g; lightning 10% + 3 walls 8h01m/235 g. `slice_variants.py` reproduces these (env DENS, PAT, WALLS, PROC).

Chest-heart version (fix_manus.py, outputs in out/manus_fix/*_v5.stl):
- outline = geometric heart (two R22 lobes, straight tangent sides, tip fillet 6 mm, cleft fillet 5 mm), 85 mm wide, z 26.5..94;
  the dome is Manus' front surface, low-passed (3.5 mm), the edge to the side wall is a 4 mm fillet and the shell stays 2 mm;
- rebuild_rim(): the pocket wall cuts the bear's pebbled surface at grazing angles (knife edges, thin skins, a rim of beads).
  In an 8 mm band around the pocket the material thinner than 2.6 mm is opened away, the surface is smoothed (0.9 mm) and
  re-meshed and swapped in for the old band; the pocket wall plane is the cutting plane, so the wall stays exact and the rim is
  one clean line (before: 9 % of the pocket wall was thinner than 1 mm, now 0; thinnest wall around the pocket 2.3 mm);
- save() reloads the STL and repairs the few seam edges that a float32 round trip would break;
- checks: watertight single volume, seated overlap 0, lid pulls out toward -Y with 0 overlap to 25 mm, back of the torso unchanged.
Bambu Studio, H2D, PLA, 0.20 mm, supports on, lightning 10 % + 3 walls: body 7h47m / 234 g, lid (rim on the bed) 1h56m / 46 g.

v6 (the user's own heart): `python fix_manus.py <bear> <manus lid v2> out/manus_fix/ input/heart_sketch_mm.dxf` builds
`*_v6.stl` with the outline from the user's Fusion sketch (input/heart_sketch_mm.dxf, 75.9 x 65.2 mm, x 46.1..122.0, z 27.3..92.5)
instead of the geometric heart. Same checks as v5 pass (single watertight volume, overlap 0, pulls out to 25 mm, back unchanged,
thinnest wall next to the pocket 2.4 mm). Bambu Studio, PLA, 0.20 mm, lightning 10 % + 3 walls: body 8h03m / 237 g,
lid rim on the bed 1h49m / 44 g.

v7 (lithophane): `python fix_manus.py <bear> <manus lid v2> out/manus_fix/ input/heart_sketch_mm.dxf input/family_photo.jpg` builds `*_v7.stl`.
The photo (autocontrast, mapped to the outline's bounding box) becomes the wall thickness: 0.8 mm (bright) .. 3.2 mm (dark), fading into the plain
2 mm wall within 2..5 mm of the outline. The relief is on the OUTSIDE of the front wall (the lid is printed rim down, so the relief faces up and
needs no supports); the inner ceiling is a smooth dome. The pins moved to the rim, (52,70) and (116,70), with bosses that start at y = 62 and
never touch the front wall, so they cast no dark spots on the picture. `lithophane_backlit_preview.png` simulates the back-lit look.
Bambu Studio, PLA, 0.20 mm, lightning 10 % + 3 walls: body 7h57m / 235 g, lid (rim down, supports on) 2h03m / 40 g.
Print the lid in WHITE or natural PLA; the LED must be diffuse (warm white) and the picture must be test-printed once before the final lid.
