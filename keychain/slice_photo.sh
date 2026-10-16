#!/usr/bin/env bash
# Slice a photo keychain (from photo_keychain.py) for a Bambu Lab H2D, PLA Basic.
# Usage: ./slice_photo.sh <keychain out dir> <N copies> <colour> [colour ...]
#   colours = the STL names in that dir, in AMS order, e.g. black brown skin white pink
set -euo pipefail
DIR=$(cd "$1" && pwd); N=$2; shift 2; COLS=("$@")
HERE=$(cd "$(dirname "$0")" && pwd); PR=$DIR/presets
BBL="$(flatpak info --user --show-location com.bambulab.BambuStudio)/files/share/BambuStudio/profiles/BBL"
FIL=(); for c in "${COLS[@]}"; do FIL+=("$HERE/bambu/filament_$c.json"); done
"$HERE/../.venv-cad/bin/python" "$HERE/../cad/bambu/flatten.py" "$BBL" "$PR" "$HERE/bambu/${PROCESS:-process_keychain}.json" "${FIL[@]}" >/dev/null
python3 - "$N" "$DIR" "${COLS[@]}" <<'PY'
import json, sys
n, d, cols = int(sys.argv[1]), sys.argv[2], sys.argv[3:]
xs = [30 + 80 * (i % 4) for i in range(n)]; ys = [20 + 78 * (i // 4) for i in range(n)]
objs = [{"path": f"{d}/{c}.stl", "count": n, "filaments": [k + 1], "assemble_index": list(range(1, n + 1)),
         "pos_x": xs, "pos_y": ys, "pos_z": [0] * n} for k, c in enumerate(cols)]
json.dump({"plates": [{"plate_name": f"keychain x{n}", "need_arrange": False, "objects": objs}]}, open(f"{d}/assemble_x{n}.json", "w"), indent=1)
PY
mkdir -p /run/dbus
dbus-send --system --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetId >/dev/null 2>&1 \
  || { rm -f /run/dbus/system_bus_socket /run/dbus/pid; dbus-daemon --system --fork; }
LOADF=""; for c in "${COLS[@]}"; do LOADF+="${LOADF:+;}$PR/filament_$c.json"; done
rm -f "$DIR/result.json"
dbus-run-session -- xvfb-run -a flatpak run --filesystem=host --command=bambu-studio com.bambulab.BambuStudio \
  --debug 2 --arrange 0 --orient 0 --load-settings "$PR/machine.json;$PR/process.json" \
  --load-filaments "$LOADF" --load-assemble-list "$DIR/assemble_x$N.json" \
  --slice 0 --outputdir "$DIR" --export-3mf "keychain_x$N.gcode.3mf" > "$DIR/slice_x$N.log" 2>&1 || true
python3 - "$DIR/result.json" "$N" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); n = int(sys.argv[2])
if r["return_code"] != 0:
    sys.exit(f"FAILED: {r['error_string']}")
p = r["sliced_plates"][0]
g = sum(f["total_used_g"] for f in p["filaments"]); waste = sum(f["total_used_g"] - f["main_used_g"] for f in p["filaments"])
print("x%d: %.2f h (%.0f min each), %d filament changes, %.1f g (%.1f g purge), %.1f g each"
      % (n, p["total_predication"] / 3600, p["total_predication"] / 60 / n, p["filament_change_times"], g, waste, g / n))
PY
