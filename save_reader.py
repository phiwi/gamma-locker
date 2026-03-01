import os, re

def get_savegames(save_dir):
    if not os.path.exists(save_dir): return []
    files = [f for f in os.listdir(save_dir) if f.endswith('.scop')]
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)), reverse=True)
    return files

def extract_weapons_from_scop(file_path, all_known_weapons):
    """
    Attempts to extract weapon IDs from a binary .scop file.
    Optimized to keep real inventory items and ignore model paths/world stats noise.
    """
    if not os.path.exists(file_path):
        return []
    try:
        known = sorted(set(all_known_weapons), key=len, reverse=True)
        # Junk IDs that often appear in world data.
        junk_ids = {'wpn_binoc', 'wpn_knife', 'wpn_grenade', 'wpn_bolt'}

        # Primary source: .scoc often contains compact actor-adjacent metadata.
        scoc_path = file_path[:-5] + ".scoc" if file_path.lower().endswith(".scop") else file_path
        source_path = scoc_path if os.path.exists(scoc_path) else file_path

        import mmap
        with open(source_path, 'rb') as f:
            # Use mmap for efficient scanning in large files.
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                content = mm[:]

        # Extract ASCII-like tokens from binary data.
        # Find all occurrences of 'wpn_' followed by letters/numbers/underscores.
        # Save data often contains paths or technical names with numeric tails (wpn_ak74_up12345).
        text = content.decode("latin-1", errors="ignore").lower()
        
        # Token extraction (everything that looks like a weapon ID)
        tokens = re.findall(r"(wpn_[a-z0-9_]+)", text)
        
        found = set()
        for token in tokens:
            if any(j in token for j in junk_ids): continue
            if "_hud" in token: continue
            
            # Remove numeric object-ID tail (e.g. wpn_ak74_12345 -> wpn_ak74_)
            base_token = re.sub(r"[0-9]+$", "", token)
            if not base_token: continue
            
            # Find the longest known prefix in token.
            # Example: token 'wpn_svds_pmc_gee3612345'
            # known contains 'wpn_svds_pmc_gee36' and 'wpn_svds_pmc'.
            # We want the more specific ID (gee36).
            best_match = None
            for w_id in known:
                if token.startswith(w_id):
                    # Ensure suffix is empty or numeric object tail only,
                    # not an attachment/variant suffix.
                    suffix = token[len(w_id):]
                    if not suffix or suffix.isdigit():
                        if best_match is None or len(w_id) > len(best_match):
                            best_match = w_id
            
            if best_match:
                found.add(best_match)

        return sorted(found)
    except Exception as e:
        print(f"Error reading save: {e}")
        return []
