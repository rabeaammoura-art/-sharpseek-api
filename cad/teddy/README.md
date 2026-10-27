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

Smooth heart edges (fix_manus.py): outline = Manus silhouette, low-pass + morphological open/close (radius >= 6 mm, so tip, cleft and
lobes are all rounded curves), edge between the dome and the side wall rounded with a 4 mm fillet (wall stays 2 mm around it),
dome surface smoothed (1.6 mm). Parameters OUTLINE_R, EDGE_R, SMOOTH_MM at the top of the script.
Final print numbers (Bambu Studio, H2D, PLA, 0.20 mm): body lightning 10% + 3 walls 8h04m / 235 g;
lid, rim on the bed and dome up, supports on: 2h00m / 46 g (dome down: 1h34m / 40 g but supports would touch the visible face).
