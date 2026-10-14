# BMW E36 modular headlight (Bi-LED inboard + red Devil Eye outboard)

Parametric pipeline built on the original, vehicle-tested *BMW E36 racing headlight intake* files.
Read **docs/REPORT.md** first: inspection results, design, validation, slicing, risks, missing dimensions.

```bash
./cad/setup.sh                                    # once (PrusaSlicer, build123d venv)
.venv-cad/bin/pip install trimesh manifold3d scipy networkx rtree shapely
# put the original files in cad/e36_headlight/input/ (see input/README.md)
cd cad/e36_headlight
PY=../../.venv-cad/bin/python
$PY -I tools/repair.py input/housing_L_orig.stl out/housing_L_repaired.stl
$PY -I tools/repair.py input/housing_R_orig.stl out/housing_R_repaired.stl
$PY -I build_housing.py      # modified L/R housing (mesh booleans)
$PY -I build_parts.py        # new parts, STEP + STL, L/R
$PY -I validate.py           # interference, aim sweep, access, removal -> out/validation.json
$PY -I slice_all.py          # PrusaSlicer, approx. H2D/ASA-CF -> out/gcode, out/slicing.json
$PY -I export_step.py        # assembly STEP of the new parts
$PY -I drawings.py           # A3 drawing sheets
$PY -I render_all.py <python-with-bpy>   # Cycles renders (pip install bpy==4.5.3 on Python 3.11)
```

Every dimension lives in `params.py`, tagged [CAD] / [DESIGN] / [ASSUMED]. After measuring the real modules,
edit the [ASSUMED] values and rerun build → validate → slice. The checks show whether the design still holds.
