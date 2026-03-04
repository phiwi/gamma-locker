import re

with open('scraper.py', 'r') as f:
    content = f.read()

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
                try:"""

# Just restore the old format for now but with sorted files
part2 = """print("📂 Scanning weapon data...")
registry = {}

all_files = []
for scan_path in SCAN_PATHS:
    if not scan_path.exists(): continue
    for root, dirs, files in os.walk(scan_path):
        for f in files:
            if f.endswith(".ltx"):
                all_files.append((root, f))
all_files.sort()

# Reconstruct original loops logic
for root, f in tqdm.tqdm(all_files, desc="Parsing LTX files", leave=False):
    scan_path = root
    files = [f]
    root = root

    p_parts = Path(root).parts
    mod_name = "Vanilla"
    if "mods" in p_parts:
        m_idx = p_parts.index("mods")
        if len(p_parts) > m_idx + 1: mod_name = p_parts[m_idx + 1]
        else: continue
    
    for f in files:
        if f.endswith(".ltx"):
            try:"""

content = content.replace("for root, f in tqdm.tqdm(all_files, desc=\"Parsing LTX files\", leave=False):", "for root, f in tqdm.tqdm(all_files, desc=\"Parsing LTX files\", leave=False):")
# Let me just git restore scraper.py !
