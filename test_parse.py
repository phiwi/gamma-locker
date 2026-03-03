import re, glob, os
save_dir = "/mnt/c/Eigene Dateien/Spiele/Gamma/savedgames"
# Find a savegame
save = glob.glob(save_dir + "/*.scop")
if not save:
    # Try looking in the appdata path mentioned in app.py
    import json
    try:
        with open('paths_config.json', 'r') as f:
            cfg = json.load(f)
            save_dir = cfg.get("save_dir", save_dir)
            save = glob.glob(save_dir + "/*.scop")
    except:
        pass

if not save:
    print("Could not find saves.")
else:
    # Use the first save or the one the user specifically mentioned
    tgt = next((s for s in save if 'zaba crystal' in s.lower()), save[0])
    print(f"Scanning {tgt}...")
    scoc = tgt[:-5] + ".scoc"
    for p in [tgt, scoc]:
        if os.path.exists(p):
            with open(p, 'rb') as f:
                data = f.read().decode('latin-1', errors='ignore')
                print(f"--- File: {p} ---")
                
                # Check for weapon rack presence
                for m in re.finditer(r'wpn_rack', data):
                    start = max(0, m.start()-50)
                    end = min(len(data), m.start()+200)
                    print("RACK CONTEXT:", data[start:end].replace('\n', ' '))
                
                # Check for some weapons
                count = 0
                for m in re.finditer(r'wpn_ak74|wpn_abakan', data):
                    start = max(0, m.start()-50)
                    end = min(len(data), m.start()+200)
                    print("WEAPON CONTEXT:", data[start:end].replace('\n', ' '))
                    count += 1
                    if count > 5: break
