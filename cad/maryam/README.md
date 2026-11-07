# Maryam plaque (personal gift, NOT for sale) - private build scripts

Built from the owner's GPT picture (a Sanrio character): the **picture, the segmentation arrays and all outputs stay OUT of git** (public repo).
Only these scripts are committed; run them in a scratch dir that holds the picture as `ref.png` (1450 x 1085).

1. `seg.py` - colour segmentation of the picture -> `lab.npy`, `sil.npy`, `lab.png` (labels: white / light pink / dark pink / yellow).
2. `build_flat6.py` - flat 2D design (280 x 280 plate): pink = light + dark merged, Kitty and bow traced, decor drawn parametric from measured px and mirrored,
   name / labels / values in the real fonts, icons from the generator -> `G6.pkl`, `flat_preview6.png`, `flat_only6.png`.
3. `build_lit.py <outdir>` - backlit version with the `glow_cap` method (opaque white base with openings, translucent pink / yellow caps, frame without
   opening, 2 nut pockets) -> `maryam_{base,main,accent}.stl`, `maryam_lit_280.3mf` (tower at x = 287). Needs `G6.pkl`.
Pink level 1 (fills) 1.2 mm, level 2 (frame, Kitty lines, bow creases, text, icons) 1.8 mm, yellow 1.2 mm on a 2.4 mm base.
Paths in the scripts are those of the cloud scratch dir: adjust `sys.path` to `cad/`. Box + kickstand: `cad/print_files/glow_cap/glowcap_all_280.3mf`.
