# GAMMA Locker (Standalone)

## Code-Only Distribution (Community Model)

This project is distributed as **code only**.

- We publish Python source code and project configuration.
- Each user generates their own local data/icons by scraping their own GAMMA/MO2 installation.
- Mod assets (DDS textures, extracted icons, etc.) are **not** shipped in releases.

---

## Included Files

- `app.py` – Streamlit web UI (locker, search, strategy planner)
- `save_reader.py` – Savegame parser (`.scop` / `.scoc`)
- `scraper.py` – local data/icon extractor from game/mod files
- `pyproject.toml` – dependencies and project metadata
- `start_gamma_locker.sh` / `.ps1` / `.bat` – bootstrap launchers (auto-setup + start)
- `loadout_lab_data/.gitkeep` – placeholder for local runtime data

---

## Features

### Locker Management
- Add/remove weapons
- Bulk removal via checkboxes
- Save/load local locker state
- Backup restore

### Savegame Import
- Read savegames from `SAVE_DIR`
- Add-all or replace-all from save
- Selective import

### Weapon Search
- Multi-keyword search by ID/name
- Preview icons and stats
- Direct add/remove from results
- Melee/knife/axe entries filtered out

### Strategy Planner
- Builds strict triad sets:
  - `1 Sidearm`
  - `1 Power`
  - `1 Workhorse`
- Modes: `Balanced` and `Maxxed`
- Phase pipeline (`P1`, `P2H0`, `P1R1`, `P2H1`, `P3`)
- Badge-based hybrid/redundancy classification
- Sorting, set search, random roll

### Icon Handling
- RGBA compositing on black background
- Per-icon R/B swap detection for mixed DDS exports
- Fallback handling for invalid/transparent icons

---

## Requirements

- Python `3.10+`
- Recommended environment: Linux / WSL
- Python packages:
  - `streamlit`
  - `pandas`
  - `numpy`
  - `pillow`
  - `altair`
  - `tqdm`
- Optional for `scraper.py`:
  - ImageMagick (`convert`)

Dependencies are installed automatically by the bootstrap launchers.

---

## First-Time Setup (Required)

Before running the app for real usage, generate local data from your own installation:

```bash
python3 scraper.py
```

This creates local runtime artifacts such as:
- `loadout_lab_data/weapons_stats.csv`
- `loadout_lab_data/icons/*.png`

If these are missing, the app cannot provide meaningful output.

---

## Run GAMMA Locker (Bootstrap Launcher)

From this folder:

### Linux / WSL
```bash
bash start_gamma_locker.sh
```

### Windows (PowerShell)
```powershell
pwsh -File .\\start_gamma_locker.ps1
```

### Windows (double-click)
- Run `start_gamma_locker.bat`

The launcher will:
- create `.venv` if missing
- update `pip`
- install project dependencies
- start Streamlit (`app.py`)

Then open `http://localhost:8501`.

---

## Important Paths to Configure

In `app.py`:

```python
SAVE_DIR = "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/appdata/savedgames/"
```

Update this path for your local installation.

In `scraper.py`, adjust if needed:
- `SCAN_PATHS`
- `TEXT_PATHS`
- `TEXTURE_PATHS`

---

## Typical User Flow

1. Run `python3 scraper.py`
2. Start app: `bash start_gamma_locker.sh` (or a Windows launcher)
3. Use **Weapon Search** to build locker
4. Optionally import from savegame
5. Open **Strategy Planner**
6. Choose `Balanced` or `Maxxed`
7. Sort/filter sets and roll random loadouts

---

## Troubleshooting

### App does not start
- Check Python version: `python3 --version` (Linux/WSL) or `py -3 --version` (Windows)
- Re-run the bootstrap launcher

### No savegames detected
- Verify `SAVE_DIR`
- Confirm `.scop`/`.scoc` files exist

### Missing or incorrect icons
- Re-run `python3 scraper.py`
- Modded texture packs can change icon sources; some edge cases may still require manual tweaks

### Slow first load
- Normal with large icon/data sets

---

## Community Release Workflow

- Keep repository code-only
- Do not publish generated `loadout_lab_data` artifacts
- Tag releases with source + docs only

---

## Useful Commands

```bash
# Generate local data
python3 scraper.py

# Run app (Linux/WSL bootstrap)
bash start_gamma_locker.sh

# Run app (PowerShell bootstrap)
pwsh -File .\\start_gamma_locker.ps1

# Build release ZIP (Linux/WSL)
bash release.sh

# Build release ZIP (PowerShell)
pwsh -File release.ps1
```
