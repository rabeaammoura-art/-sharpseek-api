#!/bin/bash
cd /home/user/-sharpseek-api/concept
declare -A CUT=(
 [62]="0,20;50,40.43"
 [66]="0,30;0,41;90,33"
 [70]="-40,14.23;70,25.98"
 [74]="0,18;0,44;90,28"
 [78]="0,18;0,48;90,28"
 [82]="0,22;0,52;90,30"
 [86]="0,26;0,56;90,14"
 [90]="0,28;0,58;90,26"
 [94]="0,18;0,38;0,62;90,27"
)
for L in 62 66 70 74 78 82 86 90 94; do
  echo "=== S$L"; ../.venv-cad/bin/python make_pieces2.py $L S$L "${CUT[$L]}" 2>&1 | tail -14
  (cd .. && .venv-cad/bin/python cad/bambu_slice.py --filament "Bambu PLA Basic @BBL H2D" --price-kg 6.951 $(sed 's#^#concept/#' concept/e30_ref/S${L}_files.txt) 2>&1 | grep -E "^S${L}_|TOTAL|warning")
done
echo ALLDONE
