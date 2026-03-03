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

import app
from app import calculate_all_sets, df

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
    assert tier_counts[0] == 1
    if len(res_sets) > 1:
        assert tier_counts[1] == 1

def test_no_ammo_conflicts():
    """Verify that no generated set contains ammo conflicts."""
    test_locker = df['id'].sample(20).tolist()
    res_sets = calculate_all_sets(test_locker, "Balanced")
    
    for s_entry in res_sets:
        weps = [w for w in s_entry['weapons'] if w]
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
    res_sets = calculate_all_sets(test_locker, "Maxxed")
    
    used_ids = set()
    for s_entry in res_sets:
        for w in s_entry['weapons']:
            if w:
                used_ids.add(w['id'])
                
    for w_id in test_locker:
        assert w_id in used_ids, f"Weapon {w_id} was never drafted!"

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
