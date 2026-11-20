# Clear TPU coaster with PETG drawings inside

Ø95 x 3.0 mm. Printed flat: clear TPU base 1.6 mm, PETG drawing 0.6 mm, clear TPU cover 0.8 mm (the drawing is sealed
inside). H2D: TPU on nozzle 2 (external spool, soft TPU does not go in the AMS), the PETG colours on nozzle 1 (AMS). One print, no pause.

    python cad/coaster/coaster.py PICTURE.png            -> cad/print_files/coaster/coaster_birds.3mf (1 coaster)
    python cad/coaster/coaster.py PICTURE.png --set4 --out cad/print_files/coaster/coaster_birds_set4.3mf

The picture (owner's ChatGPT image) stays out of git. Left half = colour version inside a thin grey circle; only flat
red / blue / orange shapes are traced. Features and gaps under 0.7 mm are dropped.

Slice check (CLI, 0.20, 100% zig-zag infill, prime tower): 1 coaster 58 min / 29 g (TPU 26 g);
4 on one plate 2h58m / 107 g (TPU 98 g) = 45 min each. Not print-tested (printer not here yet).

    python cad/bambu_slice.py cad/print_files/coaster/coaster_birds_set4.3mf --filament "Bambu TPU 95A HF @BBL H2D 0.4 nozzle" \
      --filament "Bambu PETG Basic @BBL H2D 0.4 nozzle" (x3) --nozzle-map 2,1,1,1 --tower-x 270 --tower-y 140 --tower-width 30 \
      --set sparse_infill_density=100% --set sparse_infill_pattern=zig-zag

## ChatGPT prompt for new drawings (must be flat 2D)
Flat 2D design for a round coaster, NOT a 3D render (no perspective, shadows, gradients, mockup). 2048x2048 white canvas,
one thin light-grey circle (90% of the canvas) = the edge. Inside: 8-12 small shapes (birds, butterflies, hearts, stars,
flowers), each a SOLID silhouette in ONE flat colour: red #C8102E, blue #1F5FA8, orange #E07A1F only. Details are cut-out
holes (at least 2% of the canvas), nothing thinner than 1%, shapes do not touch (2% gap), 6% away from the circle, no text.
Also give the same image in pure black on white.

## Heart version (test size)
    python cad/coaster/coaster.py PICTURE.png --heart 65 --out cad/print_files/coaster/coaster_heart65.3mf
Heart 65 x 56 mm (+ hanging loop in the top notch, hole 3.6 x 5 mm, owner's mark), the same 12 shapes re-placed one by one
inside (43% of their round size); after shrinking, gaps under 0.8 mm are closed and thin parts thickened (the butterfly
antennae merge at this size). Slice: 38 min / 12.6 g (TPU 10 g), print_test 0 problems.
