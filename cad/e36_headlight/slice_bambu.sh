#!/bin/sh
# Slice with the OFFICIAL Bambu Studio H2D + Bambu ASA-CF profiles (Bambu Studio 2.08 from Flathub, run headless).
# One-time setup (as root in a container without a flatpak session):
#   apt-get install -y flatpak xvfb && flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
#   flatpak install --user -y flathub com.bambulab.BambuStudio
#   ln -s ~/.local/share/flatpak/app/com.bambulab.BambuStudio/current/active/files /app   # CLI expects /app resources
# Usage: ./slice_bambu.sh <bambu-launcher>   (launcher = wrapper running /app/bin/bambu-studio with the GNOME 50 runtime libs)
set -e
BAMBU=$1; B=out/bambu; PY=../../.venv-cad/bin/python; A=/app/share/BambuStudio/profiles/BBL
mkdir -p $B/housing $B/small
$PY -I tools/bambu_flatten.py "$A" machine "Bambu Lab H2D 0.4 nozzle" $B/machine.json
$PY -I tools/bambu_flatten.py "$A" filament "Bambu ASA-CF @BBL H2D 0.4 nozzle" $B/filament.json
# 0.20 mm Standard; only internal changes: 3 walls, 12 % gyroid. Slim trees keep supports inside the right nozzle's
# area (X 25-350); no brim / prime tower (single filament; the housing is 317.5 mm wide at 16 deg).
$PY -I tools/bambu_flatten.py "$A" process "0.20mm Standard @BBL H2D" $B/process.json wall_loops=3 'sparse_infill_density=12%' \
  sparse_infill_pattern=gyroid enable_support=1 'support_type=tree(auto)' support_style=tree_slim filament_map_mode=Manual \
  'filament_map=["2"]' 'curr_bed_type=Textured PEI Plate' brim_type=no_brim enable_prime_tower=0
$PY -I - <<'PYEOF'
import numpy as np, trimesh
h = trimesh.load("out/housing_L_mod.stl"); a = np.radians(16); T = np.eye(4); T[:2, :2] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
h.apply_transform(T); h.apply_translation(-h.bounds[0]); e = h.extents
h.apply_translation([187.5 - e[0] / 2, 160 - e[1] / 2, 0]); h.export("out/bambu/housing_placed.stl")      # centred on right nozzle
R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
for n, cx in (("projector_carrier", 110), ("devil_clamp", 250)):
    m = trimesh.load(f"out/parts/{n}_L.stl"); T = np.eye(4); T[:3, :3] = R; m.apply_transform(T)
    m.apply_translation([cx - m.bounds.mean(0)[0], 160 - m.bounds.mean(0)[1], -m.bounds[0][2]]); m.export(f"out/bambu/{n}_placed.stl")
PYEOF
xvfb-run -a $BAMBU --slice 0 --arrange 0 --orient 0 --load-settings "$B/machine.json;$B/process.json" --load-filaments "$B/filament.json" \
  --export-3mf housing.3mf --outputdir $B/housing $B/housing_placed.stl
xvfb-run -a $BAMBU --slice 0 --arrange 0 --orient 0 --load-settings "$B/machine.json;$B/process.json" --load-filaments "$B/filament.json" \
  --export-3mf small.3mf --outputdir $B/small $B/projector_carrier_placed.stl $B/devil_clamp_placed.stl
grep -m2 -E "^; (model printing time|total filament weight)" $B/housing/plate_1.gcode $B/small/plate_1.gcode
