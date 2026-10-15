#!/usr/bin/env bash
# Install the logo toolchain: rsvg-convert (SVG -> PNG, Pango text shaping incl. Arabic),
# ImageMagick (favicon.ico, preview sheets) and fonts (Inter, Noto Sans Arabic).
set -euo pipefail
pkgs=()
command -v rsvg-convert >/dev/null || pkgs+=(librsvg2-bin)
command -v convert      >/dev/null || pkgs+=(imagemagick)
fc-list | grep -qi "Noto Sans Arabic" || pkgs+=(fonts-noto-core)
fc-list | grep -qi "Inter"            || pkgs+=(fonts-inter)
if [ ${#pkgs[@]} -gt 0 ]; then
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${pkgs[@]}"
fi
echo "Logo environment ready."
