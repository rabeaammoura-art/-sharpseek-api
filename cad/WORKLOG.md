# Work log (shared by cloud and laptop sessions)

Every session — cloud or laptop — appends a short entry here at the end of each task and commits it, so the others can
read what happened. Newest first. Keep it factual and short; this repo is public (no prices, no private data).

Entry format: `## YYYY-MM-DD (cloud|laptop) — title` then 2-5 bullets: what was done, results, what is left.

## 2026-11-26 (cloud) — rose coaster: black roses
- Owner: roses black. `--rose-black`: open roses go to the letter's slot (black), clear petal lines kept, buds stay crimson. print_test 0 problems, 0 crossed layers, CLI 2h02m / 33 g. `coaster_R_rose_black.3mf` sent. Crimson is now only the 7 buds: if they go black too, the slot (and its colour swaps) can be dropped.

## 2026-11-26 (cloud) — rose coaster: sharp 1254 px rose (owner), clear lines
- The screenshot rose (185 px) printed jagged; owner sent a sharp 1254 px bold rose (thick even white lines, not in git). `rose_template` for big pictures: up=1, smooth 1.0, closing radius 3 % of the width, no sepal trim. Clear lines grown only to ~0.7 mm (+0.15 per side; +0.25 cut the petals into bits), crimson opening 0.2.
- Flat true-colour previews (STL sections) instead of the shadowed render (owner asked what the grey shadows were: render lamp only). print_test 0 problems, Textured PEI, 0 crossed layers, CLI 2h02m / 33 g. `coaster_R_rose_v2.3mf` sent.

## 2026-11-26 (cloud) — rose coaster v-final: bold stencil rose, CLEAR petal lines
- Owner picked (on my advice) the bold "Rose Black And White Vector" stencil (fewer, thicker white lines; screenshot crop, not in git) and wants the white lines CLEAR, R black. `--rose-pic head.png --rose-head-only --clear-lines`: picture padded white (a shape touching the crop edge did not close -> garbage), sepals/stem stub under the bloom cut off (looked like drips).
- print_test 0 problems, Textured PEI (owner), ensure none, purge 50, 0 crossed layers, CLI 2h02m / 33 g. `coaster_R_rose_clear.3mf` sent. Stock image licence not checked (owner told).

## 2026-11-26 (cloud) — rose coaster with the stencil rose head (owner's pick)
- Owner disliked the drawn spiral rose; marked the HEAD of a black rose stencil picture (300 px, not in git). `coaster_picture.py --rose-pic PIC [--rose-scale 1.7]`: head cut above the stem neck, all pieces kept, closed 6 px -> silhouette (crimson), white gaps -> black petal lines (thin ones grown to ~0.7 mm); each of the 4 roses replaced at 1.7x its size (~17 mm; at 13 mm the black swamped the petals); leaves/stems cleared 0.6 mm around.
- print_test 0 problems, file settings: Textured PEI (owner), ensure none, purge 50; 0 crossed layers, CLI 2h01m / 33 g. One CLI run gave a bogus 64h55m / 2941 g again (known glitch, re-run fine). `coaster_R_roses_stencil.3mf` sent.

## 2026-11-26 (cloud) — back to OUR rose coaster; clarity values now written into every file
- Owner: stop fixing the other file, work on ours (`coaster_R_roses_black`). Found our 3MFs also carried ensure_vertical_shell_thickness = enabled (CLI prep default; our CLI checks used --set, the GUI reads the file). `clear_tpu_settings.py` now writes all clarity process values into the file (aligned rectilinear everywhere, 1/1 shells, thickness 0, ensure none, ironing). `coaster_R_roses_black_v3.3mf` sent: Textured PEI kept (owner), 0 crossed layers from its own settings, CLI 1h59m.
- Older files sent before today have ensure = enabled inside: re-run them through clear_tpu_settings if reprinted.

## 2026-11-26 (cloud) — owner's rose coaster: print photo diagnosis, v4
- Owner: colours not clear vs our files. Measured: in his file 11 % of the black ink is < 0.7 mm (8 % < 0.5), ours 0 %. Printed photo (his v2): crossed grid visible (ensure_vertical_shell_thickness was on), fuzzy/lacy black edges and a hollow-looking R (thin strokes + Textured PEI frosting the 0.4 mm face), leaves came out black (olive slot probably mapped to a black spool).
- v4 (chat only): thin ink parts thickened (+0.18 mm on the thin bits only, black thin share 11 -> 5 %), rounded TPU, ensure_vertical none, purge matrix 32, Textured PEI kept as asked; slices, 0 crossed layers, CLI 1h53m. Advised Smooth PEI as the biggest clarity gain.

## 2026-11-26 (cloud) — owner's rose coaster file brought to our method (v3)
- Compared his `coaster_rania_rose_black_v2.3mf` with our method: same layers 0.4/0.6/2.0, face down, clear settings; differences: sharp TPU edge, ensure_vertical_shell_thickness enabled, Textured PEI. Owner: keep Textured PEI, fix the rest.
- v3 (chat only): TPU body rebuilt = `coaster_text.rounded_disc()` (r 0.6) minus his unchanged ink parts; ensure_vertical_shell_thickness none; purge matrix 32. Slices fine, 0 crossed layers, CLI 1h52m. The TPU mesh is watertight as written in the 3MF; an STL round trip (vertex merge) opens it, so print_test on STLs flags it.
- Owner also asked if a black rose stencil picture (300 px) prints: yes at 55-60 mm tall (40 mm: 17 gaps < 0.7 mm); a bigger/SVG version would be cleaner. Waiting for what goes with it.

## 2026-11-26 (cloud) — GUI error "Purge volumes matrix do not match to the correct size!"
- Correction: the owner's screenshot was HIS other file `coaster_rania_rose_black_v2.3mf` (laurel + roses ring, 4 filaments, made elsewhere, not in git) with the same cause (16 entries, needs 32). New `clear_tpu_settings.py --purge-only`: changes only flush_volumes_matrix + flush_multiplier (checked: nothing else differs). Fixed file sent in chat, CLI slices it (1h53m).
- Owner opened the 5-filament rose coaster in Studio: error. The 3MF had a 5x5 purge matrix; the H2D GUI wants one per nozzle (2 x n x n) and 2 flush multipliers. `clear_tpu_settings.py` now writes 2 n n entries, vector 2 n, multiplier x2. `coaster_R_roses_black_v2.3mf` sent (CLI still slices it: 1h59m). Owner's screenshot shows the Textured PEI plate selected: use the smooth plate for a glossy face.

## 2026-11-26 (cloud) — rose coaster: black R + black rose spirals
- Owner: spirals black (not clear) and the R black too. `coaster_picture.py --white --black`: spirals added to the letter's slot, colour #141414; ink outlines cleaned (buffer 0.01 + simplify) because the merged black shape was not a closed volume. print_test 0 problems, 0 crossed layers, CLI 1h57m / 30.7 g. `coaster_R_roses_black.3mf` sent in chat.

## 2026-11-26 (cloud) — rose coaster: roses must look like damask roses (جوري)
- Solid rose blobs rejected. Tracing the picture's dark swirl bands (~1 mm in a ~10 mm rose) ate the roses; arcs + spiral looked like smiley faces. Final: each open rose (4, R 4.6-5.2 mm) gets one drawn spiral (1.75 turns) cut as a 0.7 mm CLEAR line, ~1.2 mm crimson bands. Buds unchanged.
- print_test 0 problems, 0 crossed layers, CLI 1h57m / 30.5 g. `coaster_R_roses_jouri.3mf` sent in chat.

## 2026-11-26 (cloud) — R coaster with a rose wreath (owner's new flat picture)
- Owner's picture on WHITE (no circle): purple serif R, crimson roses + buds, olive leaves, brown stems. `coaster_picture.py --white`: nearest-palette colour per pixel (rose swirls -> crimson, so roses print as solid shapes), whole design fitted inside r 43.5 mm (69 mm wide), stems thickened/smoothed like before. 5 slots: TPU + purple, crimson #B0123F, olive, brown.
- print_test 0 problems, 0 crossed layers, CLI 1h56m / 30.5 g. `coaster_R_roses_final.3mf` sent in chat (picture not in git).

## 2026-11-24 (cloud) — check of a downloaded LED-strip sign ("Sally", 5 mm strip)
- Owner's downloaded 3MF (not in git): 174 x 111 x 10 mm, 2 mm back + 8 mm outline walls (~1.2-1.8 mm) = open channel for a 5 mm LED strip. Two separate bodies ("S" and "ally"), plain 3MF centred at 0,0 (Bambu CLI refused it; sliced as STL).
- print_test 0 problems. CLI 0.20 mm: PLA 59 min / 38 g, PETG 1h00 / 37 g (GUI usually longer). Price sheet missing in this session.
- Scaled to 250 mm wide in X/Y only (250 x 159 x 10, walls ~1.7-2.6 mm, height kept for the strip): print_test 0, CLI PLA 1h55m / 74 g. Sent `sally_250.3mf` in chat.
- Owner: channel must stay as it was. New `cad/scale_keep_channel.py` (medial axis, scaled centreline, original local widths, wall 1.6 re-offset): `sally_250_channel.3mf` 250 x 159 x 10, channel widths 7.2-11.6 (orig 7.4-11.5), print_test 0, CLI PLA 1h25m / 59 g. Sent in chat.
- Owner wants a constant 5.2 mm channel (neon style): script arg 4 = constant width. `sally_250_ch52.3mf` 250 x 160 x 10, channel 5.2, wall 1.6, print_test 0, CLI PLA 1h20m / 52 g. Waiting for his OK.
- Owner's printytron files: v2 identical to v1 (md5); 7021 = 220 mm, channel still 7-13; c07e (after my prompt) = 249 x 166 x 10, monoline, channel 5.2 constant, wall 1.6, one body; print_test 0 (as 3MF centred at 0 it gave a false overhang, as STL clean), CLI PLA 1h25m / 55 g. Its 'a' looks like an 'e' (reads Selly) - told the owner.
- printytron aa66 'Neon 250': 250 x 157 x 10, original letters scaled, channel back to 6-12 (median 9), S separate again, narrow spot at the y joint; print_test 0, CLI 1h27m / 60 g. Not 5.2.
- Drew S-to-a cursive swash (loop + 5.2 channel under the S); owner chose to keep the S separate. Final = `sally_250_ch52.3mf` (sent with 3D + top images). Left: wire hole if wanted, test strip fit with a small S print.
- Owner then: the look must stay like the original (fat letters). New `cad/sign_fat_groove.py`: original outline x1.439 (250 x 159 x 10), 5.2 groove on the stroke centreline, solid walls 4.4-8.3, counters open. `sally_250_fat52.3mf`: groove 5.2-5.3, print_test 0 (after STL vertex repair), CLI PLA 2h24m / 89 g. Sent with images.
- Owner marks: l1/l2 grooves must not be linked (bridge removed), junctions must follow the original flow and be smooth. New `cad/sign_branches.py` + `cad/sign_chains.py`: medial-axis branches joined into pen strokes (a stem->baseline->l1 loop->baseline->l2 loop->y), spline smoothing 0.8. `sally_250_v7.3mf`: groove 5.2, wall between l1/l2 grooves 5 mm, print_test 0, CLI 2h25m / 88 g. Owner OK.
- S joined to the a after owner marks: `cad/sign_s_join.py` (S end -> round lying loop like the l -> straight cross under the S -> into the a), outer edge near the S top kept separate, wire hole 4.5 on the y right stem. `sally_250_final.3mf` 250 x 159 x 10, one body, print_test 0, CLI PLA 2h29m / 90 g. Test piece `sally_S_test.3mf` (S only, 74 x 100) 42 min / 25 g. Both sent; owner to print the S test for strip fit.
- Left: owner decides if it becomes a product (name customisation, diffuser/cover, wire exit hole not seen in the model).

## 2026-11-23 (cloud) — HueForge horse head 150 mm (owner's new AI picture)
- Owner sent a grey/cream/rust horse-head picture (not in git). White background flood-filled to black (thin base only). `zt_forge.py --width 150 --px 0.3 --base 0.64 --top 1.6`, filaments black, grey, orange, white PLA (hex/TD guesses), swaps at layers 8 / 13 / 14, dE 6.0 (orange before grey: 7.2). STL closed, print_test 0 problems. Outputs `cad/out/hueforge/horse150*` (not in git).
- Slice at 0.08 failed here (invalid params with --set layer_height); default 0.20: 56 min / 24.8 g, so real 0.08 time is only an estimate (~2.5 h). Price sheet missing in this session.
- Left: orange is only 1 layer thick (will look weak), owner's choice; 3MF with swaps; real TD calibration.

## 2026-11-23 (cloud) — R coaster: purple R + berries, smooth stem (owner's marks)
- Owner marked: main stem rough (yellow) -> brown traced at 4x with more smoothing + close/open 0.35/0.25 mm; R and berries (magenta) -> purple. `coaster_picture.py --purple`: berries = olive pieces < 15 mm2 and round (berries 6-11 mm2, smallest leaf 21.7), 13 found. Slots: TPU, purple #7B4FA0, olive, brown.
- print_test 0 problems, 0 crossed layers, CLI 1h48m / 30 g. `coaster_R_purple_final.3mf` sent in chat.

## 2026-11-23 (cloud) — coaster: monogram R + leafy branch (owner's flat picture)
- Owner sent a gold/marble R coaster photo ("take the R and the frame"); I started a Cinzel R + rings + own laurel (`cad/coaster/coaster_monogram.py`, Cinzel Bold OFL added to cad/fonts), owner stopped it and sent a flat picture instead: black serif R, olive leaves + berries, brown stems on a tan circle.
- New `cad/coaster/coaster_picture.py`: traces the 3 ink colours (picture circle -> Ø88 so the art stays inside Ø95), stems thickened evenly (~0.65 -> ~1.1 mm). Same layers TPU 0.4 | inlay 0.6 | TPU 2.0, rounded, mirrored; 4 slots (TPU + black, olive, brown PETG).
- print_test 0 problems, clear settings: 0 crossed layers, CLI 1h48m / 30 g. `coaster_R_branch_final.3mf` sent in chat (picture not in git).

## 2026-11-23 (cloud) — coaster «رانيا» with my own olive wreath
- Owner: try a new decoration instead of his. `coaster_text.py --deco wreath`: own parametric olive wreath arc under the text (brown stem r 38.5 from 226 to 314 deg, vesica leaves both sides, 3 lavender 5-petal flowers with black outline + centre at the ends and middle). Leaves room for a bigger text: name 50 x 42, line 56 x 9.
- Same layers / colours / clear settings: 0 crossed layers, CLI 1h57m / 31 g, print_test 0 problems. `coaster_rania_wreath_final.3mf` sent in chat only.

## 2026-11-23 (cloud) — coaster «رانيا» in the style of the owner's plate3 file
- Owner: first coaster design (3 mm) + clear settings + rounded edges + face on the plate; text «رانيا» big + «تطيل النظر بمحبة وتأمل» (Tabassom, no tashkeel). Inlay stays under 0.4 TPU (owner: only the STYLE of his reference, not its flush inlay).
- His reference 3MF (plate3_duaa_islam_maimouna, his own design, not in git): Ø95 x 3 PETG plates, 1 mm flush colour inlays: black text, olive leaves, brown stems, lavender flowers with black outlines.
- New `cad/coaster/coaster_text.py`: TPU 0.4 | inlay 0.6 | TPU 2.0, rounded edges, mirrored; `--deco REF.3mf --deco-object N` takes his branches/flowers (z=0 faces, his text dropped = black bits not hugging a flower), text fitted as big as it goes 1.2 mm from them. Plate 1 (دعاء, lavender) leaves the most room: name 43 x 36, line 48 x 8. Inks merged before pocketing (touching colours had left the TPU open).
- 5 slots: TPU (nozzle 2) + black, olive, brown, lavender PETG (AMS). Clear settings + top/bottom_shell_thickness=0: 0 crossed layers in the G-code. CLI 1h55m / 31 g, print_test 0 problems. `coaster_rania_lavender.3mf` sent in chat only.

