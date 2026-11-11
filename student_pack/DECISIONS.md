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

Status: waiting for the owner's go before touching the generator (layout.py ruler()). After the change: re-run the tests,
re-slice the rulers and compare with the numbers below.

Current ruler numbers (H2D 0.4, 0.20, Generic PLA, 6.951 JOD/kg), cars theme: 2 colours 1h01m / 23.3 g / 0.20 JOD, 3 colours 1h11m / 25.7 g / 0.22 JOD.
