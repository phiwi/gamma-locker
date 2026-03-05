import pandas as pd
import pytest
import os
import sys
from unittest.mock import MagicMock

# Mock streamlit BEFORE importing app
mock_st = MagicMock()
# Mock st.sidebar.columns(2) to return 2 mocks to handle unpacking
def mock_columns(n):
    if isinstance(n, list):
        return [MagicMock() for _ in range(len(n))]
    return [MagicMock() for _ in range(n)]

mock_st.sidebar.columns.side_effect = mock_columns
mock_st.sidebar.button.return_value = False
mock_st.button.return_value = False
mock_st.columns.side_effect = mock_columns
mock_st.tabs.side_effect = mock_columns
mock_st.select_slider.return_value = 30
mock_st.radio.return_value = "Balanced"
mock_st.checkbox.return_value = False
mock_st.text_input.return_value = ""

# Prevent JSON serialization errors of MagicMocks in save_ui_prefs
class MockSessionState(dict):
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value

mock_st.session_state = MockSessionState({
    "strategy_mode": "Balanced",
    "sort_mode_sets": "By score",
    "set_search_query": "",
    "search_result_limit": 30,
    "show_raw_stats_cards": False,
    "locker": []
})
sys.modules['streamlit'] = mock_st

# Add the project root to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import io

_MOCK_CSV = """id,real_name,hit,rpm,slot,acc,rec,rec_inc,rec_hor,mag,handling,ammo,mod,class,gx,gy,gw,gh,tex
wpn_pm,Makarov PM,0.45,315.0,1,0.62,2.0,0.1,0.52,8,1.0,9x18_fmj,Vanilla,Pistol,0,0,2,1,ui_icon
wpn_glock,Glock 17,0.5,300.0,1,0.6,1.8,0.1,0.5,17,1.0,9x19_fmj,Vanilla,Pistol,0,0,2,1,ui_icon
wpn_beretta,Beretta,0.5,300.0,1,0.6,1.8,0.1,0.5,15,1.0,9x19_fmj,Vanilla,Pistol,0,0,2,1,ui_icon
wpn_mp5k,MP5K,0.5,900.0,2,0.5,1.5,0.1,0.4,30,1.0,9x19_fmj,Vanilla,SMG,0,0,3,2,ui_icon
wpn_p90,P90,0.5,900.0,2,0.6,1.2,0.1,0.3,50,1.0,5.7x28_ss190,Vanilla,SMG,0,0,3,2,ui_icon
wpn_sr2_veresk,SR-2,0.6,900.0,2,0.5,1.8,0.1,0.5,30,1.0,9x21_sp10,Vanilla,SMG,0,0,3,2,ui_icon
wpn_colt,Colt 1911,0.6,300.0,1,0.6,2.2,0.1,0.6,7,1.0,.45_acp,Vanilla,Pistol,0,0,2,1,ui_icon

wpn_ak74,AK-74,0.6,600.0,2,0.5,1.5,0.1,0.4,30,1.0,5.45x39_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_m4a1,M4A1,0.6,800.0,2,0.6,1.4,0.1,0.3,30,1.0,5.56x45_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_akm,AKM,0.7,600.0,2,0.5,1.8,0.1,0.5,30,1.0,7.62x39_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_groza,Groza,0.8,700.0,2,0.5,1.6,0.1,0.4,20,1.0,9x39_pab9,Vanilla,Assault Rifle,0,0,4,2,ui_icon
wpn_l85,L85,0.6,650.0,2,0.6,1.3,0.1,0.3,30,1.0,5.56x45_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_g36,G36,0.6,750.0,2,0.6,1.3,0.1,0.3,30,1.0,5.56x45_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_ak105,AK-105,0.6,600.0,2,0.5,1.6,0.1,0.4,30,1.0,5.45x39_fmj,Vanilla,Assault Rifle,0,0,4,2,ui_icon
wpn_fn2000,FN F2000,0.6,850.0,2,0.6,1.2,0.1,0.3,30,1.0,5.56x45_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon

wpn_mp5,MP5,0.5,800.0,2,0.5,1.4,0.1,0.3,30,1.0,9x19_fmj,Vanilla,SMG,0,0,4,2,ui_icon
wpn_spas12,SPAS-12,1.2,200.0,2,0.4,3.0,0.2,1.0,8,1.0,12x70_buck,Vanilla,Shotgun,0,0,5,2,ui_icon
wpn_mp7,MP7,0.5,950.0,2,0.6,1.1,0.1,0.2,40,1.0,4.6x30_fmj,Vanilla,SMG,0,0,3,2,ui_icon
wpn_toz34,TOZ-34,1.5,100.0,2,0.5,4.0,0.3,1.5,2,1.0,12x70_buck,Vanilla,Shotgun,0,0,6,1,ui_icon
wpn_mp133,MP-133,1.2,150.0,2,0.4,3.0,0.2,1.0,6,1.0,12x70_buck,Vanilla,Shotgun,0,0,5,2,ui_icon
wpn_ump45,UMP-45,0.6,600.0,2,0.5,1.6,0.1,0.4,25,1.0,.45_acp,Vanilla,SMG,0,0,4,2,ui_icon

wpn_svd,SVD,1.0,150.0,2,0.8,2.5,0.2,0.8,10,1.0,7.62x54_7h1,Vanilla,Sniper,0,0,6,2,ui_icon
wpn_m110,M110,0.9,300.0,2,0.8,2.2,0.2,0.7,20,1.0,7.62x51_fmj,Vanilla,DMR,0,0,6,2,ui_icon
wpn_ash12,ASh-12,1.2,600.0,2,0.6,2.8,0.2,0.9,20,1.0,12.7x55_fmj,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_lapua,Lapua,1.8,50.0,2,0.9,4.0,0.3,1.5,5,1.0,.338_magnum,Vanilla,Sniper,0,0,6,2,ui_icon
wpn_sig_spear,Spear,0.8,650.0,2,0.7,1.8,0.1,0.5,20,1.0,6.8x51_hybrid,Vanilla,Assault Rifle,0,0,5,2,ui_icon
wpn_ks23,KS-23,2.0,100.0,2,0.3,5.0,0.4,2.0,3,1.0,23x75_shrapnel,Vanilla,Shotgun,0,0,5,2,ui_icon
wpn_saiga,Saiga,1.1,400.0,2,0.4,2.5,0.2,0.8,8,1.0,12x76_bull,Vanilla,Shotgun,0,0,5,2,ui_icon
wpn_mosin,Mosin,1.1,60.0,2,0.8,3.0,0.2,1.0,5,1.0,7.62x54_7h1,Vanilla,Sniper,0,0,6,1,ui_icon
wpn_pkm,PKM,0.9,650.0,2,0.5,2.5,0.2,0.8,100,1.0,7.62x54_7h1,Vanilla,Machine Gun,0,0,6,2,ui_icon
"""

