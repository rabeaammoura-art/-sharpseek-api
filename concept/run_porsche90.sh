#!/bin/bash
cd /home/user/-sharpseek-api/concept
export STL=/home/user/-sharpseek-api/concept/porsche_ref/p_L2926_t2625.stl MASKPFX=P_
for B in 3.0 1.5; do
  echo "=== band $B"; BAND=$B ../.venv-cad/bin/python make_pieces2.py 90 PO90 "0,28;0,58;90,30" 2>&1 | tail -n 12 | tee /tmp/po90.out
  grep -q "fits False" /tmp/po90.out || break
done
(cd .. && .venv-cad/bin/python cad/bambu_slice.py --filament "Bambu PLA Basic @BBL H2D" --price-kg 6.951 $(sed 's#^#concept/#' concept/e30_ref/PO90_files.txt) 2>&1 | grep -E "^PO90_|TOTAL|warning|FAILED")
echo DONE
