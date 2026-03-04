with open('scraper.py', 'r') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if l.strip() == "except: continue" and i > 180 and i < 195:
        # It's at line 187
        lines[i] = "    except: continue\n"
with open('scraper.py', 'w') as f: f.writelines(lines)
