with open('scraper.py', 'r') as f:
    t = f.read()
import re
new_code = """        for f in files:
            if f.endswith(".xml"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as xf:
                        text = xf.read()
                except:
                    continue
                import re
                pattern = r'<string\\s+id="([^"]+)">\\s*<text>(.*?)</text>'
                matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
                for m in matches:
                    s_id = m.group(1).lower()
                    s_text = m.group(2).strip()
                    if s_id and s_text:
                        translations[s_id] = s_text

"""
t = re.sub(r'        for f in files:\n            if f\.endswith\("\.xml"\):\n                try:\n                    tree = ET\.parse\(os\.path\.join\(root, f\)\)\n                    for string in tree\.findall\("\.//string"\):\n                        s_id = string\.get\(\'id\'\)\n                        text_elem = string\.find\(\'text\'\)\n                        if s_id and text_elem is not None:\n                            translations\[s_id\.lower\(\)\] = text_elem\.text\n                except: continue\n\n', new_code, t)

# Fix up
t = t.replace("r'_cw', r'_up'", "r'_cw', r'_up_', r'_up$', r'_kit'")

# Re-implement the sorting logic for ltx scanning
t = t.replace('        for f in files:\n            if f.endswith(".ltx"):\n', '        # REMOVE ME')

with open('scraper.py', 'w') as f:
    f.write(t)
