import os, re, pandas as pd, tqdm
from pathlib import Path
from paths_config import get_path_list

# --- CONFIGURATION ---
SCAN_PATHS = get_path_list("scan_paths")
TEXT_PATHS = get_path_list("text_paths")
TEXTURE_PATHS = get_path_list("texture_paths")
OUT_DIR = Path("./loadout_lab_data")
os.makedirs(OUT_DIR, exist_ok=True)

# --- TRANSLATION LOADING ---
print("📝 Loading translations...")
translations = {}
import xml.etree.ElementTree as ET

for t_path in TEXT_PATHS:
    if not t_path.exists(): continue
    for root, dirs, files in os.walk(t_path):
        rel = Path(root).relative_to(t_path)
        rel_parts = [p.lower() for p in rel.parts]
        
        # PRIORITY: Only keep 'eng' (English).
        # Ignore everything in language folders that are not 'eng'.
        # Some mods may place st_*.xml directly under configs/text, so keep this conservative.
        languages_to_skip = ['spa', 'fra', 'rus', 'lat', 'ger', 'ita', 'pol', 'ptb']
        
        skip = False
        for lang in languages_to_skip:
            if lang in rel_parts:
                skip = True
                break
        if skip: continue
        
        # If path contains 'text' but not 'eng', check if sibling language folders exist.
        # Typical GAMMA structure is: .../configs/text/eng/file.xml
        if 'text' in rel_parts and 'eng' not in rel_parts:
            # If sibling language folders exist and current folder is not eng, skip.
            if any(os.path.isdir(os.path.join(root, "..", l)) for l in languages_to_skip):
                continue

        for f in files:
            if f.endswith(".xml"):
                try:
                    tree = ET.parse(os.path.join(root, f))
                    for string in tree.findall(".//string"):
                        s_id = string.get('id')
                        text_elem = string.find('text')
                        if s_id and text_elem is not None:
                            translations[s_id.lower()] = text_elem.text
                except: continue

def translate(s_id):
    if not s_id: return None
    return translations.get(str(s_id).lower())

# Aggressive list of scope/attachment suffixes to ignore
JUNK_SUFFIXES = [
    '_acog', '_eot', '_e0t2', '_ac10632', '_specter', '_leupold', '_aimpoint', 
    '_point_aimpro', '_ekp8_18', '_pn23', '_gauss_sight', '_marchf', '_kemper', 
    '_mepro', '_rakurs', '_0kp2', '_rmr', '_deltapoint', '_compm4s', '_pka', 
    '_1p29', '_kobra', '_ps01', '_1pn93', '_triji', '_spec_alt', '_mark8_rmr',
    '_romeo4', '_hco', '_t12', '_monstrum', '_trihawk', '_vulcan', '_echo1', '_gauss'
]

def clean_num(s):
    res = re.findall(r"[-+]?\d*\.\d+|\d+", str(s))
    return float(res[0]) if res else None

def get_weapon_class(sec, ammo, slot, d, registry):
    id_l, ammo, kind = sec.lower(), str(ammo).lower(), str(d.get('kind', '')).lower()
    
    # SNIPER Check (Higher Priority)
    sniper_keywords = ['sniper', 'vssk', 'svd', 'dvl', 'l96', 'm24', 'trg', 'm98', 'scout', 'remington', 'sr25', 'dmr']
    is_sniper = any(x in id_l or x in kind for x in sniper_keywords)
    
    # Ammo-based logic
    if any(x in ammo for x in ['12x70', '12x76', '23x75']): 
        return "Shotgun"
    
    # Heavy calibers
    if any(x in ammo for x in ['7.62x51', '7.62x54', '308', 'magnum_300', '338_lapua', '12.7x55']):
        if is_sniper: return "Sniper/DMR"
        if any(x in id_l for x in ['deagle', 'rex', 'mp412', 'desert_eagle']): return "Pistol"
        if slot == 1: return "Sidearm Heavy"
        return "Battle Rifle"
    
    if is_sniper: return "Sniper/DMR"
    
    # Slot 1 special handling (PDWs)
    if slot == 1:
        if any(x in id_l for x in ['p90', 'mp7', 'mp5k', 'aps']): return "SMG/PDW"
        return "Pistol"
    
    # LMG Check
    mag_size = clean_num(d.get('ammo_mag_size', 0))
    if mag_size and mag_size > 60: return "LMG"
    
    # SMG Check
    if any(x in id_l or x in kind for x in ['mp5', 'vityaz', 'ump', 'vector', 'pp2000', 'bizon', 'mp7', 'p90']): 
        return "SMG"
    
    # Sniper check for smaller calibers (e.g. VSS)
    if any(x in id_l or x in kind for x in ['vss', 'val', 'sr3', '7.62x39_sniper']): 
        return "Sniper/DMR"
    
    return "Assault Rifle"

