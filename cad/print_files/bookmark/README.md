# Tatreez bookmark (cross-stitch look) — 50 x 170 mm

`bookmark.3mf`: one object, **two parts = two filament slots, swap colours freely in Bambu Studio**:
- slot 1 `fabric`: plate 1.2 mm with the aida weave texture + 4.4 mm tassel hole
- slot 2 `stitches`: raised X stitches (two rounded threads, the second rides over the first), 0.6 mm high

Default colours cream + red. Any pair works (e.g. black + gold, white + blue); a **silk PLA** for the stitches looks most like thread.
Printed flat, face up as loaded, no supports. Prime tower right of the part. Tassel bought ready (not printed).

Time (Bambu Studio CLI, H2D, PLA, prime tower 20 mm): 0.20 mm 41 min / 14 g; 0.16 mm 54 min; **0.12 mm 1h14m / 15 g (rounder threads)**; 0.08 mm 1h34m.
Not print-tested (printer not arrived).

Regenerate / other default colours: `python cad/bookmark/bookmark.py --fabric "#FFFFFF" --thread "#1E3A8A" --out cad/print_files/bookmark`
(the slicer needs all 4 `--filament` slots for this 3MF).
