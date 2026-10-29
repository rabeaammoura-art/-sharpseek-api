#!/usr/bin/env bash
# Slice the keychain for a Bambu Lab H2D (PLA Basic, 4 colours) with Bambu Studio's command line.
# Usage: ./slice_h2d.sh N      N = 1 (single) or up to 12 (grid of 4 x 3)  -> out/keychain_xN.gcode.3mf
set -euo pipefail
N=${1:-1}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=$HERE/out; PR=$OUT/presets
BBL="$(flatpak info --user --show-location com.bambulab.BambuStudio)/files/share/BambuStudio/profiles/BBL"
"$HERE/../.venv-cad/bin/python" "$HERE/../cad/bambu/flatten.py" "$BBL" "$PR" "$HERE"/bambu/process_keychain.json \
  "$HERE"/bambu/filament_{brown,white,skin,pink}.json >/dev/null

# grid positions (mm) for N copies, 4 columns x 3 rows, clear of the prime tower at the back
python3 - "$N" "$OUT/assemble_x$N.json" "$OUT" <<'PY'
import json, sys
n, path, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]
xs = [40 + 70 * (i % 4) for i in range(n)]; ys = [20 + 75 * (i // 4) for i in range(n)]
objs = [{"path": f"{out}/{c}.stl", "count": n, "filaments": [k + 1], "assemble_index": list(range(1, n + 1)),
         "pos_x": xs, "pos_y": ys, "pos_z": [0] * n} for k, c in enumerate(("brown", "white", "skin", "pink"))]
json.dump({"plates": [{"plate_name": f"keychain x{n}", "need_arrange": False, "objects": objs}]}, open(path, "w"), indent=1)
PY

mkdir -p /run/dbus
dbus-send --system --dest=org.freedesktop.DBus / org.freedesktop.DBus.GetId >/dev/null 2>&1 \
  || { rm -f /run/dbus/system_bus_socket /run/dbus/pid; dbus-daemon --system --fork; }
rm -f "$OUT/result.json"
dbus-run-session -- xvfb-run -a flatpak run --filesystem=host --command=bambu-studio com.bambulab.BambuStudio \
  --debug 2 --arrange 0 --orient 0 \
  --load-settings "$PR/machine.json;$PR/process.json" \
  --load-filaments "$PR/filament_brown.json;$PR/filament_white.json;$PR/filament_skin.json;$PR/filament_pink.json" \
  --load-assemble-list "$OUT/assemble_x$N.json" \
  --slice 0 --outputdir "$OUT" --export-3mf "keychain_x$N.gcode.3mf" > "$OUT/slice_x$N.log" 2>&1 || true
python3 - "$OUT/result.json" "$N" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); n = int(sys.argv[2])
if r["return_code"] != 0:
    sys.exit(f"FAILED: {r['error_string']}")
p = r["sliced_plates"][0]
g = sum(f["total_used_g"] for f in p["filaments"]); waste = sum(f["total_used_g"] - f["main_used_g"] for f in p["filaments"])
print("x%d: %.2f h total (%.0f min each), %d filament changes, %.1f g filament (%.1f g purge waste), %.1f g per keychain"
      % (n, p["total_predication"] / 3600, p["total_predication"] / 60 / n, p["filament_change_times"], g, waste, g / n))
PY
