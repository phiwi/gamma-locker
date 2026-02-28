@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel% neq 0 (
  echo Error: Python launcher ^("py"^) not found. Install Python 3.10+ first.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment ^(.venv^)...
  py -3 -m venv .venv
  if %errorlevel% neq 0 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

echo Installing/updating dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if %errorlevel% neq 0 goto :fail

".venv\Scripts\python.exe" -m pip install -e .
if %errorlevel% neq 0 goto :fail

echo Starting GAMMA Locker...
".venv\Scripts\python.exe" -m streamlit run app.py
exit /b %errorlevel%

:fail
echo Startup failed.
pause
exit /b 1
