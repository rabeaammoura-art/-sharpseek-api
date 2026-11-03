# Workshop key holder shaped like a combination wrench

Reconstruction of the reference picture as a parametric build123d model (`cad/wrench_keyholder.py`).
The "native editable CAD project" is that script: change `PARAMS` and re-run
`python cad/wrench_keyholder.py --out cad/wrench_keyholder` (needs `cad/setup.sh` first).

## What is here
- `step/` and `stl/`: one file per printable component and colour (`<part>__<colour>`), plus
  `assembly_disc_brake.step` / `assembly_drum_brake.step` (complete assemblies, the two brake variants are never combined).
- `views/`: lit renders (`*_render_front|iso|close.png`, three.js with shadows, `cad/wrench_render3d.py`) and plain technical views front/side/top/iso (`*_front.png` ...), both variants.
- Parts: `A_left_jaw`, `B_bar_left`, `C_bar_right`, `D_ring_head` (body split in 4 so each fits the H2D bed, longest 201 mm),
  `hook_1..5`, `splice_1..3` (back plates across the joints), `brake_disc`, `brake_drum`.
- Colours (filament slots): black, orange, white, red.

## Assumptions and uncertainty (the picture has no dimensions)
- Overall size is NOT measured: `SCALE = 0.32 mm/px` gives about 610 x 155 mm. One number changes it.
- Every outline is traced by eye from the picture (jaw slot angle, neck curves, tool shapes, car). It is a faithful
  layout, not an exact copy; the brick texture and the soft shading of the picture are not modelled.
- Hooks: slim J hooks with a ball tip (7 mm wide, 10 mm thick), screwed from the back.
- Brake: the picture shows a disc brake; the drum variant is an addition with the same footprint.
- Nothing is print-tested (the printer has not arrived).

## Assembly
1. Print the 4 body parts, 5 hooks, 3 splice plates, one brake variant. Joints are dovetails (0.25 mm clearance): slide each tongue into its groove from the back.
2. Each joint gets a splice plate in the recess on the back: 4 x M3x6 flat-head self-tapping screws (pilot 2.6 mm).
3. Hooks: 2 x M3 countersunk screws each, from the back through the plate into the hook (pilot 2.5 mm).
4. Brake: push the 6 mm peg into the socket (no glue).
5. Wall: two keyhole pockets in the back behind the two decorative screws, for M4 screws (head 2.2 mm off the wall).

## Validation done (CAD kernel, not a print)
- All components are valid solids; exact boolean interference check of every pair, both variants: 0 clashes (> 1 mm3).
- Exported STLs: 2 of them (`B_bar_left__black`, `C_bar_right__white`) have a few edges shared by two touching solids
  (not manifold edges); slicers repair this, but check in Studio.
- NOT done: minimum wall thickness analysis, hook load test, support analysis, slicer run, photoreal render.
  Hook J tips are thin-ish (about 3 mm inner radius) and the workshop reliefs are 2.2 mm: check after the first print.
