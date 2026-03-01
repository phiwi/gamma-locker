#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

if [[ ! -f pyproject.toml ]]; then
    echo "Error: run this script from GAMMA Locker project root (pyproject.toml missing)." >&2
  exit 1
fi

VERSION_FROM_TAG="${GITHUB_REF_NAME:-}"
VERSION_FROM_TAG="${VERSION_FROM_TAG#v}"

VERSION_FROM_PROJECT="$(python3 - <<'PY'
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
print(data['project']['version'])
PY
)"

VERSION="${VERSION_FROM_TAG:-$VERSION_FROM_PROJECT}"

OUT_DIR="dist"
PKG_NAME="gamma-locker-${VERSION}-code-only"
ZIP_PATH="${OUT_DIR}/${PKG_NAME}.zip"

mkdir -p "$OUT_DIR"
rm -f "$ZIP_PATH"

PACKAGE_VERSION="$VERSION" python3 - <<'PY'
from pathlib import Path
import os
import tomllib
import zipfile

root = Path('.')
out_dir = root / 'dist'
out_dir.mkdir(exist_ok=True)

version = os.environ.get('PACKAGE_VERSION')
if not version:
    with open(root / 'pyproject.toml', 'rb') as f:
        version = tomllib.load(f)['project']['version']

pkg_name = f'gamma-locker-{version}-code-only'
zip_path = out_dir / f'{pkg_name}.zip'

files = [
    '.gitignore',
    'README.md',
    'pyproject.toml',
    'paths_config.py',
    'paths_config.json',
    'app.py',
    'save_reader.py',
    'scraper.py',
    'release.sh',
    'release.ps1',
    'start_gamma_locker.sh',
    'start_gamma_locker.ps1',
    'start_gamma_locker.bat',
    'docs/branding/gamma-locker-logo.png',
    'docs/branding/gamma-locker-logo.svg',
    'docs/screenshots/my_locker.png',
    'docs/screenshots/search.png',
    'docs/screenshots/set_score_distribution.png',
    'docs/screenshots/weapons_per_role_most_common_calibers.png',
    'docs/screenshots/roll_random_rollout.png',
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
