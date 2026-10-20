#!/usr/bin/env bash
# Install the CAD toolchain: build123d (CAD -> STEP/STL), PrusaSlicer (STL -> G-code)
# and Bambu Studio (Flathub, official Bambu Lab profiles).
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v prusa-slicer >/dev/null; then
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq prusa-slicer
fi
[ -d .venv-cad ] || python3 -m venv .venv-cad
.venv-cad/bin/pip install -q -r cad/requirements.txt
if ! command -v flatpak >/dev/null || ! command -v bwrap >/dev/null; then
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq flatpak bubblewrap
fi
if ! flatpak info --user com.bambulab.BambuStudio >/dev/null 2>&1; then
  flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
  flatpak install --user -y --noninteractive flathub com.bambulab.BambuStudio
fi
echo "CAD environment ready."
