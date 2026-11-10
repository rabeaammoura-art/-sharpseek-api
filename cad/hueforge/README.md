# ZT-Forge: image -> layered filament painting (HueForge-style)

Our own tool (no HueForge licence needed). Brought in from a chat session of 2026-11-09 (handoff zip).

```
python cad/hueforge/zt_forge.py IMAGE OUT --px 0.3 --mode color --smooth 0 --base 0.64 --top 2.4 \
  --filaments '[["#111111",0.4],["#1E4FB4",2.5],["#D4A017",4],["#F2F2F2",5]]'
python cad/hueforge/check_stl.py OUT.stl
```

Outputs `OUT.stl` (watertight heightfield), `OUT_preview.png` (simulated print), `OUT_swaps.txt` (layers to swap filament).

* Filaments are `[hex, TD]`, ordered dark -> light. Seen colour = Beer-Lambert stack, `a = 1 - 10^(-t / (TD * 0.2))`.
* `--mode luma`: height from lightness (classic). `--mode color`: per pixel, the height whose stacked colour is nearest in Lab
  (keeps a gold area gold when it has the same lightness as a white-lit area).
* Print: 0.08 mm layers, 0.16 mm first layer, 100 % infill, no supports, never scale Z (X/Y together only). All filaments the same
  material (all PLA).
* TD values of our own filaments are **estimates** until a printed sample is photographed and fitted.
* Images, STLs and previews stay out of git (`cad/out/`); only use images we may sell (customer's / owner's / own AI images).
