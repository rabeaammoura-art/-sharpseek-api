"""Put the "clearer TPU" settings into a Bambu 3MF (owner 2026-11-23: hide / soften the TPU fill lines).

    python cad/bambu_slice.py MODEL.3mf --filament "Bambu TPU 95A HF @BBL H2D 0.4 nozzle" --filament "Bambu PLA Basic @BBL H2D" ... \
        --nozzle-map 2,1,1 --tower-x 250 --tower-y 140 --tower-width 30 --set sparse_infill_density=100% \
        --set sparse_infill_pattern=alignedrectilinear --set top_surface_pattern=monotonicline \
        --set bottom_surface_pattern=monotonicline --set ironing_type=top --set ironing_flow=10% --set ironing_speed=20 --price-kg 1
    python cad/clear_tpu_settings.py cad/out/bambu/MODEL/input.3mf OUT.3mf --colours "#E8F1F5,#C8102E,#1F5FA8"

Process part (from --set): 100 % aligned rectilinear (all lines one direction = less light scatter), monotonic line
top/bottom, ironing of the top face. TPU (slot 1, all its extruder-variant entries): +10 C, flow x1.05, fan 30-40 %,
max volumetric speed x0.65 (better fused lines, fewer air gaps). Print face down on a smooth plate.
"""
import argparse, json, zipfile

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst"); ap.add_argument("--colours")
a = ap.parse_args()
z = zipfile.ZipFile(a.src)
c = json.loads(z.read("Metadata/project_settings.config"))
variants = c["filament_extruder_variant"]
n_tpu = len(variants) - (len(c["filament_settings_id"]) - 1)          # TPU = slot 1 has one entry per variant
for i in range(n_tpu):
    for k in ("nozzle_temperature", "nozzle_temperature_initial_layer"):
        c[k][i] = str(int(c[k][i]) + 10)
    c["filament_flow_ratio"][i] = "%.2f" % (float(c["filament_flow_ratio"][i]) * 1.05)
    c["filament_max_volumetric_speed"][i] = str(round(float(c["filament_max_volumetric_speed"][i]) * 0.65, 1))
c["fan_max_speed"][0], c["fan_min_speed"][0] = "40", "30"
if a.colours:
    c["filament_colour"] = a.colours.split(",")
with zipfile.ZipFile(a.dst, "w", zipfile.ZIP_DEFLATED) as o:
    for it in z.infolist():
        d = z.read(it.filename)
        if it.filename == "Metadata/project_settings.config":
            d = json.dumps(c, indent=4, ensure_ascii=False).encode("utf-8")
        o.writestr(it, d)
print("TPU entries changed:", n_tpu, "->", a.dst)
