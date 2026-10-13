#!/usr/bin/env bash
# Install the CAD toolchain: build123d (CAD -> STEP/STL) and PrusaSlicer (STL -> G-code).
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v prusa-slicer >/dev/null; then
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq prusa-slicer
fi
[ -d .venv-cad ] || python3 -m venv .venv-cad
.venv-cad/bin/pip install -q -r cad/requirements.txt
echo "CAD environment ready."