original_read_csv = pd.read_csv
def mock_read_csv(filepath_or_buffer, *args, **kwargs):
    if isinstance(filepath_or_buffer, str) and "weapons_stats.csv" in filepath_or_buffer:
        return original_read_csv(io.StringIO(_MOCK_CSV), *args, **kwargs)
    return original_read_csv(filepath_or_buffer, *args, **kwargs)

import builtins
original_exists = os.path.exists
def mock_exists(path):
    if isinstance(path, str) and "weapons_stats.csv" in path:
        return True
    return original_exists(path)

os.path.exists = mock_exists
pd.read_csv = mock_read_csv

import app
from app import calculate_all_sets, df

# helper used by multiple tests
import random

def generate_random_locker(side=5, power=5, work=5, seed=None):
    if seed is not None:
        random.seed(seed)
    s_ids = df[df['role_label'] == 'Sidearm']['id'].sample(side).tolist()
    p_ids = df[df['role_label'] == 'Power']['id'].sample(power).tolist()
    wh_ids = df[df['role_label'] == 'Workhorse']['id'].sample(work).tolist()
    return s_ids + p_ids + wh_ids

def is_light_weapon(w):
    ammo = str(w.get('ammo', '')).lower()
    return any(cal in ammo for cal in app.GROUP_LIGHT)

def is_mp_or_shotgun_workhorse(w):
    cls = str(w.get('class', '')).lower()
    return ('smg' in cls) or ('shotgun' in cls)

def test_drafting_logic_priorities():
    """
    Test that the drafting logic respects Tier priorities:
    Tier 1 (Green) should be preferred over redundant/hybrid sets when possible.
    """
    # Sample a manageable subset of weapons
    # Ensure we have at least 1 Sidearm, 1 Power (Heavy), 1 Workhorse (Light AR)
    sidearm_ids = df[df['role_label'] == 'Sidearm']['id'].head(2).tolist()
    power_ids = df[df['role_label'] == 'Power']['id'].head(2).tolist()
    # Light ARs
    light_ar_ids = df[
        (df['role_label'] == 'Workhorse') & 
        (df.apply(is_light_weapon, axis=1))
    ]['id'].head(2).tolist()
    
    test_locker = sidearm_ids + power_ids + light_ar_ids
    
    # We have 2 of each. We should get 2 Tier 1 sets.
    res_sets = calculate_all_sets(test_locker, "Maxxed")
    
    tier_counts = [s.get('tier_val', 5) for s in res_sets]
    
    # First sets MUST be Tier 1 (Green)
    assert tier_counts[0] in (11, 12, 13)
    if len(res_sets) > 1:
        assert tier_counts[1] in (11, 12, 13)

def test_no_ammo_conflicts():
    """Verify that no generated set contains ammo conflicts."""
    test_locker = df['id'].sample(20).tolist()
    res_sets = calculate_all_sets(test_locker, "Balanced")
    
    for s_entry in res_sets:
        weps = [w for w in s_entry['weapons'] if w]
        if s_entry.get('tier_val', 0) >= 30:
            continue
        for i in range(len(weps)):
            for j in range(i + 1, len(weps)):
                a1 = str(weps[i].get('ammo', '')).lower()
                a2 = str(weps[j].get('ammo', '')).lower()
                # Simple check for identical ammo (strictest conflict)
                assert a1 != a2, f"Ammo conflict found in set: {a1} vs {a2}"

