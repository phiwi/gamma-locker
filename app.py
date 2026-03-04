import streamlit as st
import pandas as pd
import os, json
import re
import random
from itertools import product
from PIL import Image
import altair as alt
from save_reader import get_savegames, extract_weapons_from_scop
from paths_config import get_path

# --- CONFIG & PATHS ---
DATA_DIR = "loadout_lab_data"
LOCKER_FILE = os.path.join(DATA_DIR, "my_locker.json")
BACKUP_FILE = os.path.join(DATA_DIR, "my_locker_backup.json")
UI_PREFS_FILE = os.path.join(DATA_DIR, "ui_prefs.json")
SAVE_DIR = "/mnt/c/G.A.M.M.A/Anomaly-1.5.3-Full.2/appdata/savedgames/"
SAVE_DIR = str(get_path("save_dir", SAVE_DIR))

# --- CONFIG & RULES ---
GROUP_LIGHT = ['5.45x39', '5.56x45', '7.62x39', '9x39']
GROUP_HEAVY = ['7.62x51', '7.62x54', '12.7x55', '.300', '.338', '23x75', '12x76']
POWER_AMMO = GROUP_HEAVY + ['23x75', '12x76']
FORBIDDEN_CLASSES = ["assault", "sniper", "dmr", "battle", "lmg", "shotgun", "rifle", "smg"]
SIDEARM_SMG_PREFIXES = (
    "wpn_mp5k",
    "wpn_eft_mp5k",
    "wpn_sr2_",
    "wpn_sr2_veresk",
    "wpn_p90",
    "wpn_ps90",
    "wpn_eft_p90",
)
ICON_NO_CW_FALLBACK_PREFIXES = (
    "wpn_spas12",
)

CALIBER_WEIGHT_PATTERNS = [
    ("9x18", 0.72),
    ("9x19", 0.72),
    ("9x21", 0.82),
    ("11.43x23", 0.88),
    (".45", 0.88),
    ("45acp", 0.88),
    ("5.45x39", 1.00),
    ("5.56x45", 1.08),
    ("6.8x51", 1.20),
    ("7.62x39", 1.10),
    ("7.62x51", 1.25),
    ("7.62x54", 1.30),
    ("9x39", 1.15),
    ("12x70", 1.18),
    ("12x76", 1.22),
    ("23x75", 1.30),
    ("12.7x55", 1.35),
    (".300", 1.28),
    (".338", 1.40),
]

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

def load_ui_prefs():
    if os.path.exists(UI_PREFS_FILE):
        try:
            with open(UI_PREFS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}

