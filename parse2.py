import sys, re
if len(sys.argv) < 2: sys.exit(0)
p = sys.argv[1]
with open(p, 'rb') as f:
    data = f.read().decode('latin-1', errors='ignore')
    # Find anything with rack or furniture
    for m in re.finditer(r'(.{0,40})(rack|furniture|stash|box)(.{0,40})', data, re.IGNORECASE):
        print(m.group(0).replace('\n', ''))
