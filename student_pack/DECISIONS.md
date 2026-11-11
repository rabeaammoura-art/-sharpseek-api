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
