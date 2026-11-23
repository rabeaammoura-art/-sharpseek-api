# Threaded feet variant (instead of the kickstand), 200 mm box

- `nightcap_box_and_2_feet_200.3mf` = plate 2: the box with two threaded bosses (bottom corners) + two feet standing on their tips (one colour, no tower). The plaque files are the same as in `../nightcap_200/` (plaque unchanged).
- `thread_foot.stl` (print 2, tip down, stud up), `glow_box_feet_200.stl`, `thread_test_block.stl` = a 24 x 24 x 10 block with the same threaded hole: print it with ONE foot first (about 30 min) to check that the thread turns by hand.
- Thread: M11 x 3 coarse, 45 degree flanks, depth 1.2, hole clearance 0.3 (`cad/thread_feet.py`: `CLR`, `PITCH`, `RM`). If it is too tight / loose change `CLR` (0.2 - 0.45) and regenerate with `"stand": "thread_feet"`.
- CLI slice (PETG 0.24): box + 2 feet 2h32m / 86 g (the kickstand set is 2h01m / 90 g: the feet are 74 mm tall so they add layers). Not print-tested.
