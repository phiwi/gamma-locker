with open('scraper.py', 'r') as f: t = f.read()

# remove hardcode
t = t.replace("""        if sec == 'wpn_fn2000_nimble':
            real_name = 'FN F2000 "Competitor"'
            gx, gy = 40.0, 36.0
            
        final.append({""", "        final.append({")

with open('scraper.py', 'w') as f: f.write(t)
