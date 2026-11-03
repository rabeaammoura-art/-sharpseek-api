# Wrench key holder — stage 1: the wrench body only

Rebuilt from scratch from the owner's reference picture. The outline, the orange band and the ring were **traced from the
picture itself** (colour masks, `trace_wrench.py` -> `wrench_trace.json`), not drawn by eye. `wrench.py` builds the solid.

- Layers: outer border (3 mm), plate (to 7 mm, inset 3.4 mm), orange band (+1.4 mm), two cross screws. The 18-tooth ring is recessed (teeth in the border layer, round opening in the plate), as in the picture.
- Length is one parameter (`LENGTH_MM`, default 610 = assumed, the picture has no dimensions).
- Run: `python cad/wrench/wrench.py` (after `cad/setup.sh`). Re-trace: `python cad/wrench/trace_wrench.py <reference.jpg> cad/wrench`.
- `out/`: STEP + STL (black, orange) and lit renders (`cad/wrench_render3d.py`).
- Hooks: 5 J hooks (rounded-top plate, ball tip) traced from a 5x crop, even spacing, 10 mm thick, M3 holes through the wrench from the back (pilot 2.5 mm in the hook). Not done yet: splitting into printable parts (610 mm does not fit the bed), workshop, brake variants.
- Known approximations: the bar top edge is hidden behind the workshop (set as a straight line); jaw/ring edges follow the picture within a few px and are smoothed; ring teeth count/radii are measured by eye on a zoomed crop.
