#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

python3 --version || python --version
python3 scripts/build.py --onefile "$@" || python scripts/build.py --onefile "$@"

echo "Build completed. Check the 'dist' folder."