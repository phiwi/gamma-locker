# GAMMA Loadout App (Standalone)

Diese Version ist als **eigene, saubere App-Mappe** gedacht und enthält alles, was die Anwendung lokal benötigt:

- `app.py` – Streamlit UI (Lager, Suche, Set-Planer)
- `save_reader.py` – Savegame-Reader (`.scop/.scoc`)
- `scraper.py` – Daten-/Icon-Generator aus GAMMA-Dateien
- `loadout_lab_data/` – lokale Datenbasis (Stats, Icons, JSON)

---

## 1) Was die App kann

## Lagerverwaltung
- Waffen im Locker anzeigen, hinzufügen, entfernen
- Bulk-Entfernung über Checkboxen
- Locker speichern/laden
- Backup-Restore

## Savegame-Import
- Savegames aus `SAVE_DIR` lesen
- Alle gefundenen Waffen hinzufügen oder ersetzen
- Selektiver Import einzelner Waffen

## Waffen-Suche
- Suche per Name/ID (mehrere Keywords möglich)
- Ergebnisliste mit Stats und Icon
- Direkter Add/Remove aus den Treffern
- Melee/Knife/Axe/Tomahawk werden herausgefiltert

## Set-Planer
- Erzeugt Triad-Loadouts mit exakt:
  - `1 Sidearm`
  - `1 Power`
  - `1 Workhorse`
- Zwei Modi:
  - `Balanced` (nahe Ziel-Mittelwert)
  - `Maxxed` (maximaler Gesamtscore)
- Phasenmodell (`P1`, `P2H0`, `P1R1`, `P2H1`, `P3`)
- Badges/Farben für Triad/Hybrid/Redundanz
- Sortierung nach Score oder Bildungsreihenfolge
- Suche innerhalb der Sets (z. B. `spas12`)
- Zufälliges Loadout würfeln

## Icon-Handling
- RGBA-Komposition auf schwarzem Hintergrund
- Auto-Erkennung möglicher R/B-Kanalvertauschung
- Fallback-Logik bei ungültigen/transparenten Icons

---

## 2) Voraussetzungen

- Linux/WSL empfohlen
- Python `3.10+`
- Pakete:
  - `streamlit`
  - `pandas`
  - `numpy`
  - `pillow`
  - `altair`
  - `tqdm` (für `scraper.py`)
- Optional für `scraper.py`:
  - ImageMagick (`convert`)

Installation der Python-Pakete:

```bash
python3 -m pip install streamlit pandas numpy pillow altair tqdm
```

---

## 3) Start der App

Aus diesem Ordner starten:

```bash
cd gamma_loadout_app
streamlit run app.py
```

Dann Browser öffnen (normalerweise `http://localhost:8501`).

---

## 4) Wichtige Konfiguration

In `app.py` ist der Savegame-Pfad fest hinterlegt:

```python
SAVE_DIR = "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/appdata/savedgames/"
```

Passe den Pfad an, wenn deine Installation woanders liegt.

In `scraper.py` sind Scan-/Texturpfade ebenfalls fest konfiguriert (`SCAN_PATHS`, `TEXT_PATHS`, `TEXTURE_PATHS`).

---

## 5) Daten neu erzeugen (optional)

Wenn du Stats/Icons aus deiner Installation neu bauen willst:

```bash
python3 scraper.py
```

Das schreibt/aktualisiert u. a.:
- `loadout_lab_data/weapons_stats.csv`
- `loadout_lab_data/icons/*.png`

Hinweis: Je nach Mod-Setup kann das einige Zeit dauern.

---

## 6) Bedienablauf (empfohlen)

1. App starten
2. Tab **Waffen-Suche** nutzen und Waffen ins Locker legen
3. Optional **Savegame-Import** in der Sidebar nutzen
4. Tab **Strategie-Planer** öffnen
5. Modus (`Balanced`/`Maxxed`) wählen
6. Sets sortieren/suchen (`spas12`, `sr25`, …)
7. Optional Zufalls-Set würfeln

---

## 7) Rollenlogik (Kurzfassung)

- **Sidearm**:
  - Pistolen in Slot 1
  - plus erlaubte kompakte MPs (z. B. P90, Veresk, MP5K-Familie)
- **Power**:
  - Sniper/DMR/Battle/LMG bzw. starke Kaliber
- **Workhorse**:
  - restliche Primärwaffen inkl. möglicher Close-Hybrid-Kandidaten

Die Set-Erzeugung erzwingt immer eine vollständige Triad-Kombination.

---

## 8) Troubleshooting

## App startet nicht
- Prüfe Python-Version: `python3 --version`
- Prüfe Paketinstallation (siehe Voraussetzungen)

## Keine Savegames sichtbar
- `SAVE_DIR` in `app.py` prüfen
- Existieren `.scop/.scoc` Dateien im Zielordner?

## Falsche/fehlende Icons
- Bei stark modifizierten Texturpaketen `scraper.py` neu laufen lassen
- Einzelne kaputte PNGs können transparent sein; die App hat Fallbacks, aber nicht jede Mod-Kombi ist perfekt matchbar

## Sehr langsame erste Anzeige
- Viele Icons + große CSVs sind normal; nach dem ersten Laden meist schneller

---

## 9) Git-Layout in diesem Standalone-Ordner

Dieses Verzeichnis hat ein eigenes Git-Repository (unabhängig vom alten Root-Ordner).
So bleibt die App sauber getrennt von Savegame-/Test-/Restdateien im Hauptverzeichnis.

---

## 10) Nützliche Kommandos

```bash
# App starten
streamlit run app.py

# Scraper laufen lassen
python3 scraper.py

# Git-Status
git status

# Letzte Commits
git log --oneline -n 5
```
