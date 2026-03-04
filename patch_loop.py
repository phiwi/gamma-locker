import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The loop exits too early because it only checks Standard sets or Hybrid MP sets. We need it to iterate and build loadouts out of the remaining dregs even if they don't mathematically fit perfectly into Heavy/Light/MP roles. E.g., if there are 13 Workhorses left, it should just build Workhorse/Workhorse/Workhorse if it has to, to hit 100% coverage!

patch_loop = '''        # 3. Orange Tier / Absolute Failsafe:
        # If no standard or hybrid set fits because we just have 13 snipers left, we just jam them into a set.
        if not candidate_triples:
            unused = [w for w in all_w if w['id'] in unused_ids]
            if unused:
                u1 = unused[0]
                u2 = unused[1] if len(unused) > 1 else random.choice(all_w)
                u3 = unused[2] if len(unused) > 2 else random.choice(all_w)
                candidate_triples.append((u1, u2, u3))'''

content = re.sub(r'        # 2\. Hybrid sets \(Heavy/Light \+ MP/Shotgun\).*?if any\(w\[\'id\'\] in unused_ids for w in \(p, wh, s\)\):\n                candidate_triples\.append\(\(p, wh, s\)\)', 
    r'\g<0>\n\n' + patch_loop, 
    content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Loop exit failsafe patched.")
