#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [[ ! -f pyproject.toml ]]; then
    echo "Error: run this script from GAMMA Locker project root (pyproject.toml missing)." >&2
  exit 1
fi

VERSION="$(python3 - <<'PY'
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
print(data['project']['version'])
PY
)"

OUT_DIR="dist"
PKG_NAME="gamma-locker-${VERSION}-code-only"
ZIP_PATH="${OUT_DIR}/${PKG_NAME}.zip"

mkdir -p "$OUT_DIR"
rm -f "$ZIP_PATH"

python3 - <<'PY'
from pathlib import Path
import tomllib
import zipfile

root = Path('.')
out_dir = root / 'dist'
out_dir.mkdir(exist_ok=True)

with open(root / 'pyproject.toml', 'rb') as f:
    version = tomllib.load(f)['project']['version']

pkg_name = f'gamma-locker-{version}-code-only'
zip_path = out_dir / f'{pkg_name}.zip'

files = [
    '.gitignore',
    'README.md',
    'pyproject.toml',
    'app.py',
    'save_reader.py',
    'scraper.py',
    'release.sh',
    'release.ps1',
    'start_gamma_locker.sh',
    'start_gamma_locker.ps1',
    'start_gamma_locker.bat',
    'loadout_lab_data/.gitkeep',
]

with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for rel in files:
        p = root / rel
        if not p.exists():
            continue
        zf.write(p, arcname=f'{pkg_name}/{rel}')

print(zip_path)
PY

echo "Release package created: ${ZIP_PATH}"
