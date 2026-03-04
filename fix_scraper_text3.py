with open('scraper.py', 'r') as f: t = f.read()

part1 = """print("📂 Scanning weapon data...")
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
                    with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as l:"""

part2 = """print("📂 Scanning weapon data...")
registry = {}

all_files = []
for scan_path in SCAN_PATHS:
    if not scan_path.exists(): continue
    for root, dirs, files in os.walk(scan_path):
        for f in files:
            if f.endswith(".ltx"):
                all_files.append((root, f))

# Sort to roughly enforce numbered MO2 load order (e.g. 348- overrides 001-)
all_files.sort()

# Reconstruct original loops logic
import tqdm
for root, f in tqdm.tqdm(all_files, desc="Parsing LTX files", leave=False):
    scan_path = root

    p_parts = Path(root).parts
    mod_name = "Vanilla"
    if "mods" in p_parts:
        m_idx = p_parts.index("mods")
        if len(p_parts) > m_idx + 1: mod_name = p_parts[m_idx + 1]
        else: continue
    
    try:
        with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as l:"""

t = t.replace(part1, part2)
with open('scraper.py', 'w') as f: f.write(t)
