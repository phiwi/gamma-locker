import os, re

def get_savegames(save_dir):
    if not os.path.exists(save_dir): return []
    files = [f for f in os.listdir(save_dir) if f.endswith('.scop')]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)), reverse=True)
    return files

def extract_weapons_from_scop(file_path, all_known_weapons):
    if not os.path.exists(file_path):
        return []
    try:
        known = sorted(set(all_known_weapons), key=len, reverse=True)
        junk_ids = {'wpn_binoc', 'wpn_knife', 'wpn_grenade', 'wpn_bolt'}

        scoc_path = file_path[:-5] + ".scoc" if file_path.lower().endswith(".scop") else file_path
        source_path = scoc_path if os.path.exists(scoc_path) else file_path

        import mmap
        with open(source_path, 'rb') as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                content = mm[:]

        text = content.decode("latin-1", errors="ignore").lower()
        tokens = re.findall(r"(wpn_[a-z0-9_]+)", text)
        
        found = set()
        for token in tokens:
            if any(j in token for j in junk_ids) or "_hud" in token: continue
            
            base_token = re.sub(r"[0-9]+$", "", token)
            if not base_token: continue
            
            best_match = None
            for w_id in known:
                if token.startswith(w_id):
                    suffix = token[len(w_id):]
                    if not suffix or suffix.isdigit():
                        if best_match is None or len(w_id) > len(best_match):
                            best_match = w_id
            
            if best_match:
                found.add(best_match)

        return sorted(list(found))
    except Exception as e:
        print(f"Error reading save: {e}")
        return []

def extract_refined_weapons(file_path, all_known_weapons):
    # Fallback that just puts everything in "Inventory" so nothing breaks
    res = extract_weapons_from_scop(file_path, all_known_weapons)
    return {"Inventory": res, "Stashes": res, "Racks": res}
