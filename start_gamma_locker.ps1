$ErrorActionPreference = 'Stop'

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoDir

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' not found. Install Python 3.10+ first."
}

$PyExe = Join-Path $RepoDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
  Write-Host "Creating virtual environment (.venv)..."
  py -3 -m venv .venv
}

Write-Host "Installing/updating dependencies..."
& $PyExe -m pip install --upgrade pip
& $PyExe -m pip install -e .

Write-Host "Starting GAMMA Locker..."
& $PyExe -m streamlit run app.py