## 2026-11-23 (cloud) — bookmark v4: thicker middle card
- Owner asked for a thicker separating layer between the two verses. `bookmark_text.py --card 0.8` (was 0.4): TPU 0.4 | text 0.4 | card 0.8 | text 0.4 | TPU 0.4 = 2.4 mm. PETG, clear-TPU settings, all 12 TPU layers 45 deg (G-code), CLI 1h51m, print_test 0 problems. `bookmark_sharh_tahzan_v4.3mf` sent in chat.

## 2026-11-23 (cloud) — bookmark v3 after the owner's video
- Video: owner holds the bookmark sideways and flips it over the SHORT side -> the back verse came out upside down (I had mirrored for a flip over the long side). Now the back text is mirrored along the length; render held sideways: both verses upright.
- Unclear face: white starburst cracks in the middle of the text/card = thin PLA cracked when the bookmark was bent. v3 uses PETG Basic for text + card + hearts (more flexible; owner has PETG in the AMS).
- `bookmark_sharh_tahzan_v3.3mf` (sent in chat): all TPU lines 45 deg on every layer (G-code), clear-TPU values, CLI 1h36m, print_test 0 problems.

## 2026-11-23 (cloud) — bookmark print 1 feedback: crossed lines fixed, text issues open
- Owner printed the two-verse bookmark: TPU lines still crossed; the face-down verse half unclear; back text "should appear by turning right-left, not one up one down" (unclear, photo asked).
- Cause of crossing: Bambu turns SOLID layers 90 deg each layer (no switch); with 5 top / 3 bottom shells most of the 2 mm was solid. Fix: aligned rectilinear for sparse + internal solid + top + bottom, 1 top / 1 bottom shell, ensure_vertical_shell_thickness none. G-code check: all TPU lines 45 deg on every layer. `clear_tpu_settings.py` doc updated. File `bookmark_sharh_tahzan_clear_v2.3mf` sent in chat (CLI 1h41m).
- Left: owner's photos of both faces to diagnose the half-unclear verse (first layer / bed / squish?) and what "one up one down" means.

