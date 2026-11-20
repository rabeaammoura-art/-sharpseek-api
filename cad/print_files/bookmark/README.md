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

`bookmark_4_options.3mf`: the 4 colour options from stock on one plate, **each bookmark its own object** (delete the ones you
do not want), 7 filament slots, layer 0.16: 1 PLA+ White, 2 Silk Red/Gold, 3 PLA+ Black, 4 Silk Gold, 5 Silk Blue/Green,
6 Wood PLA, 7 PLA+ Red. Options: 1 = slots 1+2, 2 = 3+4, 3 = 1+5, 4 = 6+7. All profiles are PLA Basic: pick the real spools
in Studio. Time 0.16: one alone 54 min; all four together 4h07m / 60 g. Regenerate: `python cad/bookmark/bookmark.py --options --out cad/print_files/bookmark`.

`bookmark_iqra.3mf`: one bookmark with the stitched text «اقرأ وارتقِ» (hand-drawn one-stitch letters, `cad/bookmark/stitch_text.py`),
read top -> bottom, layer 0.16, colours of option 1 (white + red), 2 slots, swap freely. 57 min / 14 g.
Regenerate: `python cad/bookmark/bookmark.py --text --layer 0.16 --fabric "#F2F0EA" --thread "#B0182B" --out cad/print_files/bookmark`.