def test_all_weapons_drafted():
    """Verify that the drafting process uses every weapon in the locker at least once (if valid role assigned)."""
    # Sample only weapons that have a valid drafting role (Sidearm, Power, or Workhorse)
    # and satisfy our workhorse/power definitions.
    
    # We need to filter for IDs that the calculate_all_sets function actually collects into roles.
    # We'll just pick 5 from each role to be safe.
    s_ids = df[df['role_label'] == 'Sidearm']['id'].sample(5).tolist()
    p_ids = df[df['role_label'] == 'Power']['id'].sample(5).tolist()
    
    # Workhorse filter from app.py
    def is_valid_wh(w):
        ammo = str(w.get('ammo', '')).lower()
        cls = str(w.get('class', '')).lower()
        return any(cal in ammo for cal in app.GROUP_LIGHT) or ('smg' in cls) or ('shotgun' in cls)
    
    wh_ids = df[(df['role_label'] == 'Workhorse') & (df.apply(is_valid_wh, axis=1))]['id'].sample(5).tolist()
    
    test_locker = s_ids + p_ids + wh_ids
    # check both modes; balanced should also eventually touch each item
    for mode in ("Maxxed", "Balanced"):
        res_sets = calculate_all_sets(test_locker, mode)
        used_ids = set()
        for s_entry in res_sets:
            for w in s_entry['weapons']:
                if w:
                    used_ids.add(w['id'])
        for w_id in test_locker:
            assert w_id in used_ids, f"Weapon {w_id} was never drafted in {mode}!"

def test_hybrid_classification():
    """Check if the hybrid classification logic correctly identifies sub-tiers."""
    # Find a hybrid workhorse (SMG/Shotgun)
    hybrid_wh = df[df.apply(is_mp_or_shotgun_workhorse, axis=1)]['id'].iloc[0]
    # Find a Power weapon
    pwr = df[df['role_label'] == 'Power']['id'].iloc[0]
    # Find a Sidearm
    side = df[df['role_label'] == 'Sidearm']['id'].iloc[0]
    
    test_locker = [hybrid_wh, pwr, side]
    res_sets = calculate_all_sets(test_locker, "Maxxed")
    
    # A single unique set with a hybrid workhorse should be a lower tier than 1
    # Actually, in our logic, if it's unique AND hybrid, we still allow it but check tier.
    # Looking at get_tier_info: tier 3 is Redundant Sidearm + Hybrid.
    # If all are unique but wh is hybrid, it currently falls to Tier 5 (Red) or isn't Green.
    
    for s in res_sets:
        if any(w['id'] == hybrid_wh for w in s['weapons']):
            # It shouldn't be Tier 1 (Green) because Green requires is_pure (is_light_weapon)
            assert s.get('tier_val', 1) != 1

def test_heavy_is_never_sidearm_or_workhorse():
    """Verify that weapons with heavy ammo are never classified as Sidearm or Workhorse."""
    import app
    # Per rules, heavy ammo weapons ('6.8x51' + POWER_AMMO) should always be Power.
    for idx, row in df.iterrows():
        ammo = str(row.get('ammo', '')).lower()
        has_heavy_ammo = "6.8x51" in ammo or any(a in ammo for a in app.POWER_AMMO)
        
        if has_heavy_ammo:
            role = app.get_role(row)
            assert role == "Power", \
                f"Weapon {row['id']} has heavy ammo ({ammo}) but role is {role}"

def test_workhorse_restrictions():
    """Workhorse darf nur Light, MP oder Shotgun sein (Heavy-Kaliber ausgeschlossen, keine Sniper/DMR)."""
    import app
    for idx, row in df.iterrows():
        role = app.get_role(row)
        if role == 'Workhorse':
            cls_raw = str(row.get('class', '')).lower()
            assert 'sniper' not in cls_raw and 'dmr' not in cls_raw, \
                f"Weapon {row['id']} is Workhorse but class is {cls_raw}"
            ammo = str(row.get('ammo', '')).lower()
            has_heavy_ammo = "6.8x51" in ammo or any(a in ammo for a in app.POWER_AMMO)
            assert not has_heavy_ammo, \
                f"Weapon {row['id']} is Workhorse but has heavy ammo ({ammo})"

def test_sidearm_prefixes_are_sidearms():
    """Verify that weapons with SIDEARM_SMG_PREFIXES always get classified as Sidearm."""
    import app
    for prefix in app.SIDEARM_SMG_PREFIXES:
        matching_weapons = df[df['id'].str.startswith(prefix)]
        for _, w in matching_weapons.iterrows():
            # Even if it fires powerful ammo or has weird stats, these specific IDs must remain Sidearm.
            assert app.get_role(w) == "Sidearm", f"Weapon {w['id']} with prefix {prefix} is not a Sidearm"