## 2026-11-23 (cloud) — clearer TPU settings inside the 3MF
- Owner asked to hide/soften the TPU fill lines and have it all in the file. New `cad/clear_tpu_settings.py` (after `bambu_slice.py` prepares the 3MF with the real TPU 95A HF + PLA Basic profiles and --set process options): 100 % aligned rectilinear, monotonic line top/bottom, ironing top 10 % / 20 mm/s; TPU +10 C, flow x1.05, fan 30-40 %, volumetric x0.65.
- Bookmark (two verses) with these settings slices fine from its own embedded settings: CLI 1h35m / 21 g (owner's GUI usually longer). Sent in chat only. Owner must not re-pick the TPU preset in Studio (it resets the TPU values).
- Suggested a 30 x 30 x 2 test coupon pair (old vs new settings) now that the printer is here.

## 2026-11-23 (cloud) — bookmark with a different verse on each face
- `bookmark_text.py --text-back`: front «رب اشرح لي صدري» (Taha 25), back «لا تحزن إن الله معنا» (At-Tawbah 40), same letter size on both faces (one common scale), no tashkeel (marks too small to print). Card = rim around front + mirrored back text. print_test 0 problems. 3MF sent in chat only (font outlines). Told the owner «واهدنا سبل السلام» is a dua from Al-Ma'idah 16, not the verse text.
- Idea logged: Ramadan 2027 (mid Feb) gift set of 3-4 verse bookmarks; prepare files and photos early.

## 2026-11-23 (cloud) — clear TPU bookmark, text readable from both sides
- Owner: bookmark like the coaster, text «واهدنا سبل السلام» along the strip in the owner's Tabassom font (font file kept out of git, licence unknown), blue text, red hearts; readable from both sides.
- New `cad/bookmark/bookmark_text.py`: 45 x 160 x 2.0, TPU 0.4 | mirrored back text 0.4 | red card 0.4 | front text 0.4 | TPU 0.4; card = rim 1.2 mm around front + back text (owner chose this over a plain strip; a rim around the front text only cannot hide the mirrored back text). 8 red hearts at the sides, rounded edges, face down. Strokes thickened 0.2 mm.
- print_test 0 problems, parts watertight, no overlaps. 3MF sent in chat only (contains the font outlines), not in git. Not sliced.
- PLA instead of PETG for the drawings is fine (sealed in TPU); PLA is stiffer, watch for cracking if bent a lot.

## 2026-11-23 (cloud) — round coaster v2 with the heart learnings
- Owner: make the round coaster like the last hearts. `coaster.py PIC --layers 0.6,0.6,0.6 --round 0.6 --face-down` -> `coaster_birds_v2.3mf` + `coaster_birds_v2_set4.3mf` (Ø95 x 1.8, drawing centred, rounded edges, face down mirrored, TPU = shell minus drawing). print_test 0 problems. Old v1 files kept. Not sliced (owner slices).
- Offered 2.4 mm (0.9/0.6/0.9) if 1.8 feels too soft under a glass.

## 2026-11-21 (cloud) — classic Mercedes W115 front photo -> filament painting (zt_forge)
- Owner asked for a HueForge print of a W115 photo; used our `zt_forge.py` (no HueForge licence). Car cut out with rembg (isnet-general-use, scratch venv), background black, colour boosted x1.7 (the photo is washed out by reflections).
- Chosen: black / grey #6E6E6E / olive #7C8A4E / white, base 0.64 top 2.0, 150 x 117 mm, swaps at layers 8 / 14 / 17, dE 11.2. STL closed. CLI slice (PLA Basic, one colour, 0.08, 100 % zig-zag, no tower): 2h57m / 21.6 g (0.12 layers = 2h03m but needs regenerating with `--lh 0.12`). GUI is usually longer than CLI.
- Hex / TD of grey and olive are guesses. Photo, plate and outputs stay out of git (`cad/out/hueforge/w115_*`).
- Left: owner's pick of the real green spool, slice in Studio with the 3 swaps, first test print.

## 2026-11-21 (cloud) — whole alphabet A-Z on one plate
- Owner wanted every letter, all in one file: `coaster.py --letters ABCDEFGHIJKLMNOPQRSTUVWXYZ` -> `heart35_AZ.3mf`, 26 hearts in a 7 x 4 grid inside x 25-325 (both nozzles), face down (mirrored), letters centred on their box. Build takes ~6 min.
- G, K, U first came out with an open TPU mesh (slivers when cutting the pocket per 0.1 mm slab): TPU is now the full rounded shell minus the drawing in one boolean -> all 78 parts watertight (inner shells = sealed pockets), print_test 0 problems on all 26.
- The third small heart lands inside the opening of C, O, U (closest free spot). Not sliced (owner slices).

## 2026-11-21 (cloud) — ASSY: letters exactly centred, one file per letter
- Owner: letters not exactly in the middle. Cause: centred on the glyph centroid (A, Y off by a bit). Now centred on the glyph box: offset 0.000 mm on all four. Y 98% (was 100%).
- Files: `heart35_ASSY.3mf` (all 4) + `heart35_ASSY_1_A / 2_S / 3_S / 4_Y.3mf`, all face down (mirrored). print_test 0 problems.

## 2026-11-20 (cloud) — ASSY hearts printed face down
- Owner: print them on their face (glossy smooth-plate side = front). `--face-down` mirrors every part left-right (layers are symmetric 0.6/0.6/0.6), so the letters read right after turning the piece over. `heart35_ASSY.3mf` replaced; meshes watertight, print_test 0 problems.

## 2026-11-20 (cloud) — letter hearts A S S Y (35 mm, one letter each, one plate)
- Owner: letters instead of the swallow, letter in the middle. `coaster.py --letters ASSY` (Baloo ExtraBold, real font), hearts kept around. Owner approved Y as is; asked A/S higher: letters may now go up to the notch (only the loop part outside the heart is kept clear), tops aligned to Y where possible (A/S apex at x=0 limit +2.9 vs Y +4.7).
- File `heart35_ASSY.3mf` (4 objects on one plate). print_test 0 problems each. Not sliced (owner slices).

## 2026-11-20 (cloud) — hanging heart 35 with the owner's swallow
- Owner sent a swallow picture (transparent webp, kept out of git): `--shape-pic` replaces the main shape; preset `swallow_trail` = swallow up/right + 3 red hearts trailing behind the tail (big one top-left added by owner). Shapes placed one by one at full size.
- Files `heart35_swallow.3mf` and `heart35_swallow_set4.3mf`, print_test 0 problems. Not sliced: owner slices himself in Studio (faster for him).
- Swallow tail/wing tips taper under 0.7 mm (tips print slightly shorter), left as drawn.

## 2026-11-20 (cloud) — small hanging heart 35 mm (bird + 2 hearts)
- Owner: as a hanging piece the 65 is too big, about half; worried the drawings get spoiled. Options given (1 shape / 3 shapes / letter + shape); owner chose bird + 2 hearts.
- `coaster.py --picks bird_2hearts` (blue bird + 2 red hearts from his heart picture), 35 mm, 0.6/0.6/0.6, rounded edges, small loop. print_test 0 problems. CLI: 1 = 16 min / 3.8 g; 4 on a plate = 28 min (7 min each). Files `heart35_bird_2hearts*.3mf`.
- Left: owner prints (set of 4 recommended); then letter/name version for selling.

## 2026-11-20 (cloud) — first real print feedback -> heart v2
- Owner printed `coaster_heart65.3mf`: nice overall, but from the back the drawings barely show (wrong for a hanging heart), thinner TPU = clearer, smooth-plate face came out glossy, outer edges too sharp.
- `coaster.py --layers 0.6,0.6,0.6 --round 0.6` -> `coaster_heart65_v2.3mf` (1.8 mm, drawing centred, rounded edges). `print_test` 0 problems, CLI 30 min / 7.8 g (owner's GUI was ~1.8x the CLI on v1). v1 kept.
- Stale `cad/out/bambu/<name>` folder gave bogus slice numbers twice (14h55m, 1h03m/27 g): delete it before re-slicing.
- Left: owner prints v2; idea: print v2 on the smooth plate so the back is glossy too (top stays lined unless ironed).

## 2026-11-20 (cloud) — PRINTER ARRIVED: first print = heart coaster 65
- Owner sent `coaster_heart65.3mf` from Bambu Studio to the H2D. Pre-print check asked for a cold pull before TPU and flagged unknown filaments in the AMS mapping (spools without RFID). Advised: cold pull on the right nozzle from the printer's maintenance menu, set the AMS slots to PETG + colours, dry the clear TPU. CLAUDE.md updated (printer here).

## 2026-11-20 (cloud) — heart coaster 65: owner's Studio says 1h02m (CLI said 35 min), time options
- Owner's Bambu Studio (GUI) slice of `coaster_heart65.3mf`: 1h02m / 11.66 g, TPU right nozzle, 3 PETG left. CLI says 35 min: GUI/CLI about 1.8x for this TPU + nozzle-switch job (cause not confirmed: TPU profile chosen in the GUI, start sequence, nozzle heat-up).
- CLI comparison: 1 heart 35 min; 1 colour PETG 26 min; 0.28 layers 26 min; 4 hearts on a plate 1h26m (22 min each, file `coaster_heart65_set4.3mf`); 4 hearts 1 colour 1h17m. One CLI run gave a bogus 14h55m / 526 g, re-run fine.
- Left: owner slices the set of 4 in Studio to calibrate; check his TPU profile (Bambu TPU 95A HF vs generic).

## 2026-11-20 (cloud) — heart coaster 65: upper shapes enlarged into the lobes
- Owner asked to fill the empty top. `fill_top` grows each upper shape (up to 1.6x, small ones capped at 55% of the biggest) and shifts it up/outward, gaps >= 1.3 mm. `print_test` 0 problems, slice 35 min / 11.9 g. File replaced.

## 2026-11-20 (cloud) — heart coaster 65: drawings from the owner's heart picture
- Owner: my re-packed shapes had broken edges; keep my heart + loop, take the drawings from his ChatGPT heart picture (not in git).
- `coaster.py --heart 65 --heart-art PIC`: trace without buffer passes (they made beaded edges), shapes 65% / places 85%, gaps >= 1.4 mm. `print_test` 0 problems, slice 35 min / 11.9 g. Replaced `coaster_heart65.3mf`.
- Render tip: draw the TPU as a plain slab, else the pocket walls flicker and the edges look jagged.

## 2026-11-20 (cloud) — heart coaster 65 mm with hanging loop (test size)
- Owner: smaller heart for the first test, same drawings, loop in the top notch (owner's mark) to also use it as a hanging ornament.
- `coaster.py --heart 65`: 12 shapes re-placed inside the heart at 43%, thin parts fixed (butterfly antennae merge at this size), loop hole 3.6 x 5 clear of the lobes. `print_test` 0 problems. Slice 38 min / 12.6 g. File `cad/print_files/coaster/coaster_heart65.3mf`.
- Left: owner's look; for selling, 85 mm or more (a glass base does not sit on 65).

## 2026-11-20 (cloud) — clear TPU coaster with PETG drawings inside (new product)
- Owner: Ø95 x 3.0, clear TPU + PETG drawing sealed mid-layer. My hand drawings rejected ("ugly"); owner made the art with ChatGPT from my 2D prompt (prompt in `cad/coaster/README.md`, picture kept out of git).
- `cad/coaster/coaster.py` traces the 3 colours -> 3MF: TPU 1.6 / PETG 0.6 / TPU 0.8, TPU nozzle 2, PETG nozzle 1. 12 shapes, edge margin 3.5 mm, nothing < 0.7 mm. `print_test` 0 problems.
- CLI slice (0.20, 100% infill, tower): 1 = 58 min / 29 g; 4 on a plate (`coaster_birds_set4.3mf`) 2h58m / 107 g = 45 min each. Files in `cad/print_files/coaster/`.
- Left: owner opens in Studio, set price (sheet not in this session), real print when the H2D arrives (TPU clarity, TPU-PETG bond untested).

## 2026-11-20 (cloud) — bookmark: fewer visible lines (owner's aim), ironing timed
- Hilbert top pattern rejected (+11 min, no fewer lines). Advice: smooth PEI for the back, infill_direction 0 (top lines along the weave grid), silk thread.
- `bookmark_iqra` at 0.16: infill_direction 0 = 55 min; + ironing all top surfaces = 1h25m (+30 min); ironing topmost only = 57 min (crests only, little effect).

## 2026-11-20 (cloud) — bookmark with stitched «اقرأ وارتقِ»: single file
- `bookmark.py --text` (letters in `cad/bookmark/stitch_text.py`) -> `cad/print_files/bookmark/bookmark_iqra.3mf`, one piece, 2 slots (white + red default), 0.16. Overlap 0, watertight, `print_test` 0 problems. Slice PLA + tower 20: 57 min / 14 g.
- Left: owner opens it in Studio; text not yet in the 4-options file (owner asked for one piece only).

## 2026-11-20 (cloud) — bookmark: stitched text "اقرأ وارتقِ" preview (not in the file yet)
- Owner chose the text and the stitched look. Hand-drawn one-stitch-per-cell Kufi-style letters (auto-rasterised fonts were unreadable at 11 cells), vertical, reading top -> bottom, between two stitch lines moved to cols 5 / 19; alef 16 mm tall. Preview in the 4 colours sent (scratch, not in git).
- Left: owner's OK (reading direction, kasra left out), then add to `bookmark.py` and regenerate both 3MFs.

## 2026-11-20 (cloud) — bookmark: all 4 colour options in one 3MF (0.16)
- `bookmark.py --options` -> `cad/print_files/bookmark/bookmark_4_options.3mf`: 4 separate objects, 7 slots (colours from stock), layer 0.16; owner deletes what he does not want. New `threemf.write_bambu_3mf_multi` + `widen_filaments` (more than 4 filaments).
- `bambu_slice.py`: rebuilds the flush matrix n x n when more than 4 filaments (CLI failed "Flush volumes matrix do not match"). Slice: all 4 = 4h07m / 60 g; one alone 0.16 = 54 min.
- Left: owner opens it in Studio (7-slot file not yet opened in the GUI), picks options, tassels.

## 2026-11-20 (cloud) — bookmark print times (CLI, PLA, tower 20 mm)
- 1 bookmark (2 colours): 0.12 1h14m / 15 g, 0.20 41 min / 14 g. 2 on one plate, 4 colours: 0.12 2h42m / 32 g, 0.20 1h33m / 30 g. 2 on one plate, same 2 colours: 0.12 2h24m, 0.20 1h21m. At 0.16: 1 = 54 min, 2 different = 2h02m, 2 same = 1h47m.
- Two different colour pairs on one plate is slower than two separate prints (4 colour swaps per layer): batch same colours together.

## 2026-11-20 (cloud) — bookmark: 4 colour options from stock (owner's sheet)
- From the stock sheet (PLA family only, prints together): 1 PLA+ White + Silk Red/Gold, 2 PLA+ Black + Silk Gold, 3 PLA+ White + Silk Blue/Green, 4 Wood PLA + PLA+ Red. Shaded previews sent (scratch, not in git). Rose Gold on white dropped: too pale.
- Left: owner's pick; then regenerate the 3MF with those default colours.

## 2026-11-20 (cloud) — tatreez bookmark (new product idea, owner's reference picture)
- Owner sent a picture of an embroidered thobe-shaped bookmark (third-party shop photo, kept out of git) and wants it to look like real embroidery, colours swappable.
- New `cad/bookmark/bookmark.py` (own parametric pattern, nothing traced): 50 x 170 mm, part `fabric` (slot 1, plate 1.2 + aida weave 0.16) and part `stitches` (slot 2, X stitches made of two rounded threads, top one lifted 0.25 at the crossing; crests thinner than 0.7 mm removed). File `cad/print_files/bookmark/bookmark.3mf`.
- Checks: both parts watertight, overlap 0, `print_test` 0 problems (thin-feature note = 0.02 mm2 rounding slivers). CLI slice PLA + tower: 0.20 41 min / 14 g, 0.12 1h14m / 15 g, 0.08 1h34m. The CLI needs 4 `--filament` slots for this 3MF (2 slots -> "Failed slicing").
- Left: owner's look at the 3D file in Studio, layer choice (0.12 recommended), optional name under the pattern, silk thread filament, price (sheet not in this session). Not print-tested.

## 2026-11-23 (cloud) — owner: stand without the leg module: threaded feet at the bottom corners (built, not printed)
- Owner asked whether the box can stand without the kickstand (it cannot: 14 mm deep slab, tips at about 4 degrees), then proposed feet at the corners and finally "the foot itself threaded, no separate screws". Built `cad/thread_feet.py` + `"stand": "thread_feet"` (`make_lit_box(feet=True)`): two bosses D16 (z 1-10) at (+-(size/2 - 25), outer bottom edge + 20 mm) with a threaded hole, two feet = rod D14 + ball tip (axis 60 mm perpendicular to the back, the ball's lowest point is exactly on the table) + stud M11 x 3 (45 degree flanks, 0.3 clearance, 9.5 mm engaged), printed standing (flat tip down, stud up), made with manifold3d twisted extrusions (right-hand thread).
- Checks: foot / box watertight, stud fully inside the hole tool, box vs studs 0 mm3, feet lowest point 0.001 mm above the table, `print_test` of the foot 0 problems (box: the old ledge overhang flag). Slice: box + 2 feet 2h32m / 86 g (CLI, +30 min vs the kickstand set: tall feet). Section drawing `cad/plaque/thread_feet_section.png`. Files `cad/print_files/nightcap_200_feet/`. NOT checked in Fusion (helical threads); printed M11 coarse thread unproven: print `thread_test_block.stl` + one foot first.
- Left: owner's yes / no on this variant, hardware photos (screws for the plaque fixing), first print of the coupons.

## 2026-11-23 (cloud) — nightcap plaque at 150 mm: time; nut keep centred on the real frame ring
- Owner asked how long the complete 150 set takes. Built `example_ar_gpt_nightcap_200.json` with `"size": 150`: plaque CLI 2h19m - 2h22m / 56 g, box + leg + module + pin (one plate) 1h32m / 63.6 g, total about 3h53m / 120 g (200: about 5h30m). CLI only (Studio's GUI was 1.5 - 1.8x longer on the small coaster test: treat 150 as 4 - 6 h in Studio until measured).
- Found a 0.19 mm2 light pinhole at each nut at 150: `fix_points("topbottom")` used the 12-unit band centre, the real frame ring is 10.3 units; now centred on the ring (200: y 96 -> 96.57). Re-checked 150 and 200: 0 uncovered opening, watertight, interference with the box 0, `print_test` 0 problems; 200 files in `cad/print_files/nightcap_200/` regenerated. No 150 print files committed yet.

## 2026-11-18 (cloud) — frame bridges: 2 on top + 2 on the bottom, nuts moved into the top / bottom band (owner)
- Owner asked what the dark spots in the lit frame are (6 bridges + 2 nut keeps) and chose 2 bridges on the top band and 2 on the bottom; asked why the nuts cannot go inside the field. Answer: the plate base is only 2.4 mm, a blind pocket would leave 0.6 mm front skin and the M2 screw length does not fit (M2 x 14 pierces it, M2 x 12 engages 0.4 mm of the nut); in the frame band the 1.8 mm frame cap hides the through pocket.
- New `"fix_layout": "topbottom"` (+ `"fix_count": 2 | 4`): nuts at (-0.2 size, +band centre) and (+0.2 size, -band centre) (200: (-40, 96) and (40, -96)); the other two places are plain 2.4 mm bridges. `FIX_MODE` global, `fix_points()` and the frame-glow keep zones follow it; the box posts follow `fix_points()` (post found at (-40, 96) and (40, -96) in the mesh). Sides left / right of the frame now glow without any gap; the LED strip along the left / right walls is no longer cut by the posts (top / bottom walls still are).
- Checks: 4 meshes watertight, 0 uncovered opening, 21 base pieces, `print_test` 0 problems, interference with the box 0. CLI slice of the plaque 3h29m / 94 g (second run 3h33m; the file of the previous step gave 2h56m once and an absurd 185 h once: the CLI is noisy). Left: owner's hardware photos (nut / screw), Studio check of the 0.4 mm outer rim.

## 2026-11-18 (cloud) — mechanics re-checked in Fusion (owner's request) + chamber clearance +0.2
- Built an independent B-rep model in Autodesk Fusion (cloud session, `cad/fusion/verify_kickstand.ts`, STEP `cad/fusion/kickstand_check_200.step`): pocket block + module + leg + pin + M2 nut / screw / post of the 200 box. Fusion interference / min-distance agree with the mesh checks: module slide 0 (0.07 mm3 detent bump), leg 0 at 0-24 degrees, 4.22 mm3 at 26 (stop first touches at 24.0 degrees), pin 0, M2 fixing 0 (nut pocket gap 0.15, screw hole gap 0.2).
- Finding: the flange rested on the lip with 0 clearance and only 0.2 mm slack behind (printing +0.1 would bind). `kickstand.py`: `CH_TOP = MOD_T + 0.4` (pad top 6.9). Regenerated the box / kickstand files for glow_cap 150 / 200 / 280 and nightcap_200; mesh checks unchanged (interference 0).
- Fixing length (from the model): 200 = M2 nut + M2 x 14 screw (post 8 mm, hole 2.4, pocket af 4.3); 280 = M3 x 16 (post 9, hole 3.4, pocket af 5.8). Owner's nuts / screws: photos pending. Fusion verifies geometry only, not printer tolerance: a printed coupon is still needed.

## 2026-11-18 (cloud) — nightcap plaque v3: the frame glows (owner), cable = 3.4 mm slit
- Owner's decisions: frame should glow ("خليه يضوي أفضل"); big-opening question settled (this plaque has none, widest 14.8 mm = bear body); cable slot: no plug through it, just a 3 mm full slit; hardware photos (nuts / screws) coming; wants the mechanics re-checked in Fusion.
- Correction of my earlier statement: the glow box slot was 10 x 4.5 mm (the 14 x 8 mm was the train tray). Now `make_lit_box(glow=True)` has a 3.4 mm slit at the bottom-wall centre from z = 3 to the rim (checked by probing the mesh: no wall at x = 0 for z >= 3.5, wall intact at x = 2.5).
- `"frame_glow": true` (glow_cap): opening under the frame ring; base kept around the 2 nut pockets (r = pocket + 1.8 mm) and 6 bridges (4 corners + top / bottom middle, 3.6 units). Opening area 4387 -> 8691 mm2, uncovered 0, base pieces 23, watertight, `print_test` 0 problems, interference with the box 0. Base is thinner now: plaque slice 2h56m / 93 g (was 3h34m / 101 g). The 0.4 mm outer rim of the base around the frame opening is only one extrusion line wide: check in Studio that it is not dropped.
- Left: hardware photos -> decide fixing, Fusion verification of box pocket / module / leg / pin, real print of the coupon.

## 2026-11-14 (cloud) — torso pen holder: crane back to blue (owner's decision)
- After the fixes the yellow-crane version sliced 5h41m / 114.1 g. Owner then asked for the crane in blue: whole crane (mast on the pedestal included) in slot 1 with the torso; buildings + name yellow, pedestal black, no printed gloves. Both names built at 100 mm, files not in git.
- Slice (0.28, 8 %, 2 loops, tree supports, tower 30 mm): 5h53m / 116.7 g; Bambu Studio: 3 overhang regions without support. Not print-tested, no price (sheet not in this session).
- Left: owner's final OK, real filament colours from stock, price sheet for the cost.

## 2026-11-14 (cloud) — torso pen holder: owner's two marks fixed (jib tip, specks above the right building)
- Owner circled the blue jib end of the crane and small yellow specks above the right building. Crane outline widened over the top of the jib (to -94.5 deg, up to z 28-31.5, threshold 2.4 mm) -> whole crane yellow; building parts under 3 mm3 dropped and the right wedge starts at -49.2 deg (plate tip sliver gone). Both names rebuilt; re-sliced (time in the next entry / chat). Files not in git.

## 2026-11-14 (cloud) — torso pen holder: tower crane coloured too
- Owner asked for the tower crane as well. Whole crane (mast on the pedestal + the part in front of the jacket, z 21.5-34) moved to slot 3 with the buildings and the name (yellow); colour not specified by the owner, yellow chosen to keep 2 colours per layer. Crane top = torso inside a traced angle / z outline (-150..-104 deg) and more than 2.6 mm outside the back-side radius, largest piece only. Both names built, files not in git.
- Slice (same fast settings, tower 30 mm): 5h42m / 114.2 g (without the crane colour 4h50m / 106.6 g). The crane keeps colour swaps running up to z 34. Bambu Studio: 3 overhang regions without support. Not print-tested, no price.
- Left: owner's OK on crane colour, real filament colours, price sheet.

## 2026-11-14 (cloud) — torso pen holder: owner went back to example 3 + coloured buildings
- Owner's choice: example 3 (torso blue, pedestal black, name yellow) with the buildings coloured too; no printed gloves. Built for both names at 100 mm: slot 1 torso (crane above the pedestal stays blue), slot 2 pedestal + crane mast, slot 3 buildings + name. Files not in git.
- Slice (0.28, 8 %, 2 loops, tree supports, tower 30 mm): 4h50m / 106.6 g (example 3 without the buildings was 4h18m; single colour 3h56m). Bambu Studio: 3 overhang regions without support. No price (sheet not in this session). Not print-tested.
- Left: owner's OK, real filament colours from stock, price.

## 2026-11-14 (cloud) — torso pen holder coloured like the owner's reference render (blue / black / yellow)
- Owner sent a render: blue jacket, black pedestal, black gloves, blue crane, yellow buildings and name. Built at 100 mm for both names (3 slots: 1 blue = torso + crane mast, 2 black = pedestal + gloves, 3 yellow = buildings + name). Files not in git.
- How: gloves = two traced front outlines (right fingers x 23-38 / z 53-64.5, left glove + cuff bands x -21..-3 / z 45-58) as a 1.6 mm skin; buildings / crane mast = pedestal relief above the local wall surface (unrolled radius map from sections every 0.5 mm, wall = 10th percentile per angle, running minimum, +0.45 / 0.7 mm) inside angle wedges (-164..-132.8, -132.5..-124.8, -50.5..-21.5).
- Slices (0.28, 8 %, 2 loops, tree supports, tower 30 mm): as the picture 7h30m / 141 g; crane mast on the pedestal black instead of blue 6h27m / 131 g. Reference: one glove only + name 5h15m; colours only on the pedestal about 4h20m; single colour 3h56m. Three colours in the pedestal layers and gloves up to z 64 are what costs the time.
- Left: owner's decision between the full-colour print and the faster variants (gloves painted by hand); real filament colours; price sheet.

## 2026-11-14 (cloud) — torso pen holder: visible hand in the pedestal colour (owner's request) costs about 1 h
- Owner wants the hands in the pedestal colour. In this sculpt the arms are crossed: only the four fingers of one hand show (front, x 23-38, z 53-64.5 at 100 mm); the other hand is hidden. Hand part = torso x prism of a traced finger outline (front only, y < -15) minus a core 1.6 mm under the surface (voxel erosion) -> a 1.6 mm coloured skin, 1.8 cm3, one body.
- Slices (same fast settings, tower 30 mm): 2 colours (torso / pedestal + hand, name in torso colour) 5h20m / 120.4 g; 3 colours 5h15m / 116.4 g. Without the hand colour it was 4h18-4h23m, single colour 3h56m. The hand makes swaps (and the tower) run up to z 64.
- Left: owner decides: printed hand colour (+~55 min) or paint the fingers by hand; real colours; final files for both names.

## 2026-11-14 (cloud) — torso pen holder 100 mm: 2 / 3 colour examples and their time
- Owner asked how much time 2 or 3 colours add, with examples. Three example 3MFs via `threemf.write_bambu_3mf` (parts cut with `manifold3d`: name inlay 0.5 mm deep + 0.8 proud, pedestal / torso split by a plane at z 21.5): (1) body + name, (2) torso + pedestal, name in the torso colour, (3) torso + pedestal + name. Rendered side by side for the owner. Files not in git.
- Slices (PLA Basic x4 slots, 0.28, 8 %, 2 loops, tree supports, prime tower 30 mm at x 215): (1) 4h22m / 105.8 g, (2) 4h23m / 106.0 g, (3) 4h18m / 102.1 g; single colour was 3h56m / 100.5 g. So +22-27 min whatever the number of colours, because swaps happen only in the ~25 layers of the name (the pedestal / torso change is one swap). `--nozzle-map 1,2,1,1` gave the same 4h23m (two-nozzle gain not visible in the CLI estimate).
- Left: owner picks the example and the real colours from stock; then final files for both names + price.

## 2026-11-14 (cloud) — torso pen holder: 100 mm with the pedestal, two gift copies with a raised name
- Owner: gift for a cousin, 100 mm with the pedestal, the name must be on it, two copies (two names; names and files stay out of git). The Meshy pedestal has an empty name plate on the front (about 56 degrees wide, z 7-20.5 mm at this size) between a crane and buildings.
- Built at 100 mm: 92.9 x 90.6 x 100, wall 2 mm, floor 3 mm, opening ~41 mm, depth 80 mm, 125 cm3, one body. Name = Baloo Bhaijaan (`shape_run`, font `ar_name`), fitted in 38 x 6.6 mm, raised 0.8 mm, wrapped on the measured plate radius profile (the plate is not a true cylinder: 40.7 mm in the middle, 41.5 at the ends).
- `print_test`: same islands / overhangs as before, all from the original sculpt (arms, pedestal decor) -> tree supports. Slice (PLA Basic, 0.28, 8 % infill, 2 loops, tree supports): 3h56m / 100.5 g each; Bambu Studio: 3 overhang regions without support. No price (sheet not in this session). Not print-tested.
- Left: owner's OK on the preview, filament / colour, price sheet for the cost.

## 2026-11-14 (cloud) — torso pen holder: time-reduction trials (owner: 7h25m is far too long)
- Rebuilt a true 110 mm version (102 x 100 x 110, wall 2 mm, opening 45 mm, depth 88 mm, 160 cm3). Slices, PLA Basic, tree supports: 0.20 = 5h18m / 119 g; 0.28 = 4h53m; 0.28 + 8 % infill + 2 loops + 3 top/bottom = 4h38m / 122 g; 0.20 without supports = 4h29m; lean walls / infill alone = 5h04m; mesh simplified 0.15 mm = no gain (5h25m).
- Finding: time follows grams and size; settings give only ~40 min. Supports cost ~50 min. Parallel `bambu_slice.py` runs overwrite each other's `out/bambu/process.json` -> slice one at a time.
- Left: owner's decision (accept ~4.5 h at 110, go smaller, or drop / change the pedestal); not tried: thinner wall (1.2 mm), 0.6 nozzle.

## 2026-11-14 (cloud) — Meshy torso hollowed into a pen holder (130 mm, 2 mm wall)
- Owner: height 130-150 is fine, walls 2 mm. Scaled 75 -> 130 mm (120.8 x 117.7 x 130). Outer mesh repaired with `pymeshfix`; cavity built from a 0.4 mm voxel grid (2 mm inside the surface, 3 mm floor, grows at most ~40 degrees going down from the collar opening, so it needs no inner support) and subtracted with `manifold3d`; underside flattened. Scripts were one-off (scratchpad), model not in git (third-party).
- Result: one body, opening ~53 mm, depth 105 mm, 252.9 cm3 (solid was 790). `print_test`: cavity alone 0 overhangs; whole model = overhangs / islands of the ORIGINAL sculpt (hanging arms / elbow, shoulders, pedestal panels) -> needs tree supports outside.
- Slice (PLA Basic, 0.4, tree supports, one colour): 7h25m / 175.3 g; Bambu Studio warns of 5 overhang regions that got no support. No price (sheet not in this session). Not print-tested.
- Left: owner's choice of height (110 mm is about 5.5 h by area scaling, not sliced), filament, then re-slice + price.

## 2026-11-14 (cloud) — owner's Meshy torso "pen holder" 3MF checked: NOT hollow
- Owner uploaded a Meshy AI torso (prompt asked for a hollow pen holder) and asked to check whether it is hollow. File not in git (third-party).
- Result: 69.7 x 67.9 x 75 mm, 1.3 M faces, volume 151.7 cm3 = fully solid; horizontal slices at 19 heights and two vertical cuts show no cavity and no opening at the neck. Mesh not watertight, 803 fragments (801 tiny), one 19 k-face loose patch near the base.
- Left: owner's answer on final height (75 mm is too short for pens) and OK to carve the cavity ourselves (boolean pocket from the neck) + repair, then `print_test` and `/3d-cost`.

## 2026-11-14 (cloud) — nightcap plaque v2: GPT-style row of 4 boxes, icons + values only, cap clear of the frame
- Owner: the GPT render's boxes look better; remove the label words (keep icons), lower the bear so the cap does not touch the frame line. New `"row_boxes": true` in `layout_gpt` (`_gpt_row_boxes`): 4 portrait boxes in one row (date, weight, length, time; icon on top, number big + unit small, date = day/month + year), everything above shifted down 22 units (`upper_dy`), traced 2 x 2 boxes / icons / bottom heart dropped; bear 116 x 84.
- Checks: 4 meshes watertight, 0 uncovered opening, base islands 20 (smallest 7.8 mm2), widest bridge 14.8 mm, `print_test` 0 problems (1 note: strokes under 0.7 mm somewhere in the raised text / details), interference with `glow_box_200.stl` 0. Slice: plaque 3h34m / 101 g (was 3h40m). Units (كغم / سم / ص) kept; the label words are gone.

## 2026-11-14 (cloud) — boy's plaque: nightcap bear (owner's GPT flat picture) on the new cloud, 200 x 200, 4 AD-PETG slots
- Owner sent a GPT render with a bear in a night cap, asked for the bear like it, 4 colours and 200 as the base size. Stock sheet uploaded to the git-ignored `cad/config/filament_prices.xlsx` (prices / stock stay out of git): the owner has translucent light blue AND translucent blue, so the bear gets two translucent blues like the picture.
- `cad/poses/nightcap_export.py <flat.png>` writes the pose `nightcap` into `poses.json` (body = light blue, cream = muzzle / cap band / pompom, navy = outline / eyes / nose). `layout_gpt` got `"bear_details": "twoblue"` (body -> 4th slot, outline -> main slot, white parts cut out, 0.1 / -0.05 buffer against vertex-touching edges) and theme `gpt_nightcap`; glow_cap keeps this theme for the preview / 3MF colours.
- Checks (`example_ar_gpt_nightcap_200.json`): 4 meshes watertight, `check_plaque.py` 0 uncovered opening, 20 base pieces (smallest 15.2 mm2), widest bridge 14.1 mm, `print_test` 0 problems, interference with `glow_box_200.stl` 0 mm3. Slices (CLI, 4 `--filament`, Basic + 3 Translucent): plaque 3h40m / 101 g, box set 2h01m / 90.5 g. Files in `cad/print_files/nightcap_200/`. Not print-tested. Left: owner's marks on the preview, real name / values, LED strip perimeter test.

## 2026-11-14 (cloud) — merged branch `claude/adoring-galileo-un5tms` (wedding session, 8 Nov: new cartoon cloud + GPT layout) into main
- Owner remembered "the cloud shape was changed in some conversation": it was the session "تصميم لوحة عرسان" (session_01WCFcYzEbZE81uDQvJHdFtQ), commits of 8 Nov on that branch: `"cloud": "real"` (owner's 5-lobe cartoon cloud, `cloud_w` / `cloud_h`), `"layout": "gpt"` (sleeping teddy on the cloud, `example_ar_gpt_blue.json`, our own teddy poses, glow_cap mode), balloons layout, wedding heart plaque tools.
- Merge: only `WORKLOG.md` and `requirements.txt` conflicted (kept both sides / `networkx`). Re-ran the generator after the merge: original plaque, glow_cap + box + kickstand (one plate) and the new `gpt` layout in glow_cap mode all build without errors. Not re-sliced; not print-tested. Left: build the lit set (plaque + existing box + kickstand) for the `gpt` layout and check it against the box.

## 2026-11-11 (cloud) — Petra (Treasury) wall art 200 x 200 with `zt_forge.py`
- Owner's judgement: a 300 x 200 scenery plaque (7.5 h) cannot earn its print time -> ready-made scenery is content only, not a product. Time follows grams (~6.7 min/g at 0.08): dark pictures with a black background are the fast ones.
- First prompt (flat linocut style) gave two images the owner disliked (my prompt's fault). Second prompt (realistic, candle-lit, like the Jerusalem image): GPT image chosen; the Gemini image is not the real facade. Lanterns removed by fading the ground below the steps to black.
- Final: black, Walnut PLA, PLA+ orange, PLA+ yellow; base 0.64 / top 1.6; swaps at layers 8 / 13 / 17; dE 7.9; STL closed, 34.0 cm3. Hex / TD of all four are guesses (wood-filled filament: opacity and 0.4 nozzle at 0.08 layers unproven). Slice (PLA Basic, one colour, 0.08, no swaps / tower): 4h59m / 41.9 g; `print_test`: 0 problems (note: details thinner than 0.7 mm). The two rejected flat images sliced 4h03m (Gemini) and ~4h28m (GPT). Outputs in `cad/out/hueforge/petra_final*` (not in git).
- Left: owner's OK, photos of the spools for real colours, centring the facade (black strip at the bottom), 0.12-layer trial.

## 2026-11-11 (cloud) — Kromacut tried on the horse picture (owner's request) + thinner version of ours
- Owner pasted a Kromacut plan with 27 colours / a swap every layer (not printable with 4 AMS slots). Kromacut = open-source web app; `npm ci` of its repo was blocked here, so the live web app was driven with Playwright (headless): horse 1000 x 667 px, 0.3 mm/px, 0.08 / 0.16, Auto-paint with a 4-filament profile (black, blue, cyan, white, our TD guesses), defaults otherwise. Its 3MF download hung; STL downloaded.
- Kromacut result: 300 x 200 x 1.36 mm, swaps at layers 2 / 6 / 11, black only in the first layer -> the horse comes out BLUE (also in its own preview). Colour error vs the picture with our model: Kromacut 24.8, ours 9.6. Slice (0.08, 100 %, PLA, one colour): 6h52m / 54.0 g. Its settings were not tuned.
- Ours thinner (base 0.64, top 1.6 instead of 2.4; swaps 8 / 9 / 13; dE 10.9 vs 10.5): 7h24m / 75.0 g (was 9h06m / 82.2 g). STL closed. Base 0.48 / top 1.44 gives the same dE at low resolution (not built).
- Left: owner's choice (thin version / smaller size / 0.12 layers), print_test on the chosen file, real TDs.

## 2026-11-10 (cloud) — horse plaque 300 x 200 rebuilt from the Manus picture with `zt_forge.py`
- Manus's STL had the black horse HIGH (light) = wrong against its own picture, 4.8 mm thick, no swaps. Rebuilt in colour mode, base 0.64 / top 2.4: black, blue, cyan, white PLA+ (swaps at layers 8 / 9 / 15, dE 10.5). With 3 colours (no cyan) water and sky turn lilac (dE 12.9). STL closed, 66.7 cm3.
- Slice (0.08, first 0.16, 100 %, PLA Basic, one colour, no swaps / tower): 9h06m / 82.2 g (Manus's STL: 22h15m / 183.7 g). Cyan and blue hex / TD are guesses. Outputs in `cad/out/hueforge/` (not in git).
- Left: owner's decision on size (9 h is long; 200 x 133 untested), print_test, 4-slot 3MF with the swaps for a tower slice.

## 2026-11-10 (cloud) — owner's `horse_v3_300x200_experimental.stl` checked (STL only, no picture / colours / swaps)
- Heightfield 300 x 200, 0.64-4.8 mm (continuous heights, 901 x 601 grid), closed mesh, 149 cm3; 42 % of the area is above 2.4 mm. Edges of the reflection are ragged. Slice (0.08 Extra Fine, first 0.16, 100 %, PLA Basic, one colour, no swaps / tower): 22h15m / 183.7 g. File not in git.
- Left: the source picture + filament list (without them there is no swap plan), and a thinner rebuild (top 2.4) through `zt_forge.py`.

## 2026-11-10 (cloud) — Manus "HueForge demo pack" reviewed (owl / koi / horse images + guide)
- Pack = 3 AI source images (1920 px), a guide about HueForge modes, a layer-arithmetic checker and an owl STL that is only a brightness relief (no colour model, no swaps: not printable as a painting). Nothing sliced or calibrated there; nothing from it copied into git.
- The 3 images run through `zt_forge.py` at 200 mm with stock PLA+ (TD guesses): owl black+white (1 swap, layer 16) and koi black+red+white (swaps 8 / 11) look good; horse black+blue+white is weak (grey body turns black/white, sky lilac). All 3 STLs closed. Not sliced. Left: owner's pick of what goes to the first test prints.

## 2026-11-10 (cloud) — HueForge-style filament painting: tool brought into the repo + first real slice (Jerusalem wall art)
- Owner uploaded the handoff zip of a chat session (9 Nov). `cad/hueforge/` = `zt_forge.py` (image -> heightfield STL + simulated preview + swap layers) and `check_stl.py`, see its README. Images, STL, previews, research on the downloaded rose stay out of git (`cad/out/hueforge/`); price sheet copied to `cad/config/` (git-ignored).
- Dome of the Rock 200 x 200 regenerated: preview pixel-identical to the handoff, swaps #8 blue / #12 silk gold / #22 white, STL closed, 33.2 cm3. `print_test` on the 100 mm sample: 0 problems (note: details thinner than 0.7 mm).
- Real slice (0.08 Extra Fine, first layer 0.16, 100 % infill, PLA Basic, ONE colour so without the 3 swaps / tower): 200 mm = 4h40m / 40.9 g, 100 mm sample = 1h20m / 10.2 g (the chat's guess was 2.5-3 h and 45-60 min). Slicer warning "floating regions" on both = single raised pixels of the colour mode, not real islands.
- Fixed: `sparse_infill_density=100%` through the CLI needs `sparse_infill_pattern=zig-zag` too (this was the 0h00m failure of the entry below); `requirements.txt` now has `manifold3d`, `networkx`, `openpyxl`.
- Left: TD of PLA+ Blue and Silk Gold are guesses until a printed sample is photographed; a 4-slot 3MF with the swaps built in (for a slice with the tower); the thin cable right of the dome in the picture; time is long for the owner's taste (ideas: 0.12 layers, smaller size) - not decided.

## 2026-11-10 (cloud) — Maryam v4 (current): no ribs under the butterfly wings
- Owner noticed the smaller wings had no rib: the two upper wings were only 0.7 mm over the 20 mm rule (span 20.7; next widest openings 16.9). Owner: pick what fits, as long as it does not sag -> bridge limit raised to 21 mm in `rebuild_thick.py` (3rd argument), so no rib and no grid. v3 (one rib per wing, entry below) is superseded; `rebuild_thick.py 0.4 out 20` brings the rib back if the real print sags.
- Checks: 3 meshes watertight, `print_test` 0 problems, uncovered opening 0 mm2. Not re-sliced (time stays ~6h54m). Zip v4 sent to the owner (not in git). Left: real values for Maryam, prices, time decisions; bridge of 20.7 mm is unproven until the printer arrives.

## 2026-11-10 (cloud) — Maryam v3: grid under the butterfly wings replaced by one rib per wing (owner's choice)
- Only 2 openings were wider than 20 mm (upper wings, span 20.7). `rebuild_thick.py` now cuts ONE 1.4 mm base rib along the long axis (`vein`), spans after 10.7 / 11.4 mm. Supports instead of ribs were discussed and rejected (cap sits on a 0.4 mm ledge, PETG on PETG, scar on the light face).
- Checks: 3 meshes watertight, `print_test` 0 problems, uncovered opening 0 mm2. Not re-sliced (base changed by < 0.2 cm3; time stays ~6h54m). Zip v3 sent to the owner (not in git). Left: owner's OK, real values for Maryam, prices, time decisions from the entry below.

## 2026-11-10 (cloud) — why the lit 280 plaque takes ~7 h (owner: too long; compare Maryam with Yusuf)
- Same settings for both (PETG Basic white base + PETG Translucent caps, 0.24, tower): Maryam 6h54m / 194.5 g, Yusuf 280 6h11m / 201.7 g, Yusuf 200 3h46m / 108 g. Maryam +43 min = pink 52 g vs 28 g and more outlines (walls 72 vs 45 min raw, travel 69 vs 51).
- Where the time goes (both): the solid white base 280 x 280 x 2.4 (10 of 18 layers, about 60 %). One base layer (6) takes 43-46 min = slow bridge layer over the 2 sparse layers inside the base. Bambu's PETG Translucent profile is limited to 6 mm3/s (Basic 18, HF 25): all PETG Basic gives 5h53m (that is the 5h48m of 7 Nov), all PLA 5h41m.
- Tried on Maryam: 0.28 layer 6h41m, HF base 6h46m, both 6h26m (small gains). `sparse_infill_density=100%` via the CLI returned 0h00m (failed, not solved).
- Owner asked about the grid in the butterfly wings of the lit preview: these are the base ribs of `add_ribs` (openings wider than 20 mm get 1.4 mm ribs every 14 mm); they were in v1 too, the old preview did not draw them. Left: owner's choice (keep / one centre rib / none), and the time decision (size 200, real flow of his translucent filament, bridge layer).

## 2026-11-10 (cloud) — Maryam backlit plaque v2: Kitty line art thicker (owner: "سمّك خطوط وجه كيتي")
- New session had no picture / `G6.pkl`; owner uploaded his package zip (3 STL + 3MF + box). Layer shapes recovered by sectioning the STLs (`cad/maryam/recover_from_stl.py`; identical rebuild matches the old base area within 1 mm2, 22 pieces), then the whole Kitty line art (head, whiskers, eyes, bow outline, body: 4 pieces) grown 0.4 mm per side (`rebuild_thick.py 0.4`). Name, pills, decor, frame, nut pockets unchanged.
- Result: light opening under the Kitty lines 707 -> 1283 mm2. 3 meshes watertight, `print_test` 0 problems, opening not covered by a cap 0 mm2, base pieces 22 -> 29 (smallest 6.9 mm2). Slice (PETG Basic base + PETG Translucent caps, 0.24, tower x=287): 6h54m / 194.5 g vs 6h53m / 194.5 g for the old file with the same settings (the 5h48m of 7 Nov was with another filament profile). No price sheet in this session.
- Setup gaps found: `cad/requirements.txt` lacks `manifold3d`, `networkx`, `openpyxl` (installed by hand). Outputs sent to the owner as a zip (not in git). Left: owner's real values for Maryam (weight / length / time / date are still the picture's examples: needs the fonts path of `build_flat6.py` = the picture again, or a text-only patch), owner's OK on the look, translucent filament prices, Studio check. Not print-tested.

## 2026-11-08 (cloud) — Newborn plaque round C: balloons layout + 4 bear poses (original teddy, no third-party character)
- Owner wants the plaque improved (Etsy-style soft look) and a buyer-selectable bear POSE per order. He asked to copy Care Bears (cover picture) -> refused (trademarked character; badge removal / one colour does not change that); built our own original teddy instead: GPT sheet (prompt in `gpt_prompt/PROMPT_C_balloons.md`, pose sheet prompt in chat) -> `cad/poses/clean_bears.py` (one-colour vector) -> `export_poses.py` -> `cad/poses/poses.json` (sleep / cheer / balloon / star).
- New layout `"layout": "balloons"` + `"pose"` in `cad/newborn_plaque.py` (`layout_balloons`): teddy on top of a lower name cloud, 3 hot-air balloons, small clouds, stars, crescent, date badge as a pill, smaller footprint box; new themes `soft_blue / soft_green / soft_pink` (tan teddy). Example: `cad/plaque/example_balloons_sleep_ar.json`. Flat previews only; the GPT sheet / third-party pictures are not committed.
- Left: owner's marks on the previews; check thin lines (eyes, smile, ropes) at 150 mm; stock filament match for the soft colours; then glow_cap 3D, print test, slice.

## 2026-11-07 (cloud) — Wedding heart plaque: 3D built (plaque + heart box + kickstand), checks done
- Owner approved flat v3 ("ابني الـ3D"). `cad/wedding/build3d.py <flat.png> <out_dir>`: plaque 4 slots (opaque base 2.4 with openings under the cream field + ribs, translucent cream 1.2, gold 1.8, navy 1.8), 2 planted M3 nuts in the 9 mm frame at y=+48, heart box 285.6 x 269.8 x 14 (12 tabs, 2 posts, USB-C slot in the flat bottom wall, dovetail pocket), kickstand reused with `kickstand.OVERRIDE` (hinge at 0.79 of the box height so the pocket stays inside the heart; leg 213 mm). Design change decided by me: the heart tip is cut FLAT (38 mm foot) so it can stand: plaque 280 x 264.2.
- Checks: all parts watertight (needed manifold3d + closing buffers on box slabs / base), interference box vs module/pin/leg (0 and 23.5 deg) = 0 mm3, `print_test` plaque 0 problems, box = only the old ledge overhang flag at Z 8.5 (the old square box gives the same), leg/module = the known flange bridge. Slices (PETG Basic 0.24, price 4.263 JOD/kg because no price sheet in this session; translucent costs more): plaque (tower x=287) 4h49m / 134 g, box+leg+module+pin one plate (x 3..300, y 1.5..302) 2h26m / 111 g. `render3d.py` z-buffer renders. Not print-tested.
- Print files + renders stay in the scratchpad (silhouette traced from a GPT picture: not committed). Left: owner's view of the renders, real filament prices, Studio check of the plate, first print of module + leg + pin coupon.

## 2026-11-07 (cloud) — Wedding heart plaque: flat v3 from the owner's own clean flat picture (no banner)
- Owner marked v1 (lobes too pointed, rings not interlocked, flecks) and then sent his own clean flat picture (no banner, bigger rings, calendar icon, bottom heart). Agreed: use it as the base, NO "يوم الزواج" line (assumed, he did not object), frame rebuilt 9 mm wide (picture had 3 mm) so it can carry the box.
- `cad/wedding/flat_v3.py <flat.png> <out_dir> [--name1 --name2 --date --frame]`: heart outline + couple + veil + hearts + lines + rings + calendar traced from the clean colour masks (smoothed), names/date re-typeset with the real fonts, content auto-scaled only if it does not fit the wider frame (it fit at scale 1.000). Heart 280.0 x 279.9 mm. Pictures/preview stay in scratchpad (third-party).
- Left: owner's marks on v3, then 3D (layers: gold / navy / translucent cream; heart box + nut posts + kickstand), print test, slice. Nothing print-tested.

## 2026-11-07 (cloud) — Wedding heart plaque (backlit, same idea as the newborn plaque): flat 2D preview v1
- Owner sent 2 GPT pictures (backlit couple silhouette / lithophane photo). Agreed after discussion: start with the backlit silhouette version, heart plate 280 wide + NEW heart-shaped box (+ same printed kickstand), lithophane maybe later as an option. Colours planned: gold / navy / translucent cream.
- `cad/wedding/flat_v1.py <picture.png> <out_dir>`: heart outer measured from the picture (spline, mirrored), frame 48 -> 34 px, couple + veil traced (big shapes only), banner / hearts / lines / rings parametric, names + date with the real fonts. Picture and preview stay in the scratchpad (third-party).
- Left: owner's marks on the flat preview (rings are smaller than the picture because the heart tip is narrow, bottom lines short), then 3D (layers, heart box, nut posts, kickstand), print test, slice. Nothing print-tested.

## 2026-11-07 (cloud) — Maryam plaque: square 280 x 280 (fits the EXISTING box) + backlit (glow_cap) build
- Owner: keep the box as it is, change the plaque size -> plate 280 x 280 (r 28): butterflies / bottom sprigs moved out, sprigs stretched, pills 15 mm wider, same content. Backlit like the original plaque: opaque white base with openings, translucent pink (2 levels: fills 1.2, frame / Kitty lines / text / icons 1.8) and yellow (1.2) caps, frame has no opening, 2 nut pockets as in `fix_points`. 3 slots used (white opaque, pink translucent, yellow translucent), tower x=287.
- Checks: 3 meshes watertight (base needed a 0.12/-0.06 buffer to remove 3-4 vertex-touching edges), `print_test` 0 problems, opening not covered by a cap = 0 mm2 (no light leak), interference with `glow_box_280.stl` = 0 mm3, base pieces 22 (smallest 6.9 mm2). CLI slice (PETG 0.24, tower on, 4 --filament args): 5h48m / 194 g (price per kg is the plain PETG estimate, translucent costs more). Not print-tested.
- Scripts in `cad/maryam/` (picture + traces stay out of git, see its README). Thin lines (< 0.8 mm: Kitty outline, whiskers, small text) get no real opening, so they glow weakly. Left: owner's view of the lit preview, real filament prices, Studio check.

## 2026-11-07 (cloud) — Maryam plaque v3 flat (owner: v1 was bad; 3 colours only: white / ONE pink / yellow)
- Owner's marks on v1: broken leaf stems at the cloud corners, mess above the name and on Kitty's dress/heart, bow overlapping the clock text, sliver bottom-left. Fixed: pink = light+dark merged (frame, Kitty lines, text, icons are the same filament printed 0.6 mm higher), decor symmetric (left half mirrored), flowers / butterflies / leaf sprigs drawn parametric from measured px (traced leaves merged), pink under the yellow parts (no white halo), slivers near the frame dropped. Scratch only (picture + Kitty character stay out of git). Left: owner's marks on v3, then 3D (z levels, 3 slots), print test, slice; date 12/03/2024 and values are the picture's examples.

## 2026-11-07 (cloud) — Maryam Hello Kitty plaque (personal gift, NOT for sale): flat preview from the owner's GPT picture
- Owner's GPT zip was a mess (wrong letters "الورن"/"الاريخ", digits reversed, no eyes, non-watertight, 245 x 280). Owner confirmed: gift, wants this design. Rebuilt from the GPT picture (1450 x 1085) following `3d-picture-to-cad`: colour segmentation (white / light pink / dark pink / yellow), plaque 245 x 280 (frame 11 mm, r 28), pills parametric, name/labels/values with the real font, icons from the generator, dark pink kept only for Kitty + bow (elsewhere it was 3D side-wall shading), thin lines buffered to >= 0.7 mm.
- Flat preview + overlay shown to the owner; scripts and picture traces stay in the scratchpad (third-party character/picture: NOT committed). Left: owner's marks, then 3D (z levels, 4 filament slots: white / light pink / dark pink / yellow), print test, slice. Date 12/03/2024 and values are the picture's examples.

## 2026-11-07 (cloud) — kickstand: everything on ONE plate (owner: all parts in the same print)
- `glowcap_all_<size>.3mf` = box + leg + module + pin on one plate (replaces `glowcap_box_*` / `glowcap_kickstand_*`). Foot narrowed 40 -> 28 mm (`FOOT_W`) so the leg fits the 32 mm strip above the 280 box (bed 320 in y); pin in the right strip (x <= 300; left nozzle reaches ~305). Slices OK (the CLI needs one `--filament` per slot, 4 for these 3MFs; with a single `--filament` it fails with ZFiller errors): 280 2h57m/145 g, 200 2h01m/91 g, 150 1h32m/63 g (PETG, 0.24). 280 is tight (1.5 mm from the front edge): verify in Bambu Studio.

## 2026-11-07 (cloud) — removable printed kickstand built for the backlit box (owner: "ابني", no brass inserts)
- New `cad/kickstand.py` + `make_lit_box(..., kick=True)`: box gets a pad (back panel thickened to 6.7 mm inside, +6.5 cm3) and a blind dovetail pocket in the back (lips 2.5 mm, chamber behind, two entry windows, 2 detent dimples, floor 2 mm = no light leak). Module (30 x 28 x 17.7) enters through the windows and is pushed UP 10 mm: the leg pushes the module up, so the load cannot unlock it. Two ears + stop bar (touches the leg at 24 degrees), snap pin (head + slit prongs), leg 232 x 12 x 4 with barrel + 40 mm foot flush with the bottom edge. Print-in-place hinge dropped: the leg would hang in the air when printed flat -> separate printed pin instead (still no metal).
- Checks (`trimesh`+manifold): all parts watertight, module/leg/pin vs box 0 mm3 at 0-23.5 degrees, stop collides at 26 degrees, pin vs leg/module 0, sliding-in detent interference 0.06 mm3. `print_test`: leg and pin OK, module only the 8 mm bridge between the flanges, box only the old plate-ledge overhang at Z 8.6 (existed before). Slices (PETG, 0.24, 280): box 2h30m/131 g, leg 23m/10 g, module 19m/4.5 g, pin 5m.
- Files in `cad/print_files/glow_cap/` (box + kickstand 3MF and STL for 150/200/280); old `back_leg_*`, `glowcap_box_and_leg_*`, `glow_box_noleg_*` removed; picture `cad/plaque/kickstand_renders.png`. Nothing print-tested: detent bumps (0.45 mm) and pin/barrel clearances are parameters. Left: owner's view of the renders, first print of module + leg + pin coupon, fix the pad over the LED strip layout if it collides.

## 2026-11-07 (cloud) — backlit box without any leg base
- Owner: remove the boss and screw hole, no base for the leg at all (leg to be decided later). `make_lit_box(size, glow=True, leg=False)` -> `cad/print_files/glow_cap/glow_box_noleg_{150,200,280}.stl` (watertight; boss/pocket/screw/cord hole gone, -794 mm3 at 200). Plaque fixing (2 planted nuts + 2 posts/screws) unchanged. The generator's default output and `glowcap_box_and_leg_*` still carry the leg boss.

## 2026-11-07 (cloud) — owner asked for the latest backlit (glow_cap) original plaque: image + files + gaps
- Added `cad/plaque/example_ar_glowcap_preview.png`. Latest files: `cad/print_files/glow_cap/` (plaque 3MF ar/en 150/200/280, `glowcap_box_and_leg_*.3mf`, `glow_box_*`, `back_leg_*`). Open: the leg hinge fix (bracket with ears + horizontal M3 pin + brass insert, leg +2.8 mm) was proposed on 2 Nov and is NOT in the code/files; nothing print-tested; owner's yes on the fix pending.

## 2026-11-06 (cloud) — Parametric one-piece automotive nameplate script
- `cad/nameplate_one_piece.py --name Omar --width 250 --out cad/out/x` (English names only, Pacifico font bundled): frame polygon + name, 3 layers extruded with manifold3d (body 10, name +6, LED channel cut from the FRONT, 3 mm x 5 mm, wire hole d=3 from the back). Output watertight by construction (checked), 1 body, `/3d-print-test` 0 problems.
- Frame outline is third-party/private: `cad/config/automotive_frame*.wkt` (git-ignored, copy by hand). Known limit: the traced frame still has the old name's banner outline (kept to stay one piece); the `_cut` variant is clean but leaves rods/wrench cut in 5-6 loose bodies. Fix = redraw the cut rods/wrench parametrically (not done). Not print-tested; no diffuser/rear cover yet.

## 2026-11-06 (cloud) — Reviewed owner's automotive nameplate zip (wrench+pistons+"Rabea", 297x250x28)
- Findings: A/B/C/E meshes not watertight (few open edges + pinch points from traced outlines, 8-17 bodies each), D/F/G fine, parts not at z=0, SCAD is symbolic (not matching STL), font Brush Script not bundled. Quick repair (normals, z=0) done in scratch; pinch points remain, so slicer test still pending.
- Agreed rule: quick repair first, rebuild only if needed (now in CLAUDE.md). Left: run cad/setup.sh + /3d-print-test + /3d-cost on repaired parts.

## 2026-11-04 (cloud) — BMW painter: 600 x 211 mm version in 3 interlocking modules
- Owner asked for the approved art at 600 mm, 3 mm body, exactly 3 modules with hidden joints. `cad/bmw_painter/modular.py <master_stl_dir> <out>` reads the approved model back, scales x2.0149, cuts at x=196 (between grille/lamps and front wheel) and x=452 (car tail / spray beams bases), adds rear sliding dovetails (tab 6 mm, 12 deg flanks, 0.25 clearance, vertical slide, gravity-seated, pads <= 1.8 mm outside the lines), rear tie bars for isolated bits, exports STL/3MF (art mirrored in X because modules print front face DOWN), validation.json; `render_modules.py`, `drawing.py`, `step_export.py` (slow, optional).
- Checks: each module 1 shell, watertight, 0 bad edges after STL export, fits H2D (max 262 x 211 x 12.65), interference 0, seam gap 0.2 mm. Slices (PLA, supports, tower): M1 2h26 41 g, M2 5h15 90 g, M3 3h03 48 g = 10h44, 180 g, ~1.62 JOD. Nothing print-tested.
- Honest limits: pads are visible as dark blocks through the open spaces at oblique angles; seam 2 cuts the beam bases; 0.2 mm hairline on the front; STEP bodies are polylines.

## 2026-11-04 (cloud) — BMW painter openwork wall art: phase 2 (CAD) built
- Owner approved the flat design (v5: painter 82 mm tall to match the car's rear perspective, blue = recoloured original rear-quarter lines + 3 spray beams, 5-spoke wheels, open face). `cad/bmw_painter/phase2.py <phase1_dir> <out_dir> [--depth 5]` -> exact manifold extrusions (manifold3d), STL (fused), STL per colour, 2-colour Bambu 3MF, STEP per colour; `render3d.py` -> lit renders. Piece is 297.8 x 104.7 mm.
- Checks: all STL watertight, 1 body, footprint 1 piece, `/3d-print-test` 0 problems (0.6 % of area thinner than 0.7 mm). Slice (PLA Basic, tower beside the piece at y=235, price 6.951 JOD/kg from the owner's file, no price sheet in this session): 5 mm = 5h45m, 62.8 g, 0.64 JOD; 3 mm = 3h36m, 38.6 g, 0.39 JOD. Nothing print-tested (printer not here).
- Left: owner picks 5 mm or 3 mm; real print test when the printer arrives; STEP is faceted polygons (not parametric).

## 2026-11-04 (cloud) — BMW painter openwork wall art: phase 1 (flat vector) done, waiting for approval
- New project (not the plaque). `cad/bmw_painter/phase1.py <car_rgba.png> <composition.png> <out_dir>`: car from the owner's picture 1 (3/4 view), painter from picture 2, 300 x 150 mm flat, black + blue, wheels replaced by 5 spokes, ground line follows the car's perspective, 3 blue beams + 2 blue accents. Union = ONE connected piece. Pictures/SVG/preview stay out of git (scratchpad).
- Open for owner: grille/headlights fuse to black blobs at 3 mm lines; blue accents on quarter panel small; height 150 not 180-200 (proportions). Nothing built in 3D, nothing sliced.

## 2026-11-04 (cloud) — key holder: hooks switched to the outward J hook (owner gave me the choice)
- Owner (annoyed that I changed the design without discussing, then): "you have the freedom, pick the best". He sent the MakerWorld fish-skeleton 3MF (6 hooks 5-6 mm wide, plate 7.6, curl out 29 mm, printed with tree supports on an A1) and his own Aldawayme wrench 3MF (our v6: 5 hooks 6.0 wide x 39.5 tall x 29.3 out, no supports thanks to the 45 deg underside slope, PLA Basic, 2 walls, 15 %). Both third-party-derived, kept OUT of git.
- Decision: use the proven outward J (stem in the wall plane, curl toward the viewer, 45 deg underside = no supports) instead of my flat hanging J, but 8 mm wide (own call, stronger) and stem 8 mm into the plate, same colour as the plate. `keyholder3d.py --hook-profile <local json>` (the (y,z) side profile cut from the owner's wrench 3MF with a local script; fallback without the json = my flat J). Flat view: stem 8 x 31.5 mm with round end (`flat_preview.hook_j_mm`).
- Checks (palette D: red plate, black seat/wheel/strip, Silk Silver): watertight, `/3d-print-test` 0 problems (five 0.4 mm overhangs at the tips), piece 300 x 182 x 29 mm. Slice (tower on): 5h40m, 171 g (red 105, black 50, silver 15.7), 1.42 JOD. The tall hooks add about 30 min vs the flat J (5h11m). Nothing print-tested. Left: owner's view; time idea (shorter hooks); hook strength is untested.

## 2026-11-04 (cloud) — key holder: palette D (red plate, black seat/wheel/strip) + hanging J hooks (owner showed the wrench piece's hook system)
- Palette D approved to try: plate/panel/arch red, seat + wheel + leather strip black (`--grey --strip-dark`), lettering/machine/chrome Silk Silver; 3 filaments (PLA+ red, PLA+ black, Silk Silver). Hooks changed to the wrench-piece system: flat J hooks hanging BELOW the plate in the wall plane (stem 9 wide, 30 mm drop, curl R 11, rounded tip, 6 mm thick, stem 10 mm into the plate), same colour as the plate, printed flat: no overhang, no support. `flat_preview.hook_j_mm`, my own drawing (not the third-party profile). Piece is now 300 x 196 mm (the original 300x200 target); the peg hooks are gone.
- Checks: all parts watertight, `/3d-print-test` 0 problems, slice (3MF `make_3mf.py --scheme D`, tower on): 5h11m, 169.9 g (red 106.1, black 49.7, Silk Silver 14.0); with the stock sheet: 1.39 JOD (material 1.21 + electricity 0.18). Nothing print-tested. `wrench_render3d.py` camera now fits taller pieces.
- Left: owner's look at the hooks (length, curl size, thickness), wall mounting (2 countersunk screws kept), then the texture idea, time reduction.

## 2026-11-04 (cloud) — key holder colours: seat/wheel looked like the background; 4-colour options from stock
- Owner rejected the grey seat. Price sheet received (copied to `cad/config/filament_prices.xlsx`, git-ignored). Stock useful here: Wood PLA, Walnut PLA, Silk Silver/Bronze/Copper, PLA+ black/red/white/grey. `keyholder3d.py --grey` now splits 4 colour groups: black = plate/panel/arch (z<=5.5), "grey" slot = seat + wheel + hooks (start exactly on the plate), red, white (-> Silk Silver in the options). Rendered 3 palettes (`cad/keyholder/preview/palette_*.png`): A walnut plate + black seat, B light wood plate + black seat, C black plate + walnut seat; all with Silk Silver trim. Recommended A (red stitching and silver pop best). Owner to choose; then 3MF colours + print test + cost. Not yet checked: Walnut/Wood PLA print profile, time with 4 colours (the last slice was 3 colours, 5h05m).

## 2026-11-03 (cloud) — key holder 3D v2: rounded edges + real quilted diamond cells
- Owner asked why the print would be smooth (the picture's leather grain is a render texture, not geometry) and said "try 1 and 2" (chamfered/rounded edges and domed surfaces). `keyholder3d.py`: `shaped()` = quarter-round top edges built as 0.4 mm slabs (`ROUND` per piece: bolsters/cushion/headrest 2.2, wheel rim 1.4, hub pad 1.2, strip 1.5, plate 0.8); stitches only on the flat top (so the wheel rim radius is small, its stitch sits 2 mm from the edge). A bigger "dome" was NOT done: it would carry the stitches off the surface. Diamond panel now has real raised cells (1.2 mm, R 0.9) with 1.9 mm grooves where the red stitches lie. Also fixed: wheel decoration no longer runs over the seat.
- Checks: all 3 colours watertight, black one fused solid; `/3d-print-test` 0 problems; CLI PLA 0.20 mm no support: 5h05m, 162.6 g (no price sheet -> no cost). Nothing print-tested. Preview `cad/keyholder/preview/render3d_iso_v2.png`.
- Left: owner's view; hub pad/spokes still low contrast; texture question (fuzzy skin on walls only vs pebble relief); time reduction; cost needs the price sheet.

## 2026-11-03 (cloud) — key holder (car upholstery): flat drawing approved ("ابدء") -> 3D v1 built
- Flat v5f approved by the owner. `cad/keyholder/keyholder3d.py` extrudes the flat layers (flat_preview.load_layers): black structure stepped by height (plate 4, panel 5.5, wheel rim 8, hub 9, seat sides 12, cushion/headrest 14), red raised stitching/strip/wheel mark (+0.8, strip to 9), white lettering (+3.5), swoosh, machine, chrome trim, strip stitching. 5 hooks of my own design (J: stem 28 mm out, 12 wide x 9 thick, 45 deg lip underside, round boss) fused into the black solid; 2 countersunk wall screw holes. Piece 300.2 x 150.8 x 32 mm, back on the bed, no supports. `make_3mf.py` (3 colours + tower).
- Checks: all 3 colours watertight (black = ONE fused solid; fixed pinch points with a 0.02 mm region overlap); `/3d-print-test` 0 problems (note: thin items near Z 5.8); CLI PLA Basic 0.20 mm, no support: 5h06m, 162.5 g (black 133.8, red 14.2, white 14.5). Cost NOT computed (price sheet missing in this session). Nothing print-tested. STL/3MF/renders stay local (derived from the owner's picture); only the code and the two preview renders are committed.
- Left: owner's look at the 3D renders (heights, hook shape, colours), time reduction ideas (plate thinner, lower seat), seam groove, price sheet for cost.

## 2026-11-03 (cloud) — key holder flat v4: seat and steering wheel redrawn from a 1.5x crop
- Owner: overlap between seat and wheel, and the whole seat was wrong. New `cad/keyholder/seat_wheel.py`: separate pieces (headrest, left bolster, plain centre panel, diamond panel with parametric lattice, right bolster, cushion, red piping, dashed red stitching) measured on a 1.5x crop; wheel = measured ellipse ring, dark airbag pad with silver ring, 3 spokes, buttons, red top mark, dashed stitch. Seat drawn over the wheel (as in the picture). Checked on a zoomed overlay: matches. Also earlier today: dashed stitching on the red strip, smoothed jagged outline. Preview `cad/keyholder/preview/flat_v4.png`.
- Left: owner's marks, then 3D (each piece gets its own relief height), J hooks, print test, cost.

## 2026-11-03 (cloud) — key holder flat v3: whole outline traced (skill 3d-picture-to-cad re-run)
- Owner asked to redo the drawing with the skill. Now traced by colour masks: outer silhouette (`trace_silhouette.py`: "not wood" mask, stays local), red strip, car swoosh. Machine/steering hub traced too but the result was ragged/missing the handwheel, so those stay clean parametric drawings. Seat/headrest/wheel inner edges are dark-on-dark (not traceable): measured by eye, checked on zoomed overlays. Lettering re-fitted (Upholstery 472 px wide, cap 78). `flat_preview.py <ref> <out> <trace.json>`; preview `cad/keyholder/preview/flat_v3.png`. Size 301 x 160 mm. Left: owner's marks, then 3D.

## 2026-11-03 (cloud) — key holder flat v2: red strip + car swoosh traced from the picture
- Owner: 3 colours for now, J hooks OK; circled the car swoosh and the red strip as wrong, asked to use the tracing method. `cad/keyholder/trace_keyholder.py` (colour masks, smoothed) -> local json (not committed); `flat_preview.py <ref> <out> <trace.json>` uses it. Overlay checked: both now match the picture. Preview `cad/keyholder/preview/flat_v2.png`.
- Left: owner's OK/marks on v2, then 3D heights, J hooks, print test, cost. Nothing 3D, nothing print-tested.

## 2026-11-03 (cloud) — car-upholstery key holder (seat + wheel + sewing machine + 5 hooks): flat 2D drawing v1
- Owner sent a new reference picture (1536x1024, AI render) + a master prompt (ONE printed piece, 300 mm wide, Bambu H2D). `cad/keyholder/flat_preview.py` draws it flat from clean shapes measured on the picture (seat, headrest, diamond quilt, wheel, arch + panel + recessed band, real-font lettering, car swoosh, sewing machine from a 3x crop, red strip, 5 hooks, 2 screw holes). Real size 300 x 156 mm (not 200 tall: the picture's proportions; hooks included). Preview `cad/keyholder/preview/flat_v1.png` (overlay on the reference kept local).
- Left: owner's marks on the flat drawing, colours (black/red/silver + brown band?), hook type (J printed in the same job), THEN 3D (relief heights), print test, cost. Nothing 3D yet, nothing print-tested.

## 2026-11-03 (cloud) — wrench key holder restarted from zero: wrench body traced from the picture
- Owner rejected the first by-eye build (wrong proportions: I had assumed a 2000 px wide picture, it is 2345 px). Deleted it (still in git history). New: `cad/wrench/` — `trace_wrench.py` extracts outline + orange band from the reference by colour masks (json committed), `wrench.py` builds layers (border, plate, orange band, screws, recessed 18-tooth ring), STEP/STL/renders in `cad/wrench/out/`, `cad/wrench_render3d.py` = lit three.js render in headless Chromium.
- Left (in order): owner approval of the body, then hooks (ball-tip, from the trace positions), split into printable parts, workshop (also traced layer by layer), brake disc/drum variants, validation. Nothing print-tested.

## 2026-11-03 (cloud) — wrench key holder: owner's order of work (hooks LAST, do not forget them)
- Owner: leave the hooks for the very end but do not forget them. Open hook issues: shorter and wider than the picture, ball too small from the front, curl should be slimmer. Proposed order (NOT yet approved by the owner, who said do nothing without his permission): split into printable parts, workshop (layer by layer), brakes, then hooks. Ring top edge and render shadows fixed (commits 0fd9d3a, 3d7755b).

## 2026-11-03 (cloud) — wrench key holder shrunk to 300 mm (same proportions)
- Owner: a long non-square piece fits the H2D up to 300-310 mm, so no split into parts. `LENGTH_MM=300` (310 possible), size 300 x 68.8 mm, Z: border 2 + plate to 5 mm, band +1, hooks 6 mm. Splitting is dropped. Hooks need rework at this size (stem only 5.5 mm wide: now one 2.4 mm hole each, pilot 1.8): still LAST on the list. Next steps need owner approval.

## 2026-11-03 (cloud) — version 2 = 300 mm wrench + workshop (traced), version 1 untouched
- Owner: keep the first version intact, make a second with the workshop; colours black/white/orange only (white instead of grey, orange instead of red), disc included, trace from the picture (no GPT drawing needed), and asked about raising the workshop (4 cm too small). Built `cad/wrench/workshop/` (trace + parametric disc/caliper, `--stretch`); both 1.0 and 1.5 rendered, owner to choose. Left: owner's choice of stretch, real font for WORKSHOP, parametric gear, relief heights per element, slicing/time, hooks (last), nothing print-tested.

## 2026-11-03 (cloud) — version 3 idea: fish-skeleton hooks on the wrench (preview only, owner has the designers' OK to adapt)
- Owner found two MakerWorld designs (fish-skeleton wall hook, 30 cm customisable wrench) and said the designers allow adapting parts but not selling the piece as is. Wrench design rejected as a body (too slim, no room for the workshop). Fish hooks: side profile is a J (stem on the wall 6 mm wide x 7.6 thick, curl standing out 29.4 mm, 33 mm hang); printed in the same job as the plate, no screws, no supports. `cad/wrench/workshop/v3_fish_hooks.py` builds v3 (v2 + 5 hooks at scale 0.8: 4.8 mm wide, 23.4 mm out, 27 mm hang; stem thickness = plate 5 mm); the profile json is third-party-derived and kept OUT of the repo (`--profile`). Fixed a bug (hook went 12 mm behind the wall). v3 is a local preview, not committed as files; waiting for the owner's OK. Whole piece 300 x 116 x 23.4 mm.

## 2026-11-03 (cloud) — clean vector workshop (owner: my traced drawing and the other one each have good and bad parts)
- Owner's notes on the traced workshop: lifts and roof outline good; car had no headlights, disc muddy, jerry cans wrong/unclear, "more" (not yet sent). Plan approved: wrench body from the found wrench + workshop + fish hooks at scale 1.0 (not modified, owner: if strong do not change) + optional text.
- New `cad/wrench/workshop/vector_workshop.py`: workshop redrawn as clean 2D shapes (3 colours) with layout measured on the reference; kept the traced lifts + house outline; real font lettering, parametric gear, clear jerry cans, 6 spanners, cabinet, car with orange headlights, ceiling lamp, filters, clean disc + caliper; `S` = vertical stretch (1.5 default idea). Previews in `cad/wrench/workshop/vector_preview/` (flat S1.5, S1.0 + overlay on the reference). Next: owner's feedback on the flat drawing, THEN extrude to 3D (min feature 0.7 mm), then the new wrench body, fish hooks (scale 1.0), text, slicing/time.

## 2026-11-03 (cloud) — vector workshop: car taken from the owner's second picture, stretch chosen 1.25
- Owner: take ONLY the car from the other drawing; I pick the stretch. `trace_car.py` traces the white car (dark windscreen/grille/lights = holes, mirrors, roof arc; the floating bar above it dropped); the json stays local (the picture's origin is unknown, repo is public); `vector_workshop.py <ref> <out> <S> <car_trace.json>`. Stretch 1.25: house ratio about 2.4:1, close to the other drawing (2.5:1), details keep their size without big empty gaps; 1.5 left too much empty wall, 1.0 too low. Preview `vector_preview/vector_S1.25_car2.png`. Next: owner's OK on the flat drawing, then 3D, new wrench body, fish hooks 1.0, text.

## 2026-11-03 (cloud) — workshop approved flat, now in 3D; skill `3d-picture-to-cad` created
- Owner approved the clean vector workshop (lifts redrawn clean with details, car symmetric from his second picture, stretch 1.25) and asked for a skill so the mistake (auto-traced details, 3D before 2D approval) is not repeated: `.claude/skills/3d-picture-to-cad/SKILL.md` (+ line in CLAUDE.md). Plan approved: 1 workshop 3D (done: `workshop_v4.py`, black base + white/orange +0.8, min feature 0.7 mm), 2 new wrench body from the found wrench (300 mm, plain: NO text, the word WORKSHOP may change later), 3 fish hooks at scale 1.0, 5 3MF in 3 colours + slicer estimate. Next: step 2, show before 3.

## 2026-11-03 (cloud) — v5: new body (found wrench outline) + clean workshop + fish-profile hooks; 3MF + slice
- `cad/wrench/workshop/v5_new_body.py`: body from the found wrench's silhouette (300 mm, straight handle 15 mm tall, 12-point ring, border + plate + orange band, plain: no text/screws), workshop v4 sitting on the handle (shelf now reaches the ground line), 5 J hooks (fish side profile, scale 1.0, x = -80..80 pitch 40) with a 45 deg underside slope under the tip because printed plate-down the tip is an 11 mm cantilever; the slope must reach the J floor (a corner 0.24 mm away made a floating island = slicer warning). Piece 300 x 109 x 29.3 mm, all watertight, Z starts at 0.
- `make_3mf.py`: 3-colour Bambu 3MF (1 black, 2 white, 3 orange), PLA template, tower at (150, 230, w 30). CLI estimate PLA 0.20 mm, no support: 1h45m, 51.2 g (black 45.8, white 2.1, orange 3.3); body+workshop alone 1h16m / 42.4 g, hooks add about 30 min (tall layers). Cost NOT computed: price sheet missing (ask the owner for `3D_ZONE_TECH_Filament.xlsx`). The 3MF and renders are NOT in the repo (third-party-derived); inputs stay local (`--outline`, `--profile`, `--car-trace`). Nothing print-tested.

## 2026-11-03 (cloud) — v5 update: jaw mirrored (short prong at the bottom), workshop 1.25x uniform
- Owner: the short jaw prong goes at the bottom (mirrored the body about the handle's centre line, `FLIP`), and the total height (109) was too small -> whole workshop 1.25x uniform (`--ws-scale`, about the house bottom line): workshop 187 mm wide (equals the straight handle), piece now 300 x 124.3 x 29.3 mm. Disc plate now rests on the border layer (z 2) instead of starting in the air at z 5. CLI estimate PLA 0.20 mm, no support, tower on: 2h01m, 64.2 g (black 57.2, white 3.2, orange 3.7), no slicer warnings. Cost still needs the price sheet. Nothing print-tested.

## 2026-11-03 (cloud) — v6: owner-approved picture applied to the design, word changed to "Aldawayme"
- Flow that worked: flat picture (mock) -> owner's marks -> picture again -> design once. Decisions: handle 20 mm (widened downward, eased into the necks), ring head +15 % (piece 302.4 mm long), disc 75 % (now a parameter `disc_scale` of the vector workshop, default 1.0), ONE continuous orange line (lower jaw prong -> around the jaw slot -> U-turn at the upper prong -> handle top edge -> 240 deg around the ring head); the ring wall is only 3-5 mm so around the ring head there is no plate level: the line runs on the border level (1.4 mm) and the plate is cut away there (otherwise scalloped slivers made the line look dashed). Word: `text` parameter of the vector workshop (Noto Sans Bold, cap height 36 view units, stripes follow the word's width).
- `cad/wrench/workshop/v6_final.py` (inputs local: outline, hook profile, car trace). Piece 302.4 x 129.3 x 29.3 mm, all watertight, Z from 0. CLI PLA 0.20 mm, no support, tower on: 2h09m, 67.8 g (black 61.0, white 2.9, orange 3.9), no warnings; cost needs the price sheet. Nothing print-tested; the 3MF is not in the repo (third-party-derived).

## 2026-11-04 (cloud) — v7: big version (about 1 m, no hooks) in 4 interlocking columns
- Owner: a big version up to 1 m, no hooks, assembled by INTERLOCKING (no glue/screws between pieces). Facts: without hooks the piece is only 102.7 mm tall at 1x, so at x3.3 (997.8 mm wide) each column fits the bed (heights 257.6 / 308.7 / 316.0 / 261.1 mm; the earlier idea of 8 pieces and a roof cap was wrong). Z for the big size: border 3, plate 9, house base 11, relief +2.5, orange line +1.8 mm (only XY is scaled).
- Interlock = dovetail puzzle tabs in the PLANE (neck 9, head 15, length 11 mm, 0.3 mm clearance), pressed in from the front, 3 per seam. A sliding dovetail across the thickness cannot print plate-down (its lower flank hangs in the air). Tabs/sockets must not sit under raised relief (white/orange/line): the print test caught white hanging over a socket at the left/right posts; tabs are now placed only where nothing is raised above (`seam_ys`). Wall: 2 countersunk M5 holes per column on the handle centre line. Columns are hung by their own screws; the tabs align and stop shear.
- Code: `cad/wrench/workshop/v7_big.py`, `make_3mf_big.py` (inputs local). All 12 STLs watertight; `/3d-print-test` per column: 0 problems (column 3: two harmless notes). Seams cross the word and the car (hairline 0.3 mm). Nothing print-tested.

## 2026-11-03 (cloud) — colour options for the v6 piece (from the owner's stock sheet)
- Stock (PLA+: white, black x2, red, blue, yellow, green, orange, purple, pink, cyan, grey; Silk PLA gold/silver/bronze/copper/rose gold + bicolours; PETG, AD-PETG, TPU...). Rendered 4 palettes of the same geometry (only the colour changes, no design change): 1 Black/White/Red, 2 Grey/White/Yellow, 3 Blue/White/Orange (all PLA+), 4 Black PLA+/Silk Silver/Silk Gold. `cad/wrench_render3d.py` takes an optional palette JSON (4th argument, with "metal" list). Owner to choose; then only the 3MF's filament colours change.

## 2026-11-03 (cloud) — v6: wall screw holes added (owner: "you forgot the screw holes")
- Two countersunk holes on the handle's centre line at x = -100 and +100 mm (200 mm apart): through hole 4.2 mm, 45 deg countersink 8.5 mm head (2.2 mm deep), for 4 mm wall screws (plugs needed in plasterboard). The orange line keeps 0.6 mm clear of the heads. Picture shown first, then built in `v6_final.py` (`SCREW_XS/SCREW_D/SCREW_HEAD_D`). The touching border/plate shells shared the hole edges (non-manifold STL), so body black is now ONE fused solid. All parts watertight, size 302.4 x 129.3 x 29.3.
- Owner asked for NO print test / cost rerun this time: `/3d-print-test` and `/3d-cost` were NOT re-run after this change (the holes only remove a little material; earlier run: 0 problems, 2h09m, 67.8 g). Nothing print-tested.

## 2026-11-03 (cloud) — price sheet received; Aldawayme piece costed
- Owner uploaded `3D_ZONE_TECH_Filament.xlsx` to this cloud session (copied to `cad/config/filament_prices.xlsx`, git-ignored; `openpyxl` installed in `.venv-cad`). Ran the full flow on the v6 piece: `/3d-print-test` = 0 problems, then CLI cost with the sheet (PLA Basic priced as PLA+): 2h09m, 67.8 g. The money figure was given to the owner in chat only (the repo is public). Studio's estimate is usually ~5 % higher than the CLI.

## 2026-11-03 (cloud) — skill `3d-print-test` (printability check), the "سكيل فحص" the owner meant
- "سكيل" = skill (I first read it as scale and searched the wrong thing; no record of it in the repo or the other sessions I could read). Built `cad/print_test.py` + `.claude/skills/3d-print-test/SKILL.md` (+ line in CLAUDE.md): layer-by-layer (0.4 mm) plate-down check for open mesh, off-bed, too big, tiny bed contact, floating islands, overhangs over 45 deg, features thinner than 0.7 mm; optional `--slice` relays Bambu Studio warnings. Calibrated on the hooks: no slope -> problem, first slope (0.24 mm gap) -> floating island (same as the slicer warning), fixed hook -> clean. Whole v6 piece: 0 problems, 8 s; notes: five 0.4 mm overhangs, thin tapers of the orange line at Z 3. Also `make_3mf.py --scale` (optional, default 1.0).
- Owner's rule added to the skill: test with no problems -> run `/3d-cost` automatically on the same files; with problems stop and report first.

## 2026-11-03 (cloud) — little-prince lamp at 150 mm: files built
- Owner chose size 150 (X/Y x1.5, height unchanged) and the option-4 diffuser. `cad/lamp150.py`: diffuser (white disc 118 mm x 1.34 + black relief 0.67, 2 colours, ar/en) -> `cad/print_files/lamp_150/diffuser_{ar,en}.3mf` (own geometry, committed); case 150x150x80 and stand 105x105x5 from the owner's licensed 3MF are written to a scratch dir only (NOT committed: public repo, third-party design).
- CLI estimates (PLA, 0.2 mm, no support, no tower): case 2h52m/95 g, diffuser 0h26m/20 g, stand 0h28m/24 g = about 3h46m / 139 g per lamp. 200 mm (x2 XY): case 4h56m, diffuser 0h42m, stand 0h47m = about 6h25m. Uniform 2x incl. height would be 5.8x the original case time. Nothing print-tested (printer not here). Open: LED choice and fit of the larger case/stand, diffuser fit tolerance in the case opening, real values in the JSONs.

## 2026-11-02 (cloud) — little-prince lamp (Bambu 3MF from the owner): diffuser to carry name/date/weight/time/length
- 3MF has 3 plates: light case (~100x100x80), led stand (disc 70x70x5), light diffuser (disc ~79 mm x 1.34 mm, logo relief 0.67 mm). Owner holds the licence to modify. Decided: remove the logo, two versions (full Arabic / full English); layout via GPT prompt `cad/plaque/gpt_prompt/diffuser_layouts_PROMPT.md` (6 options). Owner chose GPT option 4 (bear on top) with the decoration as in the picture, test values (changeable), bigger text. Built `cad/diffuser.py` (+ `cad/plaque/diffuser_ar.json` / `diffuser_en.json`, previews in `cad/plaque/diffuser/`): bear/stars/icons traced from the picture, text from fonts. Left: owner's yes on the preview, then write the relief into the lamp 3MF (diffuser plate, white disc 1.34 + black relief 0.67).

## 2026-11-02 (cloud) — plaque fixing in the backlit box (nuts + screws) built; leg hinge found wrong
- Owner chose option A: two hex nuts planted in the back of the plaque (frame band, left/right) + screws from the back through two posts in the box. `fix_spec/fix_points/hexagon` in `newborn_plaque.py`; M3 for >= 250 mm, M2 below (the frame band scales with the size: 11.2 / 8 / 6 mm). Checked: pockets inside the band (walls 2.7 / 1.85 / 0.85 mm), no light leaks, watertight, zero plaque/box interference; 200 mm plaque 3h42m / 107 g, box + leg 1h40m / 81 g. Regenerated plaque 3MFs (ar/en), `glow_box_*`, `glowcap_box_and_leg_*`.
- Owner asked "are you sure about the leg motion?": a simulation showed (1) the screw axis is perpendicular to the back -> the leg turns in the back's plane, it cannot prop the plaque; (2) the leg is 2.8 mm too short. Fix proposed (drawing shown, awaiting yes): bracket with two ears + horizontal M3 pin on the boss, M3x5x5 brass insert (owner has 200 pcs, Temu) pressed in with a soldering iron (owner has one), leg +2.8 mm. Lesson: never call a mechanism "right" before simulating it; label claims "simulated" / "tested".
- Research (printed screws): printed threads only from about M8 up, PETG, 4-6 walls, 0.3 mm clearance; M3 printed is unreliable; metal nuts/inserts for repeated use. Twist-lock / bayonet printed designs exist (to test later on coupons).

## 2026-11-02 (cloud) — backlit set: box + leg now also as a ready 3MF
- Owner: "why is the box not in the file?" The plaque 3MF only had the plaque; box and leg were STL only. `newborn_plaque.py` now also writes `glowcap_box_and_leg_<size>.3mf` (box and leg side by side, one colour, no tower) next to the plaque 3MF; copied to `cad/print_files/glow_cap/` for 150/200/280. CLI: 200 = 1h37m / 80 g, 280 = 2h32m / 135 g. One file with plaque + box would not fit one plate (box ~ plaque size, bed 325 mm).

## 2026-11-02 (cloud) — first real Bambu Studio slice (owner, laptop): two nozzles win
- Owner opened `glowcap_plaque_ar_200.3mf` in Studio: the orange purging warning disappears after opening Purging volumes -> OK (Studio auto-calculates colour-based flush volumes, left extruder 150-625 mm3). Slice: 3h55m / 110.9 g with Studio's auto grouping (1+2 left, 3+4 right); 4h05m / 112.4 g with all colours on the left nozzle. Two nozzles save ~10 min (my CLI test claimed the opposite: trust Studio). CLI estimates are ~5 % low (flush volumes). Open: does a freshly opened regenerated file still warn? (owner to check); does 280 mm get two nozzles (tower position)? Owner still to send a Studio-saved 3MF (`test_fixed.3mf`) as ground truth if the warning persists.

## 2026-11-02 (cloud) — purging warning really fixed in all 3MFs
- Owner: no more warning in any file. The earlier "absurd estimate" (5 million hours) was a random CLI glitch, NOT caused by the 32-value flush matrix (re-tested: the doubled matrix slices fine twice, 3h41m / 107 g). Re-applied the `threemf.py` change and regenerated all 18 print 3MFs (standard, glow_cap, rails_280, lit_280, train_lit; ar/en). Verified each: 32 flush values, 4 filaments, tower on. Lesson: a single odd CLI result is not proof; re-run before reverting.

## 2026-11-02 (cloud) — two nozzles tested: no gain
- Owner asked why we do not use both H2D nozzles. Added `--nozzle-map 1,1,2,2` to `cad/bambu_slice.py` and sliced the 200 mm plaques with the plate at x=27..227 (the right nozzle cannot reach x<25). Lit (PETG): one nozzle 3h41m, maps 1,1,2,2 = 3h50m, 1,2,2,1 = 3h46m, 1,1,2,1 = 3h43m. Plain (PLA): one nozzle 2h30m, 1,1,2,2 = 2h29m. The time is dominated by the big base layers, not by colour swaps, so the second nozzle gives nothing (estimates) and costs plate position freedom; keep everything on the left nozzle. Re-test on the real printer (the slicer's estimate of nozzle switching may differ).

## 2026-11-02 (cloud) — Bambu Studio "Partial purging volume set to 0" warning: left as is
- The owner opened `glowcap_plaque_ar_200.3mf` in Bambu Studio (screenshot): H2D, 4 PETG filaments, 0.24mm Standard, tower right of the plaque: all OK, plus an orange warning about the purging volume (the 3MF carries one 4x4 flush matrix, the H2D has two nozzles). Doubling the matrix (32 values) made the CLI slice give absurd results (5 million hours), so it was reverted. Keep the 16-value matrix (200 mm lit: 3h42m / 107 g). The warning is harmless while all colours print on the left nozzle (filament map all 1). Do not touch the flush matrix without re-slicing.

## 2026-11-02 (cloud) — backlit original plaque marked FINAL
- Owner: keep the bear-head bridge (16.7 mm at 150 mm) as is. Lit plaque (`cad/print_files/glow_cap/`) is final: plaque 3MF (ar/en, 150/200/280), `glow_box_*`, `back_leg_*` (M3 x 12 screw + M3 nut + cord). Laptop copy: GitHub Desktop -> Fetch/Pull origin in `D:\github\-sharpseek-api` (a cloud session cannot write to the laptop; Remote Control does not support Windows). Next: stand for the plain plaque (no box).

## 2026-11-02 (cloud) — original lit plaque re-verified and regenerated
- Owner asked if the lit plaque was ready from the start: regenerated `glowcap_plaque_{ar,en}_{150,200,280}.3mf` with the current generator (tower placement, 4-filament settings), `check_plaque.py` OK (no leaks, watertight); bridge 12.6 mm at 200/280, 16.7 mm at 150 (risk). 200 mm slice at 0.24 mm: 3h41m / 107 g / 0.83 JOD (others from the README, 0.20 mm: 150 2h02m, 280 6h14m). Nothing print-tested.

## 2026-11-02 (cloud) — original plaque, backlit: folding leg on a screw + nut (decision)
- Owner (said: forget the train, work on the original "Yousef" plaque; guaranteed solutions, no untested mechanisms): stand for the backlit box = a flat leg on an M3 screw. `make_lit_box(..., leg=True)` adds a 14 mm boss high on the back panel (0.82 x size from the bottom) with a hex pocket for an M3 nut (opens to the cavity), a 3.4 mm screw hole through boss + back panel and a 2.5 mm cord hole below it. `make_back_leg(size)`: bar 14 x 4 mm, length 0.82 x size from pivot to foot (flush with the bottom edge when folded), opens 24 degrees, plaque leans 12 degrees, foot about 96 mm behind (280). Sizes 150/200/280 in `cad/print_files/glow_cap/` (`glow_box_*`, `back_leg_*`).
- Slice (0.24 mm, PETG): box 280 = 2h20m / 125 g; leg 280 = 14 min / 10 g. Fastest of the three stand options (leg ~ +14 min; separate slotted base ~ +45-60 min; wedge box 1-2 h+).
- Rejected/shelved (see STANDS.md): feet, rails, easel, clip, slotted pockets with print-in-place leg, hooks, flexible hinge, foot lip. Research notes: slot base clearance 0.2-0.4 mm is the proven range; PETG living hinges fail < 1000 cycles.
- Plain (non-lit) original plaque stand: still open (no box -> no boss); not decided.

## 2026-11-02 (cloud) — owner looking for an older plaque: standard bear plaque preview
- Owner forgot which chat had a plaque designed before the train; likely the standard bear + 4 boxes plaque. Added `cad/plaque/example_ar_preview.png` (from `example_ar.json`, 280). Waiting for the owner's picture to confirm.

## 2026-11-02 (cloud) — base now a real-looking track, plaque UPRIGHT (no tilt)
- Owner: the ladder looked like a fence/comb (my invention: wide sleepers + a tail behind the rear rail). Rebuilt `make_track_base`: two thin 5 mm rails on top of 14 narrow close sleepers (6 mm wide, 2.5 mm high, pitch ~12.7), sleepers stick out 12 mm equally beyond both rails (owner: a bit wider), no tail; centre sleepers left out for the USB-C cable. Rails 22 mm apart, base 171 x 51 mm (centre of mass +-25 mm inside).
- Owner: NO tilt at all -> `LIT_TILT = 0` (feet stands still use TILT 12). Locked fit (tray vs base) 0 mm3 interference; +-1.5 mm lift/push collides (locked). Preview: `cad/plaque/train_lit_assembled_preview.png`.
- Open risk: upright 285 mm plaque on a 35 mm deep base (centre of mass +-17 mm inside) may tip if bumped; to judge with the printer. Renders of the assembly (three.js in headless Chromium, plain lighting, not photoreal): `cad/plaque/train_lit_render_front.png` / `_back.png`. Plaque tongues (printed in the plaque 3MF) not re-checked against the pins at 0 tilt (same geometry as before, tray check only). print_files not regenerated, no re-slice.

## 2026-11-02 (cloud) — owner's explainer picture matched to the build; USB-C slot 14x8; wavy edge option
- Owner's picture = the same lit train design. Checked: "كغم" already correct, date is only an example, hooks/slide-left as built, body stays PETG blue (owner choice), LED layout left for later. Picture has a wavy (cloud) bottom edge, the build has a flat track strip.
- Done: tray USB-C slot enlarged to 14 x 8 mm (z 3-11). New JSON key `"track": false` removes the flat strip (wavy traced edge), default stays true.
- `track: false` first left the two hook tongues floating (not under wheels). Fixed by owner's choice: tongues/pins moved under two wheels (big engine wheel and 3rd wagon wheel, `WHEELS_LOCK_U`), applied to plaque, tray back tabs and base hooks via `keys=(xL, xR)` (pair no longer exactly symmetric, ~2 mm). Example JSON now has `"track": false`.
- Left: `cad/print_files/train_lit` NOT regenerated/re-sliced yet; fit check (entry/lock/interference) not re-run for the new positions; sleepers are no longer under the hooks (hooks sit on the rails, fine).
- Printer still at customs (owner, 2 Nov). Nothing print-tested.

## 2026-11-02 (cloud) — hook locking: Γ pins into L-shaped keyhole slots, slide 8 mm left
- Owner's spec (drew an upside-down L): four hooks, each on a long rail only; they ENTER holes in the plaque and the tray; lower the parts, then slide left/right. Built: base = ladder (two rails, six even sleepers + tail) with 4 hooks (stem + 3 mm pin + 6 mm head); plaque: two 18 mm tongues, 10.3 mm below the plaque, with an L-shaped keyhole slot (wide entry leg 6.8, narrow leg 3.4, slide 8 mm); tray: two back tabs (3 mm thick) with the same slots, and cut-outs in the lowest wall for the tongues. Everything is defined in a tray frame and mapped with `pin_frame()` (tilt 12 degrees, tray hangs on the pins).
- Software fit (`scratchpad/fit2.py`): zero interference at entry / halfway / locked, collision at the ends of the slot and for lift/pull/push. Base 280: 0h40m / 19 g; 200: 0h35m / 15 g. Totals about 6h34m (280) and 4h22m (200). Plaque not re-sliced after the slots (should be about the same).
- Not print-tested; pin 3 mm in PETG and the 0.2 mm slot play to be checked on the printer.
- Owner rule learned: do NOT edit before the owner confirms a drawing/understanding when they say so; they draw what they mean.

## 2026-11-02 (cloud) — base: posts clear of the rails, peg in the rear half
- Owner: the locking nubs must be 2 in front + 2 behind at equal places (not one on a sleeper and one on a rail), one holding the plaque, one the back. Slot moved 8 mm back so the posts stand between the rails; peg now in the rear half of the slot floor (tray hole at tray depth 1.4-8.0), the plaque's tongue pocket in the front half. Base depth 62 mm. Base 280: 0h46m / 24 g, 200: 0h40m / 20 g. Totals about 6h38m / 4h26m. Fit check: no interference.
- Also: `scratchpad/render` (three.js in headless Chromium) can make clean renders of any STL; not photoreal.

## 2026-11-02 (cloud) — locking for BOTH tray and plaque + even sleepers
- Owner: locking must hold the back (tray) AND the plaque; sleepers evenly spaced. Done: 6 even sleepers (pitch (L-12)/5), locks at +-1.5 pitch (`lock_x`); tray: 2 key holes + 2 tongue cut-outs; plaque: 2 tongues (12 mm) in its opaque base layer, 5.3 mm below the plaque; base: pegs + pockets. Slot floor made perpendicular to the tilted slot (fixed a 1388 mm3 interference). Assembly check script in scratchpad (tray/plate/base interference < 3 mm3).
- Base 280: 0h44m / 22 g, 200: 0h37m / 18 g. Totals about 6h36m (280), 4h23m (200). Not print-tested.

## 2026-11-02 (cloud) — base = ladder (two rails + fused sleepers + locking blocks)
- Owner's last-try spec: two long beams, cross beams fused with them, locking protrusion on top. `make_track_base`: rails 7 mm wide, 6 sleepers 12 mm, two of them (at +-key_x) carry the slot walls + a 6 mm peg. Floor 5 mm. Base 280: 0h43m / 21 g, 200: 0h36m / 17 g (the slab+rails version was 1h00m / 51 g). Totals about 6h35m (280) and 4h24m (200).
- Not print-tested; peg/hole fit and rigidity of the ladder to be checked on the printer.

## 2026-11-02 (cloud) — base = slab + two rails (as in the owner's explainer picture)
- Owner sent a product explainer (front plaque + LED + hollow back; plaque slides into the rails of a track base; one colour is enough). Base profile is now a thin slab (8 mm) with two rails that are the walls of the slot; sleepers off. Base 280: 1h00m / 51 g, 200: 0h42m / 33 g. Totals about 6h52m (280) and 4h27m (200).
- Tray + base lock with two 6 mm pegs. Not print-tested.

## 2026-11-02 (cloud) — railway-track base with locking pegs
- Owner's idea: base shaped like a railway track and locked to the tray. Done: two rails on the rear deck + two 6 mm pegs in the slot floor that enter two holes in the tray's lowest wall (`key_x`). Sleepers (cross grooves) measured +12 min -> optional (`sleepers=True`). Base 280: 1h11m / 62 g (plain was 1h04m). Totals about 6h57m (280) and 4h32m (200).
- Not print-tested; peg/hole fit (6.0 vs 6.6 mm) to be checked on the printer.

## 2026-11-02 (cloud) — base: arches measured, shorter base instead
- Arch windows under the base (`make_foot(arches=True)`): measured -4 g, +7 min -> off. Base length 0.8 -> 0.6 of the plaque width: 280: 1h04m / 60 g, 200: 0h43m / 38 g. Totals: 280 about 6h50m / 193 g / 1.35 JOD; 200 about 4h28m / 118 g / 0.86 JOD. Print files updated.

## 2026-11-02 (cloud) — backlit train: cut print time (owner: "time is our weak point", said many times)
- 0.24mm Standard profile instead of 0.20; tray now has 2 mm walls and an open back with three LED bars (73 -> 43 cm3); base is one long piece. 280: plaque 4h14 + tray 1h32 + base 1h24 = about 7h10m (was 8h18m). 200 mm: 2h38 + 1h07 + 0h56 = about 4h41m. Files in `cad/print_files/train_lit/` (280 and 200).
- Lesson: when the owner says time matters, optimise it without asking first. Still heavy: base (79 g at 280) - ideas: arch windows, lower tilt. Not print-tested.

## 2026-11-02 (cloud) — backlit train: one long base + print files
- Owner chose ONE long base (not two feet), slim: `make_foot(..., length=)` now builds a single 229 x 54 x 22 mm base (stability margin 20 mm). Light tray fixed to follow the full silhouette (it was following the plate with openings, 214 cm3 -> 72 cm3).
- Estimates (H2D, tower, +-20 %): plaque 4h37m / 81 g / 0.57 JOD; tray 2h12m / 79 g / 0.59; base 1h29m / 77 g / 0.55. Sum about 8h18m, 238 g, 1.71 JOD (LED strip extra). Files in `cad/print_files/train_lit/`.
- Left: owner feedback; the tray and base are heavy for what they are (could lighten); nothing print-tested.

## 2026-11-02 (cloud) — backlit (glow_cap) train
- `example_train_lit_ar.json`: layout train + glow_cap + theme `train_lit` (slots: PETG Blue opaque body, AD-PETG translucent white / yellow / orange-red for the bear; owner dislikes a black body for a baby). Added a flat track strip under the wheels (flat bottom edge), `make_lit_tray` (light tray that follows the outline, 14 mm deep, LED on its back panel, USB-C slot) and feet for it (`make_foot(size, thickness)`).
- Slice (280 mm, prime tower x=288, left nozzle): 4h37m / 81.4 g / 0.57 JOD (+-20 %). Tray and feet not sliced yet. Not print-tested.
- Preview used the wrong palette before (white outside); fixed: 3MF slot colours are now the train_lit ones.

## 2026-11-02 (cloud) — train: real stock colours + rounded name font
- Price sheet received again (git-ignored in `cad/config/filament_prices.xlsx`). Stock has NO cream, navy or tan: train theme now PLA+ Blue / PLA+ White / PLA+ Yellow / Wood PLA (bear). Horse: PLA+ Blue, White, Cyan, Yellow. Night theme updated the same way.
- Owner prefers the rounded name font of the picture: new kind `"name"` uses Baloo Bhaijaan 2 ExtraBold (`cad/fonts`, OFL) for Arabic names; values/labels keep Noto Kufi.
- Left: slicing estimate with prime tower (4 filaments: Blue, White, Yellow, Wood PLA), owner's feedback.

## 2026-11-02 (cloud) — "train" layout is now traced from the owner's flat picture
- The owner rejected hand-drawn shapes ("do not draw at all, trace this"). The Gemini flat picture of the train is traced with `cad/trace_layers.py` (options `cad/plaque/train_trace_opts.json`) -> `cad/plaque/train_layers.json`; `"layout": "train"` loads it (the old hand-drawn one is `layout_train_drawn`, unused). Name and the four values are re-drawn with the fonts (recessed in the cream); labels and icons stay as traced. Bear: tan slightly higher, its darker details lower (same filament).
- Result ~ 280 x 162 mm at size 280, 4 colours, watertight. Feet stand only. Not sliced yet.
- Rule from the owner: never invent shapes; trace the pictures they provide (ask Gemini for flat 4-colour versions).

## 2026-11-02 (cloud) — horse stands on a rocker runner
- Owner: "why not keep it a rocker?" -> `make_rocker_runner` (horse layout only): curved runner 220 x 50 mm (14 mm below the plate edge, 8 mm grip) with a 4.2 mm slot along the top; the flat plaque slides in and rocks (CoM about 90 mm above the bottom, curvature radius about 300 mm -> self-centring). Exports `rocker_runner_<size>.stl`, print lying on its side. Single colour PLA+ estimate: 1h29m / 78.7 g / 0.60 JOD.
- Warning from the slicer: "floating cantilever" (the 8 mm slot ceiling bridges across the arc); not print-tested. Sideways stability of a 4 mm plate in a 50 mm runner is unverified.
- Left: owner feedback; a bigger flat picture of the horse for a cleaner head; estimate of the plaque itself with the prime tower.

## 2026-11-02 (cloud) — "horse" layout traced from the owner's mock-up (rocking horse)
- Owner sent a Gemini image of a rocking horse (layered cream horse, blue mane/tail, navy saddle with the name, curved navy rocker carrying the 4 info columns) and asked not to simplify ideas. Hand-drawn shapes were too crude, so `cad/trace_layers.py` now converts a picture into colour layers (nearest palette colour, glow absorbed, smoothed, contourpy polygons) -> `cad/plaque/horse_layers.json`; `"layout": "horse"` (theme `horse`: navy / cream / blue / yellow) loads it and re-draws the name and info text with the real fonts.
- First result looks like the picture but the head/muzzle are rough (source crop is only ~620 px). Better: ask Gemini for a big flat front view of the horse alone, trace again.
- Open problem: a flat plate cannot stand on the curved rocker edge -> needs a stand decision (feet slot does not fit a curved bottom). Not sliced, not discussed with the owner yet.

## 2026-11-01 (cloud) — "train" layout (owner picked this design from a Gemini mock-up)
- Round "night" layout was rejected ("looks bad"). Owner sent a Gemini image: steam engine pulling 4 wagons (date, time, length, weight cards), dome with the name, sleeping bear, moon, stars, pedestal slab. Built as `"layout": "train"` (`cad/plaque/example_train_ar.json`, theme `train`: navy / cream / yellow / tan). Bear kept, smoke cloud kept.
- Flat shapes only, 4 colours, text and icons recessed in cream (no extra colour changes). Size 280 gives about 285 x 190 mm. Meshes watertight. Feet stand only. Not sliced yet (no time/cost), stock colours for cream/tan are placeholders in THEME_FILAMENTS.
- Left: owner feedback on the preview, slicing estimate with tower (plate is ~5 mm wider than `size`, tower still fits at 280), print_files, optional lit/glow check of this layout.

## 2026-11-01 (cloud) — new "night" layout (round, moon, sleeping baby, hanging tags)
- Owner liked an AI mock-up (round plaque on an oval pedestal, crescent moon, name cloud, 4 hanging star/tag cards with strings, sleeping character). Built as `"layout": "night"` (example `cad/plaque/example_night_ar.json`, theme `night`: navy / white / yellow / skin). Decisions: baby instead of bear, strings kept, no bow, pedestal kept, simple 4 colours.
- Feet stand only (round shape has no straight side bands for rails). Meshes watertight; 280 mm and glow_cap 200 mm generate. Text on the tags is small: use size >= 200. Not sliced/cost-checked yet; footprint pad is the ellipse on the right cloud; owner has not yet seen/approved the preview.
- Left: owner feedback on the look, stock colours for the night theme (navy / skin), slicing estimate with tower, regenerate print_files.

## 2026-11-01 (cloud) — state of the project
- Sizes: any up to ~290 mm coloured (max with prime tower); 150/200/250/280 proven. 300 mm fails in Bambu Studio (no room for the tower). Test file for 290 mm sent to the owner; result pending.
- 3MF now carries 4 filaments + slot colours + prime tower; Bambu Studio opens it with the 4 colours (confirmed by the owner). Estimates vary +-20 % run to run.
- Six colour themes (blue, pink, green, purple+gold, sky, black+gold) built; baby boy / girl characters built (small, may be enlarged); owner to choose.
- Stands: slotted feet (default), rails + bridge with folding leg (280 mm), clip, easel. Nothing print-tested (printer not delivered).
- Windows: `cad/bambu_slice.py` works with the installed Bambu Studio (laptop session, commit eef8ef5).

## 2026-11-01 (laptop) — Windows slicing test
- Slicing the 150 mm plaque with the embedded 3MF settings: 1h58m / 64.8 g (standard), 2h45m / 63.0 g (glow_cap); no warnings.
