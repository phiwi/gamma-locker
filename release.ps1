$ErrorActionPreference = 'Stop'

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoDir

if (-not (Test-Path "pyproject.toml")) {
  throw "Run this script from gamma_loadout_app root (pyproject.toml missing)."
}

$version = python -c "import tomllib;print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
$version = $version.Trim()

$OutDir = Join-Path $RepoDir "dist"
$PkgName = "gamma-loadout-app-$version-code-only"
$StageDir = Join-Path $OutDir $PkgName
$ZipPath = Join-Path $OutDir "$PkgName.zip"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (Test-Path $StageDir) { Remove-Item -Recurse -Force $StageDir }
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

$files = @(
  ".gitignore",
  "README.md",
  "pyproject.toml",
  "app.py",
  "save_reader.py",
  "scraper.py",
  "release.sh",
  "release.ps1",
  "loadout_lab_data/.gitkeep"
)

foreach ($rel in $files) {
  if (Test-Path $rel) {
    $target = Join-Path $StageDir $rel
    $targetDir = Split-Path -Parent $target
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    Copy-Item -Path $rel -Destination $target -Force
  }
}

Compress-Archive -Path "$StageDir/*" -DestinationPath $ZipPath
Remove-Item -Recurse -Force $StageDir

Write-Host "Release package created: $ZipPath"
