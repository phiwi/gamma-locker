import os, re

def get_savegames(save_dir):
    if not os.path.exists(save_dir): return []
    files = [f for f in os.listdir(save_dir) if f.endswith('.scop')]
    # Sortiert nach Änderungsdatum (neueste zuerst)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(save_dir, x)), reverse=True)
    return files

def extract_weapons_from_scop(file_path, all_known_weapons):
    """
    Versucht Waffen-IDs aus einer binären .scop Datei zu extrahieren.
    Optimiert um nur tatsächliche Inventar-Items (nicht Modellpfade oder Welt-Stats) zu finden.
    """
    if not os.path.exists(file_path):
        return []
    try:
        known = sorted(set(all_known_weapons), key=len, reverse=True)
        # Junk-IDs, die oft in Welt-Daten erscheinen:
        junk_ids = {'wpn_binoc', 'wpn_knife', 'wpn_grenade', 'wpn_bolt'}

        # Primärquelle: .scoc enthält kompaktere/actor-nahe Metadaten
        scoc_path = file_path[:-5] + ".scoc" if file_path.lower().endswith(".scop") else file_path
        source_path = scoc_path if os.path.exists(scoc_path) else file_path

        import mmap
        with open(source_path, 'rb') as f:
            # Nutze mmap für effiziente Suche in großen Dateien
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                content = mm[:]

        # ASCII-Tokens aus Binärdaten extrahieren
        # Wir suchen nach allen Vorkommen von 'wpn_', gefolgt von Buchstaben/Zahlen.
        # Im Savegame stehen oft Pfade oder technische Namen mit Anhängseln (wpn_ak74_up12345).
        text = content.decode("latin-1", errors="ignore").lower()
        
        # Token-Extraktion (Alles was wie eine Waffen-ID aussieht)
        tokens = re.findall(r"(wpn_[a-z0-9_]+)", text)
        
        found = set()
        for token in tokens:
            if any(j in token for j in junk_ids): continue
            if "_hud" in token: continue
            
            # Entferne die numerische Objekt-ID am Ende (z.B. wpn_ak74_12345 -> wpn_ak74_)
            base_token = re.sub(r"[0-9]+$", "", token)
            if not base_token: continue
            
            # Wir suchen das längste bekannte Präfix im Token.
            # Beispiel: Token 'wpn_svds_pmc_gee3612345'
            # known enthält 'wpn_svds_pmc_gee36' und 'wpn_svds_pmc'.
            # Wir wollen die spezifischere ID (gee36) finden.
            best_match = None
            for w_id in known:
                if token.startswith(w_id):
                    # Checke ob nach der ID nur noch Zahlen kommen (die Objekt-ID)
                    # oder ob wir gerade ein Attachment-Suffix matchen.
                    suffix = token[len(w_id):]
                    if not suffix or suffix.isdigit():
                        if best_match is None or len(w_id) > len(best_match):
                            best_match = w_id
            
            if best_match:
                found.add(best_match)

        return sorted(found)

        return sorted(found)
    except Exception as e:
        print(f"Error reading save: {e}")
        return []
