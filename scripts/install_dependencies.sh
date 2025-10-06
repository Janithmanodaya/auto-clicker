#!/usr/bin/env bash
set -euo pipefail

# Creates a local virtual environment (.venv) and installs dependencies from requirements.txt

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

if [[ ! -f "requirements.txt" ]]; then
  echo "requirements.txt not found in project root: $PROJECT_ROOT"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python not found. Please install Python 3.10+."
    exit 1
  fi
fi

if [[ ! -d ".venv" ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo "Dependencies installed into virtual environment: $PROJECT_ROOT/.venv"
echo
echo "To activate the environment in your current shell, run:"
echo "  source .venv/bin/activate"