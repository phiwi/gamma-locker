import streamlit as st
import pandas as pd
import numpy as np
import os, json
from itertools import product
from PIL import Image
import altair as alt
from save_reader import get_savegames, extract_weapons_from_scop

# --- CONFIG & PATHS ---
DATA_DIR = "loadout_lab_data"
LOCKER_FILE = os.path.join(DATA_DIR, "my_locker.json")
BACKUP_FILE = os.path.join(DATA_DIR, "my_locker_backup.json")
SAVE_DIR = "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/appdata/savedgames/"

# --- CONFIG & REGELN ---
GROUP_LIGHT = ['5.45x39', '5.56x45', '7.62x39', '9x39']
GROUP_HEAVY = ['7.62x51', '7.62x54', '12.7x55', '.300', '.338', '23x75', '12x76']
POWER_AMMO = GROUP_HEAVY + ['9x39', '23x75', '12x76']
FORBIDDEN_CLASSES = ["assault", "sniper", "dmr", "battle", "lmg", "shotgun", "rifle", "smg"]
SIDEARM_OVERRIDES = {
    "wpn_sr2_veresk",
    "wpn_sr2_veresk_sr2_upkit",
    "wpn_sr2_m1",
    "wpn_sr2_m2",
    "wpn_sr2_m1_p1x42",
    "wpn_sr2_m1_pk6",
    "wpn_sr2_m1_1p87",
    "wpn_sr2_m1_kp_sr2",
    "wpn_sr2_m1_aim_low",
    "wpn_sr2_m1_d0cter",
    "wpn_sr2_veresk_kp_sr2",
}

SIDEARM_SMG_PREFIXES = (
    "wpn_p90",
    "wpn_ps90",
    "wpn_eft_p90",
    "wpn_sr2_veresk",
    "wpn_sr2_m1",
    "wpn_sr2_m2",
    "wpn_mp5k",
    "wpn_eft_mp5k",
)

ICON_NO_CW_FALLBACK_PREFIXES = (
    "wpn_spas12",
)

def is_allowed_sidearm_smg(r):
    wpn_id = str(r.get('id', '')).lower()
    return any(wpn_id.startswith(prefix) for prefix in SIDEARM_SMG_PREFIXES)

def load_locker():
    if os.path.exists(LOCKER_FILE):
        try:
            with open(LOCKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_l():
    with open(LOCKER_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.locker, f, indent=2)

def backup_locker():
    if st.session_state.get('locker'):
        with open(BACKUP_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.locker, f, indent=2)

def restore_backup():
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "r", encoding="utf-8") as f:
            st.session_state.locker = json.load(f)
        save_l()
        return True
    return False

def prettify_ammo(ammo_raw):
    if pd.isna(ammo_raw):
        return ""
    text = str(ammo_raw)
    return text.split('_')[0]

def compute_score(row):
    hit = float(row.get('hit', 0))
    rpm = float(row.get('rpm', 0))
    rec = max(float(row.get('rec', 0)), 0.01)
    mag = float(row.get('mag', 0))
    return (hit * rpm) / rec + (mag * 0.5)

def load_icon_image(path):
    def open_visible_rgba(p):
        if not os.path.exists(p):
            return None
        rgba_local = Image.open(p).convert("RGBA")
        alpha_max = rgba_local.getchannel("A").getextrema()[1]
        if alpha_max == 0:
            return None
        return rgba_local

    rgba = open_visible_rgba(path)
    if rgba is None:
        root, ext = os.path.splitext(path)
        stem = os.path.basename(root)
        folder = os.path.dirname(path)
        candidates = []
        allow_cw_fallback = not any(stem.startswith(prefix) for prefix in ICON_NO_CW_FALLBACK_PREFIXES)

        if allow_cw_fallback and not stem.endswith("_cw"):
            candidates.append(os.path.join(folder, f"{stem}_cw{ext}"))

        parts = stem.split("_")
        for i in range(len(parts) - 1, 1, -1):
            base = "_".join(parts[:i])
            if allow_cw_fallback:
                candidates.append(os.path.join(folder, f"{base}_cw{ext}"))

        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            rgba = open_visible_rgba(candidate)
            if rgba is not None:
                break

    if rgba is None:
        return None

    r, g, b, a = rgba.split()

    orig_rgba = Image.merge("RGBA", (r, g, b, a))
    swap_rgba = Image.merge("RGBA", (b, g, r, a))

    def to_rgb_on_black(img_rgba):
        bg = Image.new("RGBA", img_rgba.size, (0, 0, 0, 255))
        bg.paste(img_rgba, mask=img_rgba.split()[-1])
        return bg.convert("RGB")

    orig_rgb = to_rgb_on_black(orig_rgba)
    swap_rgb = to_rgb_on_black(swap_rgba)

    # Manche DDS->PNG Exporte haben vertauschte R/B-Kanäle, andere nicht.
    # Wir wählen pro Icon die plausiblere Variante über Farbbalance.
    o_stat = orig_rgb.convert("RGB").resize((1, 1), Image.BOX).getpixel((0, 0))
    use_swapped = o_stat[2] > (o_stat[0] * 1.02)

    return swap_rgb if use_swapped else orig_rgb

