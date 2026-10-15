#!/usr/bin/env bash
# Export every src/*.svg to out/: PNG @1x/@2x, plus app icons + favicon.ico for src/mark.svg,
# and out/preview.png — every logo on light and dark backgrounds at a glance.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out/icons
for svg in src/*.svg; do
  name=$(basename "$svg" .svg)
  rsvg-convert "$svg" -o "out/$name.png"
  rsvg-convert -z 2 "$svg" -o "out/$name@2x.png"
  cp "$svg" "out/$name.svg"
done
if [ -f src/mark.svg ]; then
  for s in 16 32 48 64 128 180 192 256 512 1024; do
    rsvg-convert -w $s -h $s src/mark.svg -o out/icons/mark-$s.png
  done
  convert out/icons/mark-{16,32,48,64,256}.png out/favicon.ico
fi
# Preview sheet: each logo on light + dark, plus the mark at small sizes (legibility check).
tiles=()
for svg in src/*.svg; do
  name=$(basename "$svg" .svg)
  for bg in "#ffffff" "#0b1220"; do
    t="out/.tile-$name-${bg#\#}.png"
    rsvg-convert -h 220 -b "$bg" "$svg" -o "$t.tmp.png"
    convert "$t.tmp.png" -background "$bg" -gravity center -extent 760x300 "$t"; rm "$t.tmp.png"
    tiles+=("$t")
  done
done
if [ -f src/mark.svg ]; then
  for bg in "#ffffff" "#0b1220"; do
    t="out/.tile-sizes-${bg#\#}.png"
    convert -background "$bg" out/icons/mark-{16,32,48,64,128}.png -gravity center +append \
      -bordercolor "$bg" -border 20 -gravity center -extent 760x300 "$t"
    tiles+=("$t")
  done
fi
montage "${tiles[@]}" -tile 2x -geometry +6+6 -background "#d0d4dc" out/preview.png
rm -f out/.tile-*.png
echo "Built: $(ls out | tr '\n' ' ')"
