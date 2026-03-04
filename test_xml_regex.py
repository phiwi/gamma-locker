import re
import os

translations = {}
path = '/mnt/c/G.A.M.M.A/MO2/mods/G.A.M.M.A. Weapon Pack/gamedata/configs/text/eng/st_items_weapons.xml'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    text = f.read()

# simple regex for string id
pattern = r'<string\s+id="([^"]+)">\s*<text>(.*?)</text>'
matches = re.findall(pattern, text, re.DOTALL)
for m in matches:
    translations[m[0].lower()] = m[1]
print("Found", len(matches), "strings!")
print("st_wpn_fn2000_nimble:", translations.get('st_wpn_fn2000_nimble'))
