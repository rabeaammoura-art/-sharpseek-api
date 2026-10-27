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