def get_role(r):
    cls_raw = str(r.get('class', '')).lower()
    slot = int(r.get('slot', 0))
    ammo = str(r.get('ammo', '')).lower()
    wpn_id = str(r.get('id', ''))
    if wpn_id in SIDEARM_OVERRIDES:
        return "Sidearm"
    if slot == 1 and (cls_raw == "pistol" or ("smg" in cls_raw and is_allowed_sidearm_smg(r))):
        return "Sidearm"
    if "shotgun" in cls_raw:
        if any(x in cls_raw for x in ["sniper", "dmr", "battle", "lmg"]):
            return "Power"
        if "6.8x51" in ammo:
            return "Power"
        return "Workhorse"
    if any(x in cls_raw for x in ["sniper", "dmr", "battle", "lmg"]):
        return "Power"
    if "6.8x51" in ammo:
        return "Power"
    if any(a in ammo for a in POWER_AMMO):
        return "Power"
    return "Workhorse"

def load_data():
    df = pd.read_csv(os.path.join(DATA_DIR, "weapons_stats.csv"))
    # Drop melee/knife rows entirely (by class or name/id hints)
    melee_mask = df['class'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    name_mask = df['real_name'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    id_mask = df['id'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    df = df[~(melee_mask | name_mask | id_mask)].reset_index(drop=True)
    df['pretty_name'] = df.get('real_name', df['id'])
    df['ammo_display'] = df['ammo'].apply(prettify_ammo)
    if 'mutant_killer' not in df.columns:
        df['mutant_killer'] = False
    df['score'] = df.apply(compute_score, axis=1)
    df['role_label'] = df.apply(get_role, axis=1)
    return df

df = load_data()

if 'locker' not in st.session_state:
    st.session_state.locker = load_locker()

def is_ammo_conflict(w1, w2):
    if not w1 or not w2:
        return False
    a1, a2 = str(w1.get('ammo', '')).lower(), str(w2.get('ammo', '')).lower()
    if a1 == a2:
        return True

    in_light1 = any(g in a1 for g in GROUP_LIGHT)
    in_light2 = any(g in a2 for g in GROUP_LIGHT)
    c1, c2 = str(w1.get('class', '')).lower(), str(w2.get('class', '')).lower()
    is_hybrid = any(x in c1 for x in ["shotgun", "smg"]) or any(x in c2 for x in ["shotgun", "smg"])

    if (in_light1 or in_light2) and is_hybrid:
        return False
    if in_light1 and in_light2:
        return True
    in_heavy1 = any(g in a1 for g in GROUP_HEAVY)
    in_heavy2 = any(g in a2 for g in GROUP_HEAVY)
    if in_heavy1 and in_heavy2:
        return True
    return False

def is_valid_pair(w1, w2):
    return not is_ammo_conflict(w1, w2)

def is_valid_set(s, p, wh):
    return is_valid_pair(s, p) and is_valid_pair(s, wh) and is_valid_pair(p, wh)

def calculate_all_sets(inventory_ids, strategy):
    all_w_df = df[df['id'].isin(inventory_ids)].copy()
    all_w_df['role_label'] = all_w_df.apply(get_role, axis=1)

    def is_close_hybrid_row(r):
        if get_role(r) == "Sidearm":
            return False
        cls = str(r.get('class', '')).lower()
        slot = int(r.get('slot', 0))
        ammo = str(r.get('ammo', '')).lower()
        pistol_cals = ['9x19', '9x21', '9x18', '11.43x23', '.45', '45acp']
        is_pistol_cal = any(cal in ammo for cal in pistol_cals)
        return ('shotgun' in cls) or ('smg' in cls and slot != 1) or (is_pistol_cal and slot != 1)

    def is_true_sidearm_row(r):
        cls = str(r.get('class', '')).strip().lower()
        slot = int(r.get('slot', 0))
        wpn_id = str(r.get('id', ''))
        if wpn_id in SIDEARM_OVERRIDES:
            return True
        return slot == 1 and ("pistol" in cls or ("smg" in cls and is_allowed_sidearm_smg(r)))

    all_sidearms_df = all_w_df[all_w_df.apply(is_true_sidearm_row, axis=1)]

    all_w = all_w_df.to_dict('records')
    sidearms = all_sidearms_df.to_dict('records')
    powers = [w for w in all_w if w['role_label'] == 'Power']
    workhorses = [w for w in all_w if w['role_label'] == 'Workhorse']
    hybrids_close = [w for w in workhorses if is_close_hybrid_row(w)]

    if not all_w:
        return []
    if not sidearms or not powers or not workhorses:
        return []

    avg_s = all_sidearms_df['score'].mean() if not all_sidearms_df.empty else 0
    avg_p = all_w_df[all_w_df['role_label'] == 'Power']['score'].mean() if not all_w_df[all_w_df['role_label'] == 'Power'].empty else 0
    avg_wh = all_w_df[all_w_df['role_label'] == 'Workhorse']['score'].mean() if not all_w_df[all_w_df['role_label'] == 'Workhorse'].empty else 0
    target_average_score = avg_s + avg_p + avg_wh

    def get_fitness(w_set, target_avg):
        total_score = sum(w['score'] for w in w_set if w)
        if strategy == "Maxxed":
            return total_score
        return -abs(target_avg - total_score)

    usage = {w_id: 0 for w_id in inventory_ids}
    final_sets = []

    def add_set(triple, phase):
        order_idx = len(final_sets)
        for w in triple:
            if w:
                usage[w['id']] += 1
        final_sets.append({"weapons": [dict(w) for w in triple], "phase": phase, "order": order_idx})

    def redundant_count(triple):
        return sum(1 for w in triple if w and usage[w['id']] > 0)

    def usage_penalty(triple):
        return sum(usage[w['id']] for w in triple if w)

    # Phase 1: no redundancy
    while True:
        avail_p = [w for w in powers if usage[w['id']] == 0]
        avail_wh = [w for w in workhorses if usage[w['id']] == 0 and not is_close_hybrid_row(w)]
        avail_s = [w for w in sidearms if usage[w['id']] == 0]
        if not (avail_p and avail_wh and avail_s):
            break
        best = None
        best_f = -1e18
        for p, wh, s in product(avail_p, avail_wh, avail_s):
            if any(is_close_hybrid_row(w) for w in (p, wh, s)):
                continue
            if not is_valid_set(s, p, wh):
                continue
            f = get_fitness([p, wh, s], target_average_score)
            if f > best_f:
                best_f = f
                best = (p, wh, s)
        if not best:
            break
        add_set(best, "P1")

    # Phase 2H0: hybrid clean (exact triad), no redundancy
    while True:
        best = None
        best_f = -1e18
        for p, wh, s in product(powers, hybrids_close, sidearms):
            if usage[p['id']] > 0 or usage[wh['id']] > 0 or usage[s['id']] > 0:
                continue
            if not is_valid_set(s, p, wh):
                continue
            f = get_fitness([p, wh, s], target_average_score)
            if f > best_f:
                best_f = f
                best = (p, wh, s)
        if not best:
            break
        add_set(best, "P2H0")

    # Phase 1R1: exactly one redundant, two fresh
    while True:
        best = None
        best_f = -1e18
        for p, wh, s in product(powers, workhorses, sidearms):
            rcount = redundant_count((p, wh, s))
            fresh = sum(1 for w in (p, wh, s) if usage[w['id']] == 0)
            if rcount != 1 or fresh < 2:
                continue
            if not is_valid_set(s, p, wh):
                continue
            f = get_fitness([p, wh, s], target_average_score) - (rcount * 0.0001) - (usage_penalty((p, wh, s)) * 0.1)
            if f > best_f:
                best_f = f
                best = (p, wh, s)
        if not best:
            break
        add_set(best, "P1R1")

    # Phase 2H1: hybrid with exactly one redundancy (exact triad)
    while True:
        best = None
        best_f = -1e18
        for p, wh, s in product(powers, hybrids_close, sidearms):
            rcount = redundant_count((p, wh, s))
            fresh = sum(1 for w in (p, wh, s) if usage[w['id']] == 0)
            if rcount != 1 or fresh < 2:
                continue
            if not is_valid_set(s, p, wh):
                continue
            f = get_fitness([p, wh, s], target_average_score) - (rcount * 0.0001) - (usage_penalty((p, wh, s)) * 0.1)
            if f > best_f:
                best_f = f
                best = (p, wh, s)
        if not best:
            break
        add_set(best, "P2H1")

    # Phase 3: rest (any redundancy allowed), still exact triads only
    while True:
        best = None
        best_f = -1e18
        for p, wh, s in product(powers, workhorses, sidearms):
            triple = (p, wh, s)
            fresh = any(usage[x['id']] == 0 for x in triple)
            if not fresh and len(final_sets) > 0:
                continue
            if not is_valid_set(s, p, wh):
                continue
            f = get_fitness([p, wh, s], target_average_score) - (redundant_count(triple) * 0.001) - (usage_penalty(triple) * 0.1)
            if f > best_f:
                best_f = f
                best = triple
        if not best:
            break
        add_set(best, "P3")
        if not any(v == 0 for v in usage.values()):
            break

    return final_sets


# --- UI SIDEBAR ---
st.sidebar.title("🎒 Lager-Steuerung")
col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("💾 Speichern"):
    save_l()
    st.sidebar.success("Gespeichert")
if col_b2.button("🗑️ Leeren"):
    st.session_state.locker = []
    save_l()
    st.rerun()

# Geheimer Backup-Restore Button (unauffällig platziert)
with st.sidebar.expander("🛠️ Erweitert"):
    if st.button("⏪ Letztes Backup laden"):
        if restore_backup():
            st.success("Backup wiederhergestellt!")
            st.rerun()
        else:
            st.error("Kein Backup gefunden.")

if st.sidebar.button("🎲 50 Zufallswaffen laden"):
    st.session_state.locker = df['id'].sample(50).tolist()
    save_l()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🔌 Savegame-Import")
saves = get_savegames(SAVE_DIR)
if saves:
    selected_save = st.sidebar.selectbox("Speicherstand wählen", saves)
    col_sync1, col_sync2 = st.sidebar.columns(2)
    
    if col_sync1.button("📥 Alles hinzufügen"):
        with st.spinner("Scanne Savegame..."):
            all_ids = df['id'].unique().tolist()
            found = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
            if found:
                st.session_state.locker = list(set(st.session_state.locker + found))
                save_l()
                st.sidebar.success(f"{len(found)} Waffen hinzugefügt!")
                st.rerun()
    
    if col_sync2.button("🔄 Alles Ersetzen"):
        with st.spinner("Scanne Savegame..."):
            all_ids = df['id'].unique().tolist()
            found = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
            if found:
                st.session_state.locker = found
                save_l()
                st.sidebar.success(f"{len(found)} Waffen synchronisiert!")
                st.rerun()

    # NEU: Selektiver Import
    with st.sidebar.expander("🔍 Einzellne Waffen importieren"):
        all_ids = df['id'].unique().tolist()
        found_in_save = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
        if found_in_save:
            # Filtere Waffen, die NICHT bereits im Lager sind
            new_options = [w_id for w_id in found_in_save if w_id not in st.session_state.locker]
            
            if new_options:
                # Schöne Namen für die Auswahl generieren
                options_map = {}
                for w_id in new_options:
                    row = df[df['id'] == w_id]
                    name = row['pretty_name'].values[0] if not row.empty else w_id
                    options_map[f"{name} ({w_id})"] = w_id
                
                selected_to_add = st.multiselect("Wähle Fundstücke:", list(options_map.keys()))
                if st.button("➕ Auswahlt hinzufügen"):
                    ids_to_add = [options_map[sel] for sel in selected_to_add]
                    st.session_state.locker = list(set(st.session_state.locker + ids_to_add))
                    save_l()
                    st.success(f"{len(ids_to_add)} Waffen importiert!")
                    st.rerun()
            else:
                st.write("Alle Waffen dieses Saves sind bereits im Lager.")
else:
    st.sidebar.error("Keine Savegames gefunden.")

# --- HAUPTBEREICH ---
st.title("☢️ GAMMA Balanced Locker Master")
t0, t1, t2 = st.tabs(["🎒 Mein Lager", "🔍 Waffen-Suche", "⚖️ Strategie-Planer"])

with t0:
    st.header(f"Inhalt ({len(st.session_state.locker)} Waffen)")
    if not st.session_state.locker:
        st.info("Dein Lager ist leer. Nutze die Suche oder den Savegame-Import, um Waffen hinzuzufügen.")
    else:
        # Kompakte Tabellen-Ansicht für das Lager
        locker_df = df[df['id'].isin(st.session_state.locker)].copy()
        
        if not locker_df.empty:
            locker_df.insert(0, 'Entfernen', False)
            
            # Icons für ImageColumn
            def get_icon_path(w_id):
                # Absoluter Pfad wird oft für ImageColumn benötigt
                p = os.path.abspath(f"loadout_lab_data/icons/{w_id}.png")
                return p if os.path.exists(p) else None

            locker_df['Icon'] = locker_df['id'].apply(get_icon_path)
            
            display_df = locker_df[['Entfernen', 'Icon', 'id', 'pretty_name', 'class', 'hit', 'rpm', 'rec', 'mag', 'score']].copy()
            display_df.columns = ['Entfernen', 'Icon', 'ID', 'Name', 'Klasse', 'Damage', 'RPM', 'Recoil', 'Mag Size', 'Score']
            
            display_df['Score'] = display_df['Score'].round(3)
            display_df['Damage'] = (display_df['Damage'] * 100).astype(int)
            display_df['Recoil'] = display_df['Recoil'].round(3)
            display_df['Mag Size'] = display_df['Mag Size'].astype(int)
            display_df['RPM'] = display_df['RPM'].astype(int)
            
            edited_df = st.data_editor(
                display_df,
                hide_index=True,
                width='stretch',
                disabled=['Icon', 'Name', 'Klasse', 'Damage', 'RPM', 'Recoil', 'Mag Size', 'Score'],
                column_config={
                    "ID": None, # Verstecke die ID-Spalte
                    "Icon": st.column_config.ImageColumn("Icon", help="Waffenvorschau", width="small"),
                    "Entfernen": st.column_config.CheckboxColumn("❌", help="Markiere zum Entfernen", default=False),
                },
                key="locker_bulk_editor"
            )
            
            # Button zum Bestätigen des Löschvorgangs (verhindert Rerun beim Anklicken einzelner Checkboxen)
            if st.button("🗑️ Markierte Waffen jetzt entfernen"):
                to_remove = edited_df[edited_df['Entfernen'] == True]['ID'].tolist()
                if to_remove:
                    for w_id in to_remove:
                        if w_id in st.session_state.locker:
                            st.session_state.locker.remove(w_id)
                    save_l()
                    st.success(f"{len(to_remove)} Waffen entfernt!")
                    st.rerun()
                else:
                    st.info("Markiere zuerst Waffen in der Liste (Checkbox ❌), um sie zu löschen.")
        else:
            # Fallback, falls IDs im Locker sind, die nicht im df existieren
            for w_id in list(st.session_state.locker):
                st.write(f"Unbekannte Waffe: {w_id}")
                if st.button("Entfernen", key=f"rm_unk_{w_id}"):
                    st.session_state.locker.remove(w_id)
                    save_l()
                    st.rerun()

with t1:
    sq = st.text_input("Waffe suchen (z.B. osw, fn2000, honey)...").lower().strip()
    
    # Filtere Hits basierend auf Suchanfrage oder zeige alles wenn leer
    if sq == "":
        hits = df.sort_values('score', ascending=False)
    else:
        # Split search query into keywords for better matching
        keywords = sq.split()
        mask = pd.Series(True, index=df.index)
        for kw in keywords:
            mask &= (df['id'].str.lower().str.contains(kw, na=False) | 
                     df['pretty_name'].str.lower().str.contains(kw, na=False))
        hits = df[mask]
    
    if True: # Block immer ausführen
        # Melee / Knife / Axe / Tomahawk rausfiltern (klassenseitig und Namens-seitig)
        melee_pat = 'knife|melee|axe|tomahawk'
        hits = hits[~hits['class'].str.lower().str.contains(melee_pat, na=False)]
        hits = hits[~hits['pretty_name'].str.lower().str.contains(melee_pat, na=False)]
        hits = hits[~hits['id'].str.lower().str.contains(melee_pat, na=False)]
        # Duplikate nach pretty_name entfernen (erste behalten)
        hits = hits.drop_duplicates(subset=['pretty_name'])
        st.write(f"{len(hits)} Treffer")
        
        # Tabelle für Suchergebnisse vorbereiten
        if not hits.empty:
            # Berechne globales Ranking
            df['global_rank'] = df['score'].rank(ascending=False, method='min')
            
            # Berechne klassen-internes Ranking
            df['class_rank'] = df.groupby('class')['score'].rank(ascending=False, method='min')
            
            # Aktualisiere hits mit den neuen Rankings
            hits = df.loc[hits.index]
            
            # Zeige die Top 15 als detaillierte Liste mit Buttons
            for _, r in hits.head(15).iterrows():
                c_img, c_txt, c_btn = st.columns([1, 4, 1])
                img_path = f"loadout_lab_data/icons/{r['id']}.png"
                img = load_icon_image(img_path)
                if img is not None:
                    c_img.image(img, width=80)
                m = "🐗 " if r['mutant_killer'] else ""
                c_txt.write(f"{m}**{r['pretty_name']}** ({r['ammo_display']}) - *{r['class']}*")
                if r['id'] in st.session_state.locker:
                    if c_btn.button("Raus", key=f"main_rm_{r['id']}"):
                        st.session_state.locker.remove(r['id'])
                        save_l()
                        st.rerun()
                else:
                    if c_btn.button("Add", key=f"main_ad_{r['id']}"):
                        st.session_state.locker.append(r['id'])
                        save_l()
                        st.rerun()
            
            st.divider()
            st.subheader("📊 Detaillierte Stats der Suchergebnisse")
            
            # DataFrame für die Anzeige formatieren
            display_df = hits[['pretty_name', 'class', 'global_rank', 'class_rank', 'hit', 'rpm', 'rec', 'mag', 'score']].copy()
            display_df.columns = ['Name', 'Klasse', 'Global Rank', 'Class Rank', 'Damage', 'RPM', 'Recoil', 'Mag Size', 'Score']
            
            # Formatierung
            display_df['Global Rank'] = display_df['Global Rank'].astype(int)
            display_df['Class Rank'] = display_df['Class Rank'].astype(int)
            display_df['Score'] = display_df['Score'].round(3)
            # Damage als Raw-Wert (z.B. 0.53 -> 53)
            display_df['Damage'] = (display_df['Damage'] * 100).astype(int)
            display_df['Recoil'] = display_df['Recoil'].round(3)
            display_df['Mag Size'] = display_df['Mag Size'].astype(int)
            display_df['RPM'] = display_df['RPM'].astype(int)
            
            st.dataframe(display_df.sort_values('Score', ascending=False), width='stretch', hide_index=True)

with t2:
    if len(st.session_state.locker) < 3:
        st.warning("Füge mindestens 3 Waffen hinzu, um Sets zu planen.")
    else:
        # Diagnose: Rollenverteilung im aktuellen Lager
        locker_role_df = df[df['id'].isin(st.session_state.locker)].copy()
        role_counts_diag = locker_role_df['role_label'].value_counts()
        max_non_redundant_sets = 0
        if {'Sidearm', 'Power', 'Workhorse'}.issubset(role_counts_diag.index):
            max_non_redundant_sets = int(min(role_counts_diag['Sidearm'], role_counts_diag['Power'], role_counts_diag['Workhorse']))
        st.info(
            f"Rollen im Lager – Sidearm: {role_counts_diag.get('Sidearm',0)}, "
            f"Power: {role_counts_diag.get('Power',0)}, Workhorse: {role_counts_diag.get('Workhorse',0)} | "
            f"Theoretisch einzigartige Sets (ohne Wiederholung): {max_non_redundant_sets}"
        )

        strat = st.radio("Zuweisungs-Modus:", ["Balanced", "Maxxed"], horizontal=True)
        res_sets = calculate_all_sets(st.session_state.locker, strat)

        # Helper für Set-Klassifizierung (Farben) und Verteilung
        def is_close_hybrid_disp(w):
            if get_role(w) == "Sidearm":
                return False
            cls = str(w.get('class', '')).lower()
            slot = int(w.get('slot', 0))
            ammo = str(w.get('ammo', '')).lower()
            pistol_cals = ['9x19', '9x21', '9x18', '11.43x23', '.45', '45acp']
            is_pistol_cal = any(cal in ammo for cal in pistol_cals)
            return ('shotgun' in cls) or ('smg' in cls and slot != 1) or (is_pistol_cal and slot != 1)

        def classify_set(active_w, redundant_count):
            if len(active_w) < 3:
                return "🟥", "Multi-Redundant"
            has_hybrid = any(is_close_hybrid_disp(w) for w in active_w)
            if redundant_count == 0:
                return ("🟦", "Hybrid clean") if has_hybrid else ("🟩", "Triad clean")
            if redundant_count == 1:
                return ("🟧", "Hybrid +1R") if has_hybrid else ("🩵", "Triad +1R")
            return "🟥", "Multi-Redundant"

        # Verteilung über Set-Typen vorab berechnen (abhängig von Anzeige-Reihenfolge)
        type_counts = {"Triad clean": 0, "Hybrid clean": 0, "Triad +1R": 0, "Hybrid +1R": 0, "Multi-Redundant": 0}
        seen_for_dist = set()
        score_rows = []
        for s_entry in res_sets:
            active_w = [w for w in s_entry['weapons'] if w is not None]
            if not active_w:
                continue
            redundant_count = sum(1 for w in active_w if w['id'] in seen_for_dist)
            badge_symbol, lbl = classify_set(active_w, redundant_count)
            if lbl in type_counts:
                type_counts[lbl] += 1
            avg_score = sum(w['score'] for w in active_w) / len(active_w)
            score_rows.append({"Score": avg_score, "Label": lbl, "Badge": badge_symbol})
            for w in active_w:
                seen_for_dist.add(w['id'])

        st.header(f"⚖️ {len(res_sets)} generierte {strat} Loadouts")
        
        # --- STATISTIKEN ---
        with st.expander("📊 Lager-Statistiken & Verteilung"):
            st.write("Verteilung der Rollen und Munitionstypen in deinem Lager:")
            
            # Daten für Plots vorbereiten
            stats_df = df[df['id'].isin(st.session_state.locker)].copy()
            
            stats_df['role_label'] = stats_df.apply(get_role, axis=1)
            
            # Plot 1: Waffen pro Rolle
            role_counts = stats_df['role_label'].value_counts()
            # Plot 2: Top 10 Munitionstypen
            ammo_counts = stats_df['ammo_display'].value_counts().head(10)

            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.subheader("Waffen pro Rolle")
                st.bar_chart(role_counts)
            with s_col2:
                st.subheader("Häufigste Kaliber (Top 10)")
                st.bar_chart(ammo_counts)

            st.subheader("Set-Verteilung nach Farbe")
            dist_df = pd.DataFrame([
                {"Kategorie": k, "Anzahl": v} for k, v in type_counts.items()
            ])
            order = ["Triad clean", "Hybrid clean", "Triad +1R", "Hybrid +1R", "Multi-Redundant"]
            colors = ["#2ecc71", "#3498db", "#5dade2", "#e67e22", "#e74c3c"]
            chart = (
                alt.Chart(dist_df)
                .mark_bar()
                .encode(
                    x=alt.X("Kategorie", sort=order),
                    y=alt.Y("Anzahl"),
                    color=alt.Color("Kategorie", scale=alt.Scale(domain=order, range=colors), legend=None)
                )
                .properties(width="container")
            )
            st.altair_chart(chart)
            st.caption("Legende: 🟩 Triad clean | 🟦 Hybrid clean | 🩵 Triad +1R | 🟧 Hybrid +1R | 🟥 Multi-Redundant")
            with st.expander("Legende im Detail"):
                st.markdown(
                    "- 🟩 Triad clean: 0 Redundanz, klassisches Trio (Sidearm + Power + Workhorse) ohne Shotgun/SMG (Slot!=1)\n"
                    "- 🟦 Hybrid clean: 0 Redundanz, enthält Shotgun oder SMG (Slot!=1)\n"
                    "- 🩵 Triad +1R: genau 1 Redundanz, kein Hybrid\n"
                    "- 🟧 Hybrid +1R: genau 1 Redundanz, mit Shotgun/SMG (Slot!=1)\n"
                    "- 🟥 Multi-Redundant: zwei oder mehr Redundanzen")

            if score_rows:
                st.subheader("Score-Verteilung der Sets")
                score_df = pd.DataFrame(score_rows)
                score_chart = (
                    alt.Chart(score_df)
                    .mark_bar(opacity=0.8)
                    .encode(
                        x=alt.X("Score", bin=alt.Bin(maxbins=20)),
                        y=alt.Y("count()", title="Anzahl"),
                        color=alt.Color("Label", scale=alt.Scale(domain=order, range=colors))
                    )
                    .properties(width="container")
                )
                st.altair_chart(score_chart)
        
        # Würfel-Funktion für ein zufälliges Set
        if res_sets:
            if st.button("🎲 Zufälliges Loadout würfeln"):
                import random
                # Speichere sowohl das Set als auch dessen Index (+1 für Anzeige)
                idx = random.randrange(len(res_sets))
                st.session_state.random_set = res_sets[idx]
                st.session_state.random_set_num = idx + 1
            
            if 'random_set' in st.session_state:
                st.info(f"🎯 Dein gewürfeltes Loadout (Set #{st.session_state.random_set_num}):")
                r_cols = st.columns(3)
                labels = ["Sidearm", "Primary (Power)", "Secondary (Workhorse)"]
                set_order = [2, 0, 1]
                weapons = st.session_state.random_set['weapons']
                for i, idx2 in enumerate(set_order):
                    if idx2 >= len(weapons):
                        continue
                    w = weapons[idx2]
                    if w is None:
                        continue
                    with r_cols[i]:
                        st.subheader(w['pretty_name'])
                        st.caption(labels[i])
                st.divider()

        # Sortierungs-Option nun nach dem Würfeln
        sort_mode = st.radio("Sortierung der Sets:", ["Nach Score", "Nach Bildungsreihenfolge"], horizontal=True, key="sort_mode_sets")

        # Suchfeld für Set-Filterung
        set_search = st.text_input("🔎 Sets durchsuchen (z. B. spas12)", value="", key="set_search_query")

        # Sortierung anwenden
        if sort_mode == "Nach Score":
            phase_priority = {"P1": 0, "P2H0": 1, "P1R1": 2, "P2H1": 3, "P3": 4}
            def score_sort_key(s):
                active = [w for w in s['weapons'] if w is not None]
                avg_score = sum(w['score'] for w in active) / len(active) if active else 0
                return (phase_priority.get(s.get('phase', 'P3'), 99), -avg_score)
            res_sets = sorted(res_sets, key=score_sort_key)
        else:
            res_sets = sorted(res_sets, key=lambda s: s.get('order', 0))

        if set_search.strip():
            q = set_search.strip().lower()
            def matches_set(s_entry):
                for w in s_entry['weapons']:
                    if not w:
                        continue
                    haystack = " ".join([
                        str(w.get('pretty_name', '')),
                        str(w.get('real_name', '')),
                        str(w.get('id', '')),
                        str(w.get('ammo_display', '')),
                        str(w.get('class', '')),
                    ]).lower()
                    if q in haystack:
                        return True
                return False
            res_sets = [s for s in res_sets if matches_set(s)]
            st.caption(f"Gefilterte Sets: {len(res_sets)}")

        # Anzeige der Sets
        collapse_all = st.button("Alle einklappen")
        seen_ids = set()
        for idx, s_entry in enumerate(res_sets):
            s = s_entry['weapons']
            phase = s_entry.get('phase', "")
            active_w = [w for w in s if w is not None]
            if not active_w:
                continue
            avg = sum(w['score'] for w in active_w) / len(active_w)
            set_has_redundant = any(w['id'] in seen_ids for w in active_w)
            redundant_count = sum(1 for w in active_w if w['id'] in seen_ids)
            badge, badge_label = classify_set(active_w, redundant_count)
            title_suffix = " (🔄 Redundant)" if set_has_redundant else ""
            phase_label = f" {badge}" if badge else ""

            with st.expander(
                f"{phase_label} SET {idx+1}{title_suffix} (Ø-Rating: {avg:.2f})",
                expanded=(False if collapse_all else idx < 2)
            ):
                cols = st.columns(3)
                labels = ["Sidearm", "Primary (Power)", "Secondary (Workhorse)"]
                set_order = [2, 0, 1]
                st.caption(f"Badge: {badge} ({badge_label}) | Phase: {phase or 'n/a'} | Redundant: {set_has_redundant}")
                for i, idx2 in enumerate(set_order):
                    if idx2 >= len(s):
                        continue
                    w = s[idx2]
                    if w is None:
                        continue
                    with cols[i]:
                        img_path = f"loadout_lab_data/icons/{w['id']}.png"
                        img = load_icon_image(img_path)
                        if img is not None:
                            st.image(img, width='content')
                        st.write(f"*{labels[i]}*")
                        is_w_redundant = w['id'] in seen_ids
                        name_display = w['pretty_name'] + (" (🔄 Redundant)" if is_w_redundant else "")
                        if is_w_redundant:
                            st.markdown(f"### :green[{name_display}]")
                        else:
                            st.subheader(name_display)
                        if w['mutant_killer']:
                            st.caption("🐗 Mutant Killer")
                        st.write(f"📦 {w['ammo_display']}")
                        st.write(f"⭐ Score: {w['score']:.3f}")
                        st.progress(min(max(w['score'] / 100.0, 0.0), 1.0))
                    seen_ids.add(w['id'])