print("📂 Scanning weapon data...")
registry = {}
for scan_path in SCAN_PATHS:
    if not scan_path.exists(): continue
    for root, _, files in os.walk(scan_path):
        p_parts = Path(root).parts
        mod_name = "Vanilla"
        if "mods" in p_parts:
            m_idx = p_parts.index("mods")
            if len(p_parts) > m_idx + 1: mod_name = p_parts[m_idx + 1]
            else: continue
        
        for f in files:
            if f.endswith(".ltx"):
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as l:
                        curr = None
                        for line in l:
                            line = line.strip()
                            if not line or line.startswith(';') or line.startswith('#'): continue
                            
                            # STALKER LTX syntax: [section]:parent or ![section] or [section]
                            if line.startswith('['):
                                # Extract section name inside brackets [...]
                                end_bracket_idx = line.find(']')
                                if end_bracket_idx == -1: continue
                                
                                sec = line[1:end_bracket_idx].strip(' !@')
                                parent = None
                                
                                # Find optional parent after closing bracket
                                remainder = line[end_bracket_idx+1:].strip()
                                if remainder.startswith(':'):
                                    parent = remainder[1:].strip().split(',')[0].strip()  # first parent base only
                                
                                # FILTER: skip if section ends with known scope/attachment suffix
                                if any(sec.lower().endswith(s) for s in JUNK_SUFFIXES):
                                    curr = None; continue
                                
                                if sec not in registry: 
                                    registry[sec] = {'id': sec, 'mod': mod_name, 'parent': parent, 'root': root}
                                
                                if parent: 
                                    registry[sec]['parent'] = parent
                                
                                curr = sec
                                continue
                            
                            if curr and '=' in line and not line.startswith('['):
                                parts = line.split('=', 1)
                                key = parts[0].strip().lower()
                                val = parts[1].split(';')[0].strip().strip('"')
                                registry[curr][key] = val
                except: continue

def get_v(sec, key, db, d=0):
    if d > 10 or not sec or sec not in db: return None
    if key in db[sec]: return db[sec][key]
    return get_v(db[sec].get('parent'), key, db, d+1)