def save_ui_prefs():
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "strategy_mode": st.session_state.get("strategy_mode", "Balanced"),
        "sort_mode_sets": st.session_state.get("sort_mode_sets", "By score"),
        "set_search_query": st.session_state.get("set_search_query", ""),
        "search_result_limit": st.session_state.get("search_result_limit", 30),
        "show_raw_stats_cards": st.session_state.get("show_raw_stats_cards", False),
    }
    with open(UI_PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def init_ui_prefs():
    prefs = load_ui_prefs()
    defaults = {
        "strategy_mode": "Balanced",
        "sort_mode_sets": "By score",
        "set_search_query": "",
        "search_result_limit": 30,
        "show_raw_stats_cards": False,
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = prefs.get(key, default_value)

def render_startup_health():
    config_ok = os.path.exists("paths_config.json")
    stats_ok = os.path.exists(os.path.join(DATA_DIR, "weapons_stats.csv"))
    icon_dir = os.path.join(DATA_DIR, "icons")
    icon_count = 0
    if os.path.isdir(icon_dir):
        try:
            icon_count = sum(1 for name in os.listdir(icon_dir) if name.lower().endswith(".png"))
        except Exception:
            icon_count = 0
    icons_ok = icon_count > 0

    if config_ok and stats_ok and icons_ok:
        st.sidebar.success("🩺 Startup health: ready")
        return

    st.sidebar.warning("🩺 Startup health: action needed")
    with st.sidebar.expander("Show checks"):
        st.write(f"paths_config.json: {'✅' if config_ok else '❌'}")
        st.write(f"weapons_stats.csv: {'✅' if stats_ok else '❌'}")
        st.write(f"icons/*.png: {'✅' if icons_ok else '❌'} ({icon_count} found)")
        if not config_ok:
            st.caption("Fix: create/update paths_config.json in project root.")
        if not stats_ok:
            st.caption("Fix: run python3 scraper.py to generate weapons_stats.csv.")
        if not icons_ok:
            st.caption("Fix: run python3 scraper.py to extract icon PNGs.")

def apply_unified_score_to_df():
    df['score'] = df['final_score']

def prettify_ammo(ammo_raw):
    if pd.isna(ammo_raw):
        return ""
    text = str(ammo_raw)
    return text.split('_')[0]

def parse_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None

def compute_score(row):
    hit = float(row.get('hit', 0))
    rpm = float(row.get('rpm', 0))
    rec = max(float(row.get('rec', 0)), 0.01)
    mag = float(row.get('mag', 0))
    return (hit * rpm) / rec + (mag * 0.5)

def get_caliber_weight(ammo_raw):
    ammo = str(ammo_raw or "").lower()
    for pattern, weight in CALIBER_WEIGHT_PATTERNS:
        if pattern in ammo:
            return weight
    return 1.0

def compute_adjusted_score(row):
    # revamped formula to better reward "laser" weapons (high rpm + low recoil)
    # and to factor in handling / horizontal recoil.  This should elevate the
    # FN‑2000 family, Howa Type‑20, etc. without needing hardcoded bonuses.
    hit = float(row.get('hit', 0))
    rpm = float(row.get('rpm', 0))
    rec = max(float(row.get('rec', 0)), 0.01)
    rec_hor = float(row.get('rec_hor', rec))
    handling = float(row.get('handling', 1))
    mag = float(row.get('mag', 0))
    adjusted_hit = hit * get_caliber_weight(row.get('ammo', ''))

    # base DPS-like term, weighted more heavily towards vertical recoil but
    # allowing good horizontal control to shine as well
    base = (adjusted_hit * rpm) / (rec * 0.75 + rec_hor * 0.25)

    # small handling bonus (for lightweight/ergonomic designs)
    base *= 1.0 + (handling - 1.0) * 0.1

    # retain magazine size bonus
    return base + (mag * 0.5)

def get_score_bucket(row):
    cls_raw = str(row.get('class', '')).lower()
    rpm = float(row.get('rpm', 0) or 0)

    if 'sniper/dmr' in cls_raw:
        return 'DMR' if rpm >= 120 else 'Bolt-Action Sniper'
    if 'smg/pdw' in cls_raw:
        return 'SMG/PDW'
    if 'battle rifle' in cls_raw:
        return 'Battle Rifle'
    if 'assault rifle' in cls_raw:
        return 'Assault Rifle'
    if 'shotgun' in cls_raw:
        return 'Shotgun'
    if 'lmg' in cls_raw:
        return 'LMG'
    if 'sidearm heavy' in cls_raw:
        return 'Sidearm Heavy'
    if 'pistol' in cls_raw:
        return 'Pistol'
    if 'smg' in cls_raw:
        return 'SMG'
    return str(row.get('class', 'Unknown'))

def compute_class_normalized_scores(df_local):
    ranked = (
        df_local
        .groupby('score_bucket')['raw_adjusted']
        .rank(method='average', pct=True)
        .fillna(0)
    )
    return ranked * 100.0

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
        
        # Manual fix: Base SPAS-12 icon often extracts as invisible. Fall back to custom variant.
        if stem == "wpn_spas12":
            candidates.append(os.path.join(folder, f"wpn_spas12_custom{ext}"))
            
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

    # Some DDS->PNG exports have swapped R/B channels, others do not.
    # Choose the more plausible variant per icon via a simple color-balance heuristic.
    o_stat = orig_rgb.convert("RGB").resize((1, 1), Image.BOX).getpixel((0, 0))
    use_swapped = o_stat[2] > (o_stat[0] * 1.02)

    return swap_rgb if use_swapped else orig_rgb

def get_role(r):
    cls_raw = str(r.get('class', '')).lower()
    slot = int(r.get('slot', 0))
    ammo = str(r.get('ammo', '')).lower()
    wpn_id = str(r.get('id', '')).lower()
    if any(wpn_id.startswith(prefix) for prefix in SIDEARM_SMG_PREFIXES):
        return "Sidearm"
    if slot == 1 and cls_raw == "pistol":
        return "Sidearm"
    # Everything classified as a sniper/DMR should never become a Workhorse slot;
    # they belong in the Power category regardless of ammunition string. This also
    # covers oddball shotguns (e.g. Remington 700 "Archangel") whose internal
    # class is "Sniper/DMR" but whose ammo would otherwise make them workhorses.
    if "sniper" in cls_raw or "dmr" in cls_raw:
        return "Power"
    if "6.8x51" in ammo or any(a in ammo for a in POWER_AMMO):
        return "Power"
    return "Workhorse"

def load_data():
    stats_file = os.path.join(DATA_DIR, "weapons_stats.csv")
    if not os.path.exists(stats_file):
        st.error("Missing loadout_lab_data/weapons_stats.csv. Run: python3 scraper.py")
        st.stop()
    df = pd.read_csv(stats_file)
    
    # Manual Data Overrides
    df.loc[df['id'] == 'wpn_fn2000_nimble', 'real_name'] = 'FN F2000 "Competitor"'
    
    # Drop melee/knife rows entirely (by class or name/id hints)
    melee_mask = df['class'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    name_mask = df['real_name'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    id_mask = df['id'].fillna('').str.lower().str.contains('knife|melee|axe|tomahawk', na=False)
    df = df[~(melee_mask | name_mask | id_mask)].reset_index(drop=True)
    df['pretty_name'] = df.get('real_name', df['id'])
    df['ammo_display'] = df['ammo'].apply(prettify_ammo)
    if 'mutant_killer' not in df.columns:
        df['mutant_killer'] = False
    df['raw_score'] = df.apply(compute_score, axis=1)
    df['raw_adjusted'] = df.apply(compute_adjusted_score, axis=1)
    df['recoil_rating'] = (1.0 - df['rec'].rank(method='average', pct=True).fillna(0.5)) * 100.0
    df['score_bucket'] = df.apply(get_score_bucket, axis=1)
    df['class_norm_score'] = compute_class_normalized_scores(df)
    df['final_score'] = df['raw_adjusted']
    df['score'] = df['final_score']
    df['role_label'] = df.apply(get_role, axis=1)
    return df

df = load_data()

if 'locker' not in st.session_state:
    st.session_state.locker = load_locker()

init_ui_prefs()
apply_unified_score_to_df()

def is_ammo_conflict(w1, w2):
    if not w1 or not w2:
        return False
    a1, a2 = str(w1.get('ammo', '')).lower(), str(w2.get('ammo', '')).lower()
    if a1 == a2:
        return True

    in_light1 = any(g in a1 for g in GROUP_LIGHT)
    in_light2 = any(g in a2 for g in GROUP_LIGHT)
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

# --- pluggable scoring / role hooks ------------------------------------------------
# Users may optionally specify custom functions via a JSON config file. The
# values must be dotted paths to callables, e.g. "my_mod.balance.compute_score".
import json, importlib
BALANCE_CFG_PATH = "balance_config.json"
if os.path.exists(BALANCE_CFG_PATH):
    try:
        cfg = json.load(open(BALANCE_CFG_PATH))
        if 'score_function' in cfg:
            mod, func = cfg['score_function'].rsplit('.', 1)
            compute_adjusted_score = getattr(importlib.import_module(mod), func)
        if 'role_function' in cfg:
            mod, func = cfg['role_function'].rsplit('.', 1)
            get_role = getattr(importlib.import_module(mod), func)
    except Exception as e:
        st.warning(f"Failed loading balance_config.json: {e}")

# Internal caching to speed up repeated drafts with identical inventory/strategy
from functools import lru_cache

@lru_cache(maxsize=128)
def _cached_sets(inventory_tuple, strategy):
    # convert back to list; perform full calculation here
    return _raw_calculate_all_sets(list(inventory_tuple), strategy)

def calculate_all_sets(inventory_ids, strategy):
    return _cached_sets(tuple(inventory_ids), strategy)

# move the previous body into _raw_calculate_all_sets

def _raw_calculate_all_sets(inventory_ids, strategy):
    all_w_df = df[df['id'].isin(inventory_ids)].copy()
    all_w_df['role_label'] = all_w_df.apply(get_role, axis=1)

    score_field = 'final_score'

    def score_of(w):
        return float(w.get(score_field, w.get('score', 0)))

    all_sidearms_df = all_w_df[all_w_df['role_label'] == 'Sidearm']

    all_w = all_w_df.to_dict('records')
    sidearms = all_sidearms_df.to_dict('records')
    powers = [w for w in all_w if w['role_label'] == 'Power']
    # Workhorse darf nur Light, MP oder Shotgun sein (Heavy-Kaliber ausgeschlossen)
    def is_valid_workhorse(w):
        # Disallow sniper-class guns from ever being considered a workhorse.  They
        # are already handled above by get_role(), but this extra guard ensures
        # future tweaks won't accidentally reintroduce a bad pair.
        cls_raw = str(w.get('class','')).lower()
        if 'sniper' in cls_raw or 'dmr' in cls_raw:
            return False
        # everything else is fine; this function exists mostly for flavor and
        # to highlight constraints in the orange-tier fallback.
        return True
    workhorses = [w for w in all_w if w['role_label'] == 'Workhorse' and is_valid_workhorse(w)]

    def is_light_weapon(w):
        ammo = str(w.get('ammo', '')).lower()
        return any(cal in ammo for cal in GROUP_LIGHT)

    def is_mp_or_shotgun_workhorse(w):
        cls = str(w.get('class', '')).lower()
        return ('smg' in cls) or ('shotgun' in cls)

    flex_light_powers = [w for w in workhorses if is_light_weapon(w)]
    hybrid_workhorses = [w for w in workhorses if is_mp_or_shotgun_workhorse(w)]
    base_power_ids = {w['id'] for w in powers}
    flex_light_ids = {w['id'] for w in flex_light_powers}

    if not all_w:
        return []
    if not sidearms or not powers or not workhorses:
        return []

    avg_s = all_sidearms_df[score_field].mean() if not all_sidearms_df.empty else 0
    avg_p = all_w_df[all_w_df['role_label'] == 'Power'][score_field].mean() if not all_w_df[all_w_df['role_label'] == 'Power'].empty else 0
    avg_wh = all_w_df[all_w_df['role_label'] == 'Workhorse'][score_field].mean() if not all_w_df[all_w_df['role_label'] == 'Workhorse'].empty else 0
    target_average_score = avg_s + avg_p + avg_wh

    usage = {w_id: 0 for w_id in inventory_ids}
    final_sets = []

    def get_tier_info(triple):
        p, wh, s = triple
        red_count = sum(1 for w in (p, wh, s) if usage.get(w['id'], 0) > 0)
        
        is_p_heavy = p['id'] in base_power_ids
        is_p_light = p['id'] in flex_light_ids
        is_wh_light = is_light_weapon(wh)
        is_wh_hybrid = is_mp_or_shotgun_workhorse(wh)
        
        is_standard = is_p_heavy and is_wh_light
        is_heavy_hybrid = is_p_heavy and is_wh_hybrid
        
        sub_name = "Light Hybrid"
        sub_val = 3
        if is_standard:
            sub_name = "Standard"
            sub_val = 1
        elif is_heavy_hybrid:
            sub_name = "Heavy Hybrid"
            sub_val = 2

        if red_count == 0:
            return 10 + sub_val, "🟩", f"Green: Flawless ({sub_name})"
        elif red_count == 1:
            return 20 + sub_val, "🟦", f"Blue: Single Deficit ({sub_name})"
        else:
            return 30 + sub_val, "🟧", f"Orange: Double Deficit ({sub_name})"

    def add_set(triple, phase):
        order_idx = len(final_sets)
        active_triple = [w for w in triple if w]
        full_scores = [score_of(w) for w in active_triple]
        
        tier_val, badge, tier_name = get_tier_info(triple)

        weapon_payload = []
        for w in triple:
            w_copy = dict(w)
            w_copy['score'] = score_of(w)
            weapon_payload.append(w_copy)
            
        for w in triple:
            if w:
                usage[w['id']] += 1
                
        final_sets.append({
            "weapons": weapon_payload,
            "phase": phase,
            "order": order_idx,
            "badge": badge,
            "tier_val": tier_val,
            "tier_name": tier_name,
            "fitness": triple_fitness(triple),
            "avg_score": (sum(full_scores) / len(full_scores)) if full_scores else 0.0,
        })

    def triple_total(triple):
        # when maximizing, redundant weapons (usage>0) should not contribute
        # to the score.  This prevents old sidearms/others from inflating a set's
        # fitness and ensures active inventory drives ordering.
        total = 0.0
        for w in triple:
            uid = w.get('id')
            if uid and usage.get(uid, 0) == 0:
                total += score_of(w)
        return total

    def triple_fitness(triple):
        total = triple_total(triple)
        if strategy == "Maxxed":
            return total
        return -abs(target_average_score - total)

    def choose_best(candidates):
        if not candidates:
            return None
        
        tier_groups = {}
        for t in candidates:
            tv, _, _ = get_tier_info(t)
            tier_groups.setdefault(tv, []).append(t)
        
        for tv in sorted(tier_groups.keys()):
            group = tier_groups[tv]
            
            # Green Tiers (11, 12, 13)
            if tv < 20:
                best_f = max(triple_fitness(t) for t in group)
                top = [t for t in group if triple_fitness(t) == best_f]
                return random.choice(top)
            
            # Redundant tiers (Blue: 20+, Orange: 30+)
            if strategy == "Balanced":
                f_scores = [triple_fitness(t) for t in group]
                max_f = max(f_scores)
                min_f = min(f_scores)
                threshold = max_f - (max_f - min_f) * 0.4
                balanced_group = [t for t in group if triple_fitness(t) >= threshold]
                return random.choice(balanced_group)
            
            return random.choice(group)
        return None

    # Draft loop: Continue as long as we can find ANY valid set 
    # that uses at least one new weapon (to ensure progress).
    # The tiers will naturally guide the order via choose_best.
    while True:
        unused_ids = [w_id for w_id, count in usage.items() if count == 0]
        if not unused_ids:
            break
            
        candidate_triples = []
        
        # 1. Normal sets (Heavy + Light)
        for p, wh, s in product(powers, workhorses, sidearms):
            if not is_valid_set(s, p, wh): continue
            if not is_light_weapon(wh): continue # Strict pure mode check
            
            # To ensure we finish drafting, we must use at least one unused weapon
            if any(w['id'] in unused_ids for w in (p, wh, s)):
                candidate_triples.append((p, wh, s))
                
        # 2. Hybrid sets (Heavy/Light + MP/Shotgun)
        # Note: powers contains heavy, flex_light_powers contains light
        all_potential_p = list({w['id']: w for w in powers + flex_light_powers}.values())
        for p, wh, s in product(all_potential_p, hybrid_workhorses, sidearms):
            if not is_valid_set(s, p, wh): continue
            if any(w['id'] in unused_ids for w in (p, wh, s)):
                candidate_triples.append((p, wh, s))

        # 3. Orange Tier / Absolute Failsafe:
        # If no standard or hybrid set fits because we just have 13 snipers left, we just jam them into a set.
        if not candidate_triples:
            unused = [w for w in all_w if w['id'] in unused_ids]
            if unused:
                # To strictly obey slot rules (Power, Workhorse, Sidearm), grab available unused items by class
                u_p = [w for w in unused if w.get('role_label') == 'Power']
                u_w = [w for w in unused if w.get('role_label') == 'Workhorse']
                u_s = [w for w in unused if w.get('role_label') == 'Sidearm']

                p = random.choice(u_p) if u_p else random.choice(powers)
                wh = random.choice(u_w) if u_w else random.choice(workhorses)
                s = random.choice(u_s) if u_s else random.choice(sidearms)

                candidate_triples.append((p, wh, s))

        best = choose_best(candidate_triples)
        if not best:
            # If no set uses an unused weapon, we might have weird orphaned weapons.
            # Mark them as "used" to exit loop.
            for uid in unused_ids:
                usage[uid] += 1
            break
            
        tv, _, _ = get_tier_info(best)
        add_set(best, f"T{tv}")

    # Final sorting by tier, then fitness
    final_sets.sort(key=lambda x: (x.get('tier_val', 5), -x['fitness']))

    return final_sets


# --- UI SIDEBAR ---
render_startup_health()
st.sidebar.title("🎒 Locker Controls")
# new filtering options
hide_redundant = st.sidebar.checkbox("Hide redundant weapons", value=False,
    help="Remove any weapon that has already appeared in an earlier drafted set.")
role_filter = st.sidebar.multiselect(
    "Show roles", ["Sidearm","Power","Workhorse"],
    default=["Sidearm","Power","Workhorse"], help="Limit visible weapons to these roles."
)
col_b1, col_b2 = st.sidebar.columns(2)
if col_b1.button("💾 Save"):
    save_l()
    st.sidebar.success("Saved")
if col_b2.button("🗑️ Clear"):
    st.session_state.locker = []
    save_l()
    st.rerun()

# Hidden backup restore controls
with st.sidebar.expander("🛠️ Advanced"):
    if st.button("⏪ Restore latest backup"):
        if restore_backup():
            st.success("Backup restored!")
            st.rerun()
        else:
            st.error("No backup found.")

if st.sidebar.button("🎲 Load 50 random weapons"):
    st.session_state.locker = df['id'].sample(50).tolist()
    save_l()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📈 Scoring")
st.sidebar.caption("Unified score active: caliber-adjusted weapon score for all modes.")
apply_unified_score_to_df()
save_ui_prefs()

st.sidebar.divider()
st.sidebar.subheader("🔌 Savegame import")
saves = get_savegames(SAVE_DIR)
if saves:
    selected_save = st.sidebar.selectbox("Select savegame", saves)
    col_sync1, col_sync2 = st.sidebar.columns(2)
    
    if col_sync1.button("📥 Add all"):
        with st.spinner("Scanning savegame..."):
            all_ids = df['id'].unique().tolist()
            found = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
            if found:
                before = set(st.session_state.locker)
                unique_found = list(dict.fromkeys(found))
                new_count = sum(1 for item in unique_found if item not in before)
                already_count = len(unique_found) - new_count
                st.session_state.locker = list(before.union(unique_found))
                save_l()
                st.sidebar.success(f"Import summary: {new_count} new, {already_count} already present (found: {len(unique_found)}).")
                st.rerun()
            else:
                st.sidebar.warning("No known weapons found in this savegame.")
    
    if col_sync2.button("🔄 Replace all"):
        with st.spinner("Scanning savegame..."):
            all_ids = df['id'].unique().tolist()
            found = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
            if found:
                previous_count = len(st.session_state.locker)
                unique_found = list(dict.fromkeys(found))
                st.session_state.locker = unique_found
                save_l()
                st.sidebar.success(f"Replace summary: now {len(unique_found)} weapons (previously {previous_count}).")
                st.rerun()
            else:
                st.sidebar.warning("No known weapons found in this savegame.")

    # Selective import
    with st.sidebar.expander("🔍 Import selected weapons"):
        all_ids = df['id'].unique().tolist()
        found_in_save = extract_weapons_from_scop(os.path.join(SAVE_DIR, selected_save), all_ids)
        if found_in_save:
            # Only show weapons not already present in locker
            new_options = [w_id for w_id in found_in_save if w_id not in st.session_state.locker]
            
            if new_options:
                rows = []
                for w_id in new_options:
                    row = df[df['id'] == w_id]
                    if not row.empty:
                        rows.append({
                            "Add": False,
                            "_ID": w_id,
                            "Name": row['pretty_name'].values[0],
                        })
                    else:
                        rows.append({
                            "Add": False,
                            "_ID": w_id,
                            "Name": w_id,
                        })

                selectable_df = pd.DataFrame(rows)
                edited_select_df = st.data_editor(
                    selectable_df,
                    hide_index=True,
                    width='stretch',
                    disabled=['_ID', 'Name'],
                    column_config={
                        "Add": st.column_config.CheckboxColumn("Add", default=False),
                        "_ID": None,
                    },
                    key=f"save_import_select_table_{selected_save}"
                )

                if st.button("➕ Add selected"):
                    ids_to_add = edited_select_df[edited_select_df['Add'] == True]['_ID'].tolist()
                    if ids_to_add:
                        st.session_state.locker = list(set(st.session_state.locker + ids_to_add))
                        save_l()
                        st.success(f"Imported {len(ids_to_add)} selected weapons.")
                        st.rerun()
                    else:
                        st.info("No weapons selected.")
            else:
                st.write("All weapons from this save are already in your locker.")
else:
    st.sidebar.error("No savegames found.")

# --- MAIN AREA ---
st.title("☢️ GAMMA Locker")
t0, t1, t2 = st.tabs(["🎒 My Locker", "🔍 Weapon Search", "⚖️ Strategy Planner"])

with t0:
    st.header(f"Contents ({len(st.session_state.locker)} weapons)")
    if not st.session_state.locker:
        st.info("Your locker is empty. Use search or savegame import to add weapons.")
        q1, q2 = st.columns(2)
        with q1:
            if saves:
                quick_save = st.selectbox("Quick import from savegame", saves, key="quick_empty_save")
                if st.button("📥 Import all from selected save", key="quick_empty_import"):
                    all_ids = df['id'].unique().tolist()
                    found_quick = extract_weapons_from_scop(os.path.join(SAVE_DIR, quick_save), all_ids)
                    if found_quick:
                        unique_found = list(dict.fromkeys(found_quick))
                        st.session_state.locker = list(set(st.session_state.locker + unique_found))
                        save_l()
                        st.success(f"Imported {len(unique_found)} weapons from savegame.")
                        st.rerun()
                    else:
                        st.warning("No known weapons found in selected savegame.")
            else:
                st.caption("No savegames found in configured SAVE_DIR.")
        with q2:
            if st.button("🎲 Add 20 random starter weapons", key="quick_random_20"):
                count = min(20, len(df))
                st.session_state.locker = df['id'].sample(count).tolist()
                save_l()
                st.success(f"Added {count} random weapons.")
                st.rerun()
    else:
        # Compact table view for locker
        locker_df = df[df['id'].isin(st.session_state.locker)].copy()
        
        # apply sidebar filters
        if hide_redundant and st.session_state.get('current_usage'):
            locker_df = locker_df[locker_df['id'].map(lambda x: st.session_state['current_usage'].get(x,0) == 0)]
        if role_filter:
            locker_df = locker_df[locker_df['role_label'].isin(role_filter)]
        
        if not locker_df.empty:
            locker_df.insert(0, 'Remove', False)
            
            # Icons for ImageColumn
            def get_icon_path(w_id):
                # Absolute path is often needed for ImageColumn
                p = os.path.abspath(f"loadout_lab_data/icons/{w_id}.png")
                return p if os.path.exists(p) else None

            locker_df['Icon'] = locker_df['id'].apply(get_icon_path)
            
            display_df = locker_df[['Remove', 'Icon', 'id', 'pretty_name', 'class', 'hit', 'rpm', 'rec', 'mag', 'score']].copy()
              # show heatmap of scores for quick visual scan if matplotlib is available
              try:
                  import matplotlib  # noqa: F401
                  heat_df = display_df.drop(columns=['Remove','Icon']).copy()
                  heat_df.columns = ['id','pretty_name','class','hit','rpm','rec','mag','score']
                  st.dataframe(heat_df.style.background_gradient(subset=['score'], cmap='viridis'), width='stretch', hide_index=True)
              except ImportError:
                  pass
            display_df['Score'] = display_df['Score'].round(3)
            display_df['Damage'] = (display_df['Damage'] * 100).astype(int)
            display_df['Recoil'] = display_df['Recoil'].round(3)
            display_df['Mag Size'] = display_df['Mag Size'].astype(int)
            display_df['RPM'] = display_df['RPM'].astype(int)
            
            edited_df = st.data_editor(
                display_df,
                hide_index=True,
                width='stretch',
                disabled=['Icon', 'Name', 'Class', 'Damage', 'RPM', 'Recoil', 'Mag Size', 'Score'],
                column_config={
                    "ID": None,
                    "Icon": st.column_config.ImageColumn("Icon", help="Weapon preview", width="small"),
                    "Remove": st.column_config.CheckboxColumn("❌", help="Mark to remove", default=False),
                },
                key="locker_bulk_editor"
            )
            
            # Confirm removal in one action (avoids rerun on each checkbox click)
            if st.button("🗑️ Remove selected weapons"):
                to_remove = edited_df[edited_df['Remove'] == True]['ID'].tolist()
                if to_remove:
                    for w_id in to_remove:
                        if w_id in st.session_state.locker:
                            st.session_state.locker.remove(w_id)
                    save_l()
                    st.success(f"Removed {len(to_remove)} weapons!")
                    st.rerun()
                else:
                    st.info("Mark weapons in the list first (❌ checkbox), then remove them.")
        else:
            # Fallback for unknown IDs in locker
            for w_id in list(st.session_state.locker):
                st.write(f"Unknown weapon: {w_id}")
                if st.button("Remove", key=f"rm_unk_{w_id}"):
                    st.session_state.locker.remove(w_id)
                    save_l()
                    st.rerun()

with t1:
    sq = st.text_input("Search weapon (e.g. osw, fn2000, honey)...").lower().strip()
    
    # Filter hits by query, or show all when empty
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
    
    if True:
        # Filter out melee / knife / axe / tomahawk by class, name and id
        melee_pat = 'knife|melee|axe|tomahawk'
        hits = hits[~hits['class'].str.lower().str.contains(melee_pat, na=False)]
        hits = hits[~hits['pretty_name'].str.lower().str.contains(melee_pat, na=False)]
        hits = hits[~hits['id'].str.lower().str.contains(melee_pat, na=False)]
        # Drop duplicate display names
        hits = hits.drop_duplicates(subset=['pretty_name'])
        st.write(f"{len(hits)} matches")
        result_limit = st.select_slider(
            "Rendered result limit",
            options=[15, 30, 50, 100],
            key="search_result_limit",
            help="Limits rendered rows to keep the UI fast on large result sets."
        )
        if len(hits) > result_limit:
            st.caption(f"Performance mode: showing top {result_limit} of {len(hits)} matches.")
        
        # Prepare table for search results
        if not hits.empty:
            # Compute global rank
            df['global_rank'] = df['score'].rank(ascending=False, method='min')
            
            # Compute class rank
            df['class_rank'] = df.groupby('class')['score'].rank(ascending=False, method='min')
            
            # Update hits with rank columns
            hits = df.loc[hits.index]
            render_hits = hits.head(result_limit)
            
            # Show top-N detailed rows with add/remove buttons
            for _, r in render_hits.iterrows():
                c_img, c_txt, c_btn = st.columns([1, 4, 1])
                img_path = f"loadout_lab_data/icons/{r['id']}.png"
                img = load_icon_image(img_path)
                if img is not None:
                    c_img.image(img, width=80)
                m = "🐗 " if r['mutant_killer'] else ""
                c_txt.write(f"{m}**{r['pretty_name']}** ({r['ammo_display']}) - *{r['class']}*")
                if r['id'] in st.session_state.locker:
                    if c_btn.button("Remove", key=f"main_rm_{r['id']}"):
                        st.session_state.locker.remove(r['id'])
                        save_l()
                        st.rerun()
                else:
                    if c_btn.button("Add", key=f"main_ad_{r['id']}"):
                        st.session_state.locker.append(r['id'])
                        save_l()
                        st.rerun()
            
            st.divider()
            st.subheader("📊 Detailed stats for search results")
            
            # Format dataframe for display
            display_df = render_hits[['pretty_name', 'class', 'global_rank', 'class_rank', 'hit', 'rpm', 'rec', 'mag', 'score']].copy()
            display_df.columns = ['Name', 'Class', 'Global Rank', 'Class Rank', 'Damage', 'RPM', 'Recoil', 'Mag Size', 'Score']
            
            # Formatting
            display_df['Global Rank'] = display_df['Global Rank'].astype(int)
            display_df['Class Rank'] = display_df['Class Rank'].astype(int)
            display_df['Score'] = display_df['Score'].round(3)
            # Damage as raw-style value (e.g. 0.53 -> 53)
            display_df['Damage'] = (display_df['Damage'] * 100).astype(int)
            display_df['Recoil'] = display_df['Recoil'].round(3)
            display_df['Mag Size'] = display_df['Mag Size'].astype(int)
            display_df['RPM'] = display_df['RPM'].astype(int)
            
            st.dataframe(display_df.sort_values('Score', ascending=False), width='stretch', hide_index=True)

    save_ui_prefs()

with t2:
    if len(st.session_state.locker) < 3:
        st.warning("Add at least 3 weapons to generate sets.")
    else:
        st.caption("Scoring: unified caliber-adjusted weapon score (same for Balanced and Maxxed)")
        # Diagnostics: role distribution in current locker
        locker_role_df = df[df['id'].isin(st.session_state.locker)].copy()
        role_counts_diag = locker_role_df['role_label'].value_counts()
        max_non_redundant_sets = 0
        if {'Sidearm', 'Power', 'Workhorse'}.issubset(role_counts_diag.index):
            max_non_redundant_sets = int(min(role_counts_diag['Sidearm'], role_counts_diag['Power'], role_counts_diag['Workhorse']))
        st.info(
            f"Roles in locker – Sidearm: {role_counts_diag.get('Sidearm',0)}, "
            f"Power: {role_counts_diag.get('Power',0)}, Workhorse: {role_counts_diag.get('Workhorse',0)} | "
            f"Theoretical unique sets (without reuse): {max_non_redundant_sets}"
        )

        strat = st.radio("Assignment mode:", ["Balanced", "Maxxed"], horizontal=True, key="strategy_mode")
        show_raw_stats_cards = st.checkbox(
            "Show raw stats inspector",
            key="show_raw_stats_cards",
            help="Shows raw weapon stats and score components directly in each set card."
        )
        if strat == "Maxxed":
            st.caption("Maxxed label: P1 strict unique draft, then P2 (Light→Power only with MP/Shotgun Workhorse), then redundant phase R with uniform sampling.")
        else:
            st.caption("Balanced label: same P1/P2/R draft model, but set fitness targets balanced totals.")
        res_sets = calculate_all_sets(st.session_state.locker, strat)
        # cache usage counts for filter and scoring purposes
        usage = {}
        for s_entry in res_sets:
            for w in s_entry['weapons']:
                if w:
                    usage[w['id']] = usage.get(w['id'],0) + 1
        st.session_state['current_usage'] = usage

        # Helper for set classification (color badges) and distribution
        def classify_set(active_w, redundant_count):
            if redundant_count == 0:
                return "🟩", "Clean"
            if redundant_count == 1:
                return "🟧", "+1 Redundant"
            return "🟥", "Multi-Redundant"

        # provide a quick export of the generated sets
        if st.button("📋 Copy sets"):
            lines = []
            for idx, s_entry in enumerate(res_sets, start=1):
                weapons = [w['real_name'] for w in s_entry['weapons'] if w]
                lines.append(f"Set {idx}: " + ", ".join(weapons))
            st.text_area("Generated loadout text", value="\n".join(lines), height=200)

        # Precompute set-type distribution (depends on display order)
        type_counts = {
            "Green: Flawless (Standard)": 0,
            "Green: Flawless (Heavy Hybrid)": 0,
            "Green: Flawless (Light Hybrid)": 0,
            "Blue: Single Deficit (Standard)": 0,
            "Blue: Single Deficit (Heavy Hybrid)": 0,
            "Blue: Single Deficit (Light Hybrid)": 0,
            "Orange: Double Deficit (Standard)": 0,
            "Orange: Double Deficit (Heavy Hybrid)": 0,
            "Orange: Double Deficit (Light Hybrid)": 0
        }
        score_rows = []
        for s_entry in res_sets:
            lbl = s_entry.get('tier_name', "Orange: Double Deficit (Standard)")
            if lbl in type_counts:
                type_counts[lbl] += 1
            avg_score = s_entry.get('avg_score', 0.0)
            score_rows.append({"Score": avg_score, "Label": lbl})

        st.header(f"⚖️ {len(res_sets)} generated {strat} loadouts")
        
        # --- STATS ---
        with st.expander("📊 Locker statistics & distribution"):
            st.write("Distribution of roles and ammo types in your locker:")
            
            # Prepare data for plots
            stats_df = df[df['id'].isin(st.session_state.locker)].copy()
            stats_df['role_label'] = stats_df.apply(get_role, axis=1)
            
            # Plot 1: weapons per role
            role_counts = stats_df['role_label'].value_counts()
            # Plot 2: top 10 ammo types
            ammo_counts = stats_df['ammo_display'].value_counts().head(10)

            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.subheader("Weapons per role")
                st.bar_chart(role_counts)
            with s_col2:
                st.subheader("Most common calibers (Top 10)")
                st.bar_chart(ammo_counts)

            st.subheader("Set distribution by Tier color")
            dist_df = pd.DataFrame([
                {"Category": k, "Count": v} for k, v in type_counts.items()
            ])
            order = list(type_counts.keys())
            
            # Map 9 categories to their respective colors (3 Greens, 3 Blues, 3 Oranges)
            colors = [
                "#2ecc71", "#2ecc71", "#2ecc71",  # Greens
                "#3498db", "#3498db", "#3498db",  # Blues
                "#e67e22", "#e67e22", "#e67e22"   # Oranges
            ]
            
            chart = (
                alt.Chart(dist_df)
                .mark_bar()
                .encode(
                    x=alt.X("Category", sort=order),
                    y=alt.Y("Count"),
                    color=alt.Color("Category", scale=alt.Scale(domain=order, range=colors), legend=None)
                )
                .properties(width="container")
            )
            st.altair_chart(chart)

            if score_rows:
                st.subheader("Set score distribution")
                score_df = pd.DataFrame(score_rows)
                score_chart = (
                    alt.Chart(score_df)
                    .mark_bar(opacity=0.8)
                    .encode(
                        x=alt.X("Score", bin=alt.Bin(maxbins=20)),
                        y=alt.Y("count()", title="Count"),
                        color=alt.Color("Label", scale=alt.Scale(domain=order, range=colors))
                    )
                    .properties(width="container")
                )
                st.altair_chart(score_chart)
        
        # Random set roll
        if res_sets:
            if st.button("🎲 Roll random loadout"):
                import random
                # Store set and display index (+1)
                idx = random.randrange(len(res_sets))
                st.session_state.random_set = res_sets[idx]
                st.session_state.random_set_num = idx + 1
            
            if 'random_set' in st.session_state:
                st.info(f"🎯 Your rolled loadout (Set #{st.session_state.random_set_num}):")
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

        # Set sorting options
        sort_mode = st.radio("Set sorting:", ["By score", "By build order"], horizontal=True, key="sort_mode_sets")

        # Search input for filtering sets
        set_search = st.text_input("🔎 Search sets (e.g. spas12)", key="set_search_query")

        # Apply sorting
        if sort_mode == "By score":
            def score_sort_key(s):
                active = [w for w in s['weapons'] if w is not None]
                avg_score = sum(w['score'] for w in active) / len(active) if active else 0
                return (s.get('tier_val', 50), -avg_score)
            res_sets = sorted(res_sets, key=score_sort_key)
        else:
            res_sets = sorted(res_sets, key=lambda s: s.get('tier_val', 50))

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
            st.caption(f"Filtered sets: {len(res_sets)}")

        # Set display
        collapse_all = st.button("Collapse all")
        seen_ids = set()
        for idx, s_entry in enumerate(res_sets):
            s = s_entry['weapons']
            phase = s_entry.get('phase', "")
            active_w = [w for w in s if w is not None]
            if not active_w:
                continue
            avg = s_entry.get('avg_score', 0.0)
            
            # Tier information from drafting
            tier_val_raw = s_entry.get('tier_val', 50)
            badge = s_entry.get('badge', "🟥")
            tier_name = s_entry.get('tier_name', "Red: Multiple Redundancies")
            
            tier_val = tier_val_raw

            set_has_redundant = any(w['id'] in seen_ids for w in active_w)
            title_suffix = " (🔄 Redundant)" if set_has_redundant else ""
            phase_label = f" {badge}" if badge else ""

            with st.expander(
                f"{phase_label} SET {idx+1}{title_suffix} (Ø-Rating: {avg:.2f})",
                expanded=False
            ):
                cols = st.columns(3)
                labels = ["Sidearm", "Primary (Power)", "Secondary (Workhorse)"]
                set_order = [2, 0, 1]
                st.caption(f"Badge: {badge} ({tier_name}) | Phase: {phase or 'n/a'} | Redundant: {set_has_redundant}")
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
                        if show_raw_stats_cards:
                            with st.expander("📊 Raw stats", expanded=False):
                                hit_raw = float(w.get('hit', 0) or 0)
                                rpm_raw = int(float(w.get('rpm', 0) or 0))
                                rec_raw = float(w.get('rec', 0) or 0)
                                rec_inc = float(w.get('rec_inc', 0.1) or 0.1)
                                rec_hor = float(w.get('rec_hor', 0.5) or 0.5)
                                mag_raw = int(float(w.get('mag', 0) or 0))
                                handling_factor = float(w.get('handling', 1.0) or 1.0)
                                acc_disp = float(w.get('acc', 0.5) or 0.5)

                                # UI Mapping Calculations (Anomaly Style)
                                ui_damage = int(hit_raw * 100)
                                ui_accuracy = max(1, min(100, int(100 - (acc_disp * 100))))
                                ui_handling = max(1, min(100, int(100 - (handling_factor * 20))))
                                # Recoil is a complex mix in the UI; using a weighted mapping approximation
                                ui_recoil = max(1, min(100, int(100 - ((rec_raw + rec_inc * 1.5 + rec_hor * 0.5) * 12))))

                                cal_weight = get_caliber_weight(w.get('ammo', ''))
                                recoil_rating = float(w.get('recoil_rating', 0) or 0)
                                
                                st.caption(f"**Estimated In-game UI Bars:**")
                                cols_ui = st.columns(4)
                                cols_ui[0].metric("DMG", f"{ui_damage}%")
                                cols_ui[1].metric("ACC", f"{ui_accuracy}%")
                                cols_ui[2].metric("HND", f"{ui_handling}%")
                                cols_ui[3].metric("REC", f"{ui_recoil}%")

                                st.divider()
                                st.caption(
                                    f"Scoring inputs (LTX): DMG: {ui_damage} | RPM: {rpm_raw} | Mag: {mag_raw} | rec: {rec_raw:.3f} | Caliber weight: {cal_weight:.2f}"
                                )
                                st.caption(
                                    f"Raw: {float(w.get('raw_score', 0)):.3f} | Cal-Adj: {float(w.get('raw_adjusted', 0)):.3f} | Unified score: {float(w.get('final_score', 0)):.3f}"
                                )
                                st.caption(f"Source: ltx exported values | Recoil rating percentile: {recoil_rating:.1f}")
                    seen_ids.add(w['id'])

    save_ui_prefs()
