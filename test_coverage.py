import json
import pandas as pd
from app import calculate_all_sets, df, load_locker

locker_ids = load_locker()
print(f"Total in locker: {len(locker_ids)}")

res = calculate_all_sets(locker_ids, "Maxxed")
print(f"Total loadouts generated: {len(res)}")

used_weapons_in_draft = set()
redundant_counts = 0

for s in res:
    for w in s['weapons']:
        w_id = w['id']
        used_weapons_in_draft.add(w_id)

print(f"Unique weapons drafted: {len(used_weapons_in_draft)} out of {len(locker_ids)}")

not_drafted = set(locker_ids) - used_weapons_in_draft
if not_drafted:
    print("WARNING! These weapons were NOT drafted anywhere:")
    for w_id in not_drafted:
        row = df[df['id'] == w_id]
        if not row.empty:
            print(f"  - {w_id} ({row['role_label'].iloc[0]})")
        else:
            print(f"  - {w_id} (Unknown role)")
else:
    print("SUCCESS: 100% of the locker weapons were used at least once!")

