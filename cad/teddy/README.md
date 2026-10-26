# Teddy + heart lithophane lamp (v3)

Built from the original STLs (`teddy_rear_heart_LED.stl`, `heart_front_lithophane.stl`). The original heart, pocket
and mounting (stepped tongue that locks the lithophane into the teddy, border ring flush with the body) are unchanged.

- `relief_swap.py`: keeps the old lithophane and replaces only the relief inside the border with the new photo (`out/lithophane_photo.jpg`), same 0.8-3.2 mm thickness range as before
- `teddy_edit.py`: back hole sealed, 8 mm cable channel in the base, deeper smile, paw pads (main pad + 4 toes) on both feet
- `run_v3.py <upload dir> <photo> <out dir>` builds both STLs. (`run_teddy.py`, `run_litho.py`, `litho.py`, `heart.py` are the abandoned v2 attempt with a new frame; not used)
