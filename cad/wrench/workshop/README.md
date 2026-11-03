# Version 2: wrench + workshop

The 300 mm wrench (`cad/wrench/wrench.py`, imported unchanged) plus the workshop traced from the reference picture.
Colours (owner decision): **black, white (also the grey), orange (also the red)** = 3 filaments.

- `trace_workshop.py` -> `workshop_trace.json`: house silhouette and disc circle are hand-defined; white/orange regions come from colour masks of the picture.
- `workshop.py`: base (black) Z 0..plate+1.3 (the house overhangs the wrench above the bar), white/orange +0.8 on top. Brake disc: rotor, hub and caliper are parametric (the trace was poor there).
- `WS_STRETCH` (`--stretch`): vertical stretch of the house about its bottom line, the disc stays round. 1.0 = original proportions (house 46 mm above the bar line), 1.5 = about 69 mm. Renders of both in `out/views/` (`stretch1.0_*`, `stretch1.5_*`); STEP/STL in `out/` are stretch 1.5.
- Run: `python cad/wrench/workshop/workshop.py --stretch 1.5 --out DIR`.
- Known: details thinner than 0.7 mm are dropped; WORKSHOP lettering and gear come from the picture (not a font); caliper is a simple crescent; hooks unchanged (still to be redone, last). Not sliced, not print-tested.
