#!/bin/bash
cd /home/user/-sharpseek-api/concept
export NOMERGE=1 THICK=2.5 BAND=1.5 STL=/home/user/-sharpseek-api/concept/porsche_ref/p_L2926_t2625.stl MASKPFX=P_
../.venv-cad/bin/python make_pieces2.py 90 PT90 "0,28;0,58;90,30" 2>&1 | tail -n 12 | tee /tmp/pt90.out
(cd .. && .venv-cad/bin/python cad/bambu_slice.py --filament "Bambu PLA Basic @BBL H2D" --price-kg 6.951 $(sed 's#^#concept/#' concept/e30_ref/PT90_files.txt) 2>&1 | grep -E "^PT90_|TOTAL|warning|FAILED")
echo DONE
