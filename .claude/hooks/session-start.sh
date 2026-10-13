#!/bin/bash
# Install the CAD toolchain (build123d venv + PrusaSlicer) at the start of every cloud session.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

"$CLAUDE_PROJECT_DIR/cad/setup.sh"
