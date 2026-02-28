#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not in PATH." >&2
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment (.venv)..."
  python3 -m venv .venv
fi

PY_BIN=".venv/bin/python"

echo "Installing/updating dependencies..."
"$PY_BIN" -m pip install --upgrade pip
"$PY_BIN" -m pip install -e .

echo "Starting GAMMA Locker..."
"$PY_BIN" -m streamlit run app.py
