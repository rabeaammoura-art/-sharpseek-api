# Decisions (agreed with the owner)

## Ruler: follow the MakerWorld "Personalizable 15 cm Ruler" for numbering and thickness (agreed, NOT implemented yet)
Reference file: rulercustom.3mf (MakerWorld). Measured on it: plate 1.6 mm, 2.0 mm total with the raised strip; ticks and numbers 0-15
are painted white on the flat top surface (3150 painted faces), not raised shapes; the name is a separate white part. Sliced on our H2D 0.4 /
0.20 mm profile: 15 min, 7.5 g.

Agreed changes, ruler only (tag, pencil and bottle stay as they are, their files were not compared yet):
1. Ticks and numbers become flat, painted into the top surface (same height as the body) instead of raised 0.4 mm white shapes.
   Reason: our 0.5 mm raised lines are thinner than the 0.4 nozzle can print reliably, the weakest spot for the first print.
2. Total thickness 2.0 mm like theirs (now 2.8 mm for 2/3 colours and 3.2 mm for 4 colours).
3. Art, motifs, name and layout do not change.

Status: IMPLEMENTED (ruler only). layout.py: RULER_TOP = 2.0 (every colour ends at 2.0 mm, slab 1.6 + 0.4 colour layer) and the body is always a
colour region so ticks/numbers end flush with it. Tests pass. Other pieces unchanged.

Result, cars theme, H2D 0.4 / 0.20 / Generic PLA: 2 colours 43 min / 19.3 g (was 1h01m / 23.3 g), 3 colours 46 min / 20.1 g (was 1h11m / 25.7 g),
4 colours 51 min / 21.3 g. Not printed yet.

Current ruler numbers (H2D 0.4, 0.20, Generic PLA, 6.951 JOD/kg), cars theme: 2 colours 1h01m / 23.3 g / 0.20 JOD, 3 colours 1h11m / 25.7 g / 0.22 JOD.

## Direction for the first print (agreed): use tested, already-printed designs
Do not modify our own pieces further for now (no pencil tunnel / tag loop changes). The first print uses the three tested MakerWorld files the owner
provided: Personalizable 15 cm Ruler (rulercustom.3mf), Mariachi Bag Tag (mariachi.3mf), Customizable Pencil Topper with emoji (20Penciltopperwthemoji.3mf).
Our generator and its pieces stay in the repo unchanged (the ruler change above is already in it, not used for the first print).
Sliced on our H2D profile (0.4, 0.20, Generic PLA): ruler 15 min / 7.5 g, Mariachi 49 min / 15.6 g, topper 33 min / 14.7 g (supports were off in our run;
the topper's own profile enables them).

## Option (a) applied: numbers measured on the tested designs, our art and themes (agreed)
Pencil (measured on the tested MakerWorld topper): tunnel hole 8.0 mm (was 7.7), plate height 13.0 mm (was 10.4), floor wall 2.0 mm
(axis at z 6.0), roof wall 2.6 mm with our teardrop roof (their round hole has 3.0 mm and needs supports; ours needs none).
Tag and bottle hanging loop: wall around the hole 3.0 mm (was 2.0), measured on the tested Mariachi bag tag (~3 mm).
NOT copied: Mariachi's hole is ~3.5 mm (a key ring), ours stays 5.0 mm for a strap; Mariachi's loop thickness (~4 mm) is not applied, our loop is 2.2-3.2 mm
(needs a separate tab height in the generator). Ruler: as agreed above (flat, 2.0 mm).
Slice (H2D 0.4, 0.20, Generic PLA), cars theme: pencil 3 colours 43 min / 16.1 g (was 40 min / 14.1 g), 4 colours 1h06m / 22.8 g (was 1h02m / 20.5 g); tag unchanged.

## Working rule for artwork (agreed)
GPT draws and fixes the art, the generator only traces it. When the art has a problem (lines thinner than 0.8 mm at print size, details that vanish,
too many colours, broken white lines such as the headphones), do NOT patch it with tricks in the converter: tell the owner straight away what to
ask GPT to change and give a ready prompt (flat colours with exact hex values, no line thinner than ~1.7% of the tag width, thick continuous lines,
no tiny specks, high resolution), then trace the new image. Converter-side fixes only when the owner asks for them.
Open item: Sally 3 colours (yellow #F6BA1C, pink #EC407A, white): waiting for the GPT redraw with thicker lines and continuous white headphone lines.

## Sally 4 colours: approved version (owner)
Approved: the upscaled GPT sheet (round 4, 1911 x 2000), theme `gamer_girl7`, files in packs/gamer-SALLY-APPROVED.zip.
Slice (H2D 0.4, 0.20, Generic PLA): tag 1h04m 19.4 g, pencil 1h00m 20.1 g, ruler 43m 20.4 g, bottle 46m 13.0 g, total 3h35m 72.8 g.
Known: a few tiny yellow specks (< 1 mm) remain near the mouth, bow and hoodie; judge them on the first print.

## Hanging loop (Sally tag), proposal implemented in the generator, files NOT regenerated yet
Measured: tested Mariachi tag loop is ~4 mm thick (estimate from its file and print scale), ours was 2.2 mm; ring wall 3.0 mm and hole 5.0 mm kept.
New theme options: tab_height (raise the loop, outline colour only) and tab_fillet (round the joins to the outline). Enabled for gamer_girl7: loop 3.2 mm, fillet 1.5 mm.
Slice (H2D 0.4, 0.20, Generic PLA), Sally tag: 1h04m / 19.4 g -> 1h12m / 21.8 g (extra yellow layers = extra colour changes).
Tip from the research (sellers' guides, not official): 3+ wall loops in the slicer for the loop, PETG is less brittle than PLA.
Waiting for the owner's go before regenerating packs/gamer-SALLY-APPROVED.zip.

## Yellow specks inside the art (Sally): cause and fix, files NOT regenerated yet
Cause: gaps between art colours narrower than 0.8 mm cannot be printed, so the base slab shows through. Sally's base is yellow but the art lines are purple,
so gaps look yellow; Osayd's base is black like its lines, so the same gaps (3x more area) are invisible.
Fix (theme option gap_fill): an under-layer of the line colour (purple) inside the art area (closing 1.5 mm, kept 1.5 mm away from the outer rim), tag and bottle only.
Enabled for gamer_girl7. Thin purple slivers may print as thin lines or be skipped by the slicer.
Pending: owner's approval, then regenerate packs/gamer-SALLY-APPROVED.zip together with the thicker loop (tab_height 3.2).
