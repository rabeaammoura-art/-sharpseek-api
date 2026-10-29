#!/usr/bin/env bash
# Slice the W115 lens (RH or LH) for a Bambu Lab H2D with Bambu Studio's command line.
# Needs: flatpak com.bambulab.BambuStudio, xvfb-run, dbus (see bambu/README.md).
# Usage: bambu/slice_h2d.sh RH|LH      -> out/bambu/<side>_lens_H2D.gcode.3mf
set -euo pipefail
SIDE=${1:?RH or LH}
CAD=$(cd "$(dirname "$0")/.." && pwd)
OUT=$CAD/out/bambu; PR=$OUT/presets; STL=$CAD/out/w115_lens
mkdir -p "$OUT"
BBL="$(flatpak info --user --show-location com.bambulab.BambuStudio)/files/share/BambuStudio/profiles/BBL"
"$CAD/../.venv-cad/bin/python" "$CAD/bambu/flatten.py" "$BBL" "$PR" >/dev/null

# Supports are printed in red (filament 1). They span ~308 mm, so shift the lens until they fit
# the reach of the nozzle that red lands on (H2D: nozzle 1 reaches X 0-325, nozzle 2 X 25-350).
SHIFT=$([ "$SIDE" = RH ] && echo -5 || echo 5)
cat > "$OUT/assemble_$SIDE.json" <<JSON
{"plates": [{"plate_name": "W115 $SIDE lens", "need_arrange": false, "objects": [
  {"path": "$STL/${SIDE}_red_print.stl",   "count": 1, "filaments": [1], "assemble_index": [1], "pos_x": [$SHIFT], "pos_y": [0], "pos_z": [0]},
  {"path": "$STL/${SIDE}_clear_print.stl", "count": 1, "filaments": [2], "assemble_index": [1], "pos_x": [$SHIFT], "pos_y": [0], "pos_z": [0]},
  {"path": "$STL/${SIDE}_amber_print.stl", "count": 1, "filaments": [3], "assemble_index": [1], "pos_x": [$SHIFT], "pos_y": [0], "pos_z": [0]}]}]}
JSON

# Flatpak needs a system D-Bus; (re)start it if it isn't running (a stale socket file can be left behind).
mkdir -p /run/dbus
dbus-send --system --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetId >/dev/null 2>&1 \
  || { rm -f /run/dbus/system_bus_socket /run/dbus/pid; dbus-daemon --system --fork; }
rm -f "$OUT/result.json"
dbus-run-session -- xvfb-run -a flatpak run --filesystem=host --command=bambu-studio com.bambulab.BambuStudio \
  --debug 2 --arrange 0 --orient 0 \
  --load-settings "$PR/machine.json;$PR/process.json" \
  --load-filaments "$PR/filament_red.json;$PR/filament_clear.json;$PR/filament_amber.json" \
  --load-assemble-list "$OUT/assemble_$SIDE.json" \
  --slice 0 --outputdir "$OUT" --export-3mf "${SIDE}_lens_H2D.gcode.3mf" > "$OUT/${SIDE}_log.txt" 2>&1 || true
cp "$OUT/result.json" "$OUT/result_$SIDE.json"
python3 - "$OUT/result_$SIDE.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
if r["return_code"] != 0:
    sys.exit(f"FAILED: {r['error_string']}")
p = r["sliced_plates"][0]
print("time %.1f h (purge %.1f h), %d filament changes, filament g %s, purge waste %d g" % (
    p["total_predication"] / 3600, p["feature_type_times"]["Flush"] / 3600, p["filament_change_times"],
    [round(f["total_used_g"]) for f in p["filaments"]],
    round(sum(f["total_used_g"] - f["main_used_g"] for f in p["filaments"]))))
PY