final = []
# First identify "real" weapons (have gameplay stats or inherit from valid weapon bases)
for sec, d in tqdm.tqdm(registry.items()):
    if not sec.startswith("wpn_") or "_hud" in sec: continue
    
    # DLTX: ignore scope/attachment sections; NIMBLE remains a valid weapon id
    if any(sec.lower().endswith(s) for s in JUNK_SUFFIXES): continue
    
    hit = clean_num(get_v(sec, 'hit_power', registry))
    rpm = clean_num(get_v(sec, 'rpm', registry))
    gx = clean_num(get_v(sec, 'inv_grid_x', registry))
    
    if hit and gx is not None:
        slot = int(clean_num(get_v(sec, 'slot', registry)) or 2)
        ammo = str(get_v(sec, 'ammo_class', registry) or 'unknown').split(',')[0].replace('ammo_', '')
        
        # Resolve display name from localization
        inv_name_id = get_v(sec, 'inv_name', registry) or get_v(sec, 'inv_name_short', registry)
        real_name = translate(inv_name_id) or sec.replace('wpn_', '').replace('_', ' ').upper()

        # Icon Metadata
        gy = clean_num(get_v(sec, 'inv_grid_y', registry)) or 0
        gw = clean_num(get_v(sec, 'inv_grid_width', registry)) or 1
        gh = clean_num(get_v(sec, 'inv_grid_height', registry)) or 1
        tex = get_v(sec, 'icons_texture', registry) or "ui\\ui_icon_equipment"
        
        final.append({
            'id': sec, 'real_name': real_name, 'hit': hit, 'rpm': rpm, 'slot': slot,
            'acc': clean_num(get_v(sec, 'fire_dispersion_base', registry)) or 0.5,
            'rec': clean_num(get_v(sec, 'cam_dispersion', registry)) or 1.0,
            'mag': clean_num(get_v(sec, 'ammo_mag_size', registry)) or 30,
            'ammo': ammo,
            'mod': d['mod'], 
            'class': get_weapon_class(sec, ammo, slot, d, registry),
            'gx': gx, 'gy': gy, 'gw': gw, 'gh': gh, 'tex': tex
        })

df_final = pd.DataFrame(final).drop_duplicates('id')
df_final.to_csv(OUT_DIR / "weapons_stats.csv", index=False)
# Redundant print removed
# --- ICON EXTRACTION ---
print("🖼️ Searching textures for icons...")
import subprocess
from PIL import Image

def texture_priority(path_str):
    p = path_str.replace('\\', '/').lower()
    if "/.grok's modpack installer/resources/" in p:
        source_rank = 0
    elif "/mo2/mods/" in p:
        source_rank = 2
    else:
        source_rank = 1

    mod_rank = -1
    m = re.search(r"/mods/(\d+)-", p)
    if m:
        mod_rank = int(m.group(1))

    return (source_rank, mod_rank, len(path_str))

tex_candidates = {}
for start_p in TEXTURE_PATHS:
    if not start_p.exists():
        continue
    for root, _, files in os.walk(start_p):
        for f in files:
            if not f.lower().endswith(".dds"):
                continue
            f_path = os.path.join(root, f)
            name = Path(f).stem.lower()
            tex_candidates.setdefault(name, []).append(f_path)

tex_map = {}
for name, candidates in tex_candidates.items():
    tex_map[name] = max(candidates, key=texture_priority)

ICON_DIR = OUT_DIR / "icons"
os.makedirs(ICON_DIR, exist_ok=True)

print(f"✂️ Extracting {len(df_final)} icons...")
converted_cache = {}

for _, r in tqdm.tqdm(df_final.iterrows(), total=len(df_final)):
    tex_key = r['tex'].split('\\')[-1].lower()
    if tex_key not in tex_map: continue
    
    target_icon = ICON_DIR / f"{r['id']}.png"
    # Remove old icons to avoid stale outputs from previous extraction logic
    if target_icon.exists(): target_icon.unlink() 
    
    if tex_key not in converted_cache:
        tmp_png = OUT_DIR / f"tmp_{tex_key}.png"
        # Use ImageMagick to convert DDS to temporary PNG
        subprocess.run(["convert", tex_map[tex_key], str(tmp_png)], capture_output=True)
        if tmp_png.exists():
            try:
                converted_cache[tex_key] = Image.open(tmp_png).convert("RGBA")
                tmp_png.unlink()
            except: continue
    
    if tex_key in converted_cache:
        img = converted_cache[tex_key]
        # STALKER inventory grid uses 50 px per cell for inv_grid_* coordinates.
        cell_size = 50
        x = int(r['gx'] * cell_size)
        y = int(r['gy'] * cell_size)
        w = int(r['gw'] * cell_size)
        h = int(r['gh'] * cell_size)
        try:
            icon = img.crop((x, y, x + w, y + h))
            icon.save(target_icon)
        except: pass

print(f"✅ Done! Processed {len(df_final)} weapons.")
