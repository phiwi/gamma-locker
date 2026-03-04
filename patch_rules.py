import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure that ALL weapons are given a role. 
# Right now, some are falling through the cracks and getting "Unknown role" or being marked as ineligible Workhorses because of strict ammo checks.
patch = '''    # Fallback all others into Workhorse so NOTHING is undraftable
    # Workhorse: Assault, SMG, Shotguns, plus literally anything else not caught above
    return "Workhorse"'''
content = re.sub(r'    # Workhorse: Assault, SMG, Shotguns.*?    return "Workhorse"', patch, content, flags=re.DOTALL)

# In the calculate_all_sets method, we must be absolutely sure that EVERY weapon is categorized.
# The previous valid_workhorse checks accidentally EXCLUDED Heavy snipers from being workhorses entirely 
# when they should just be Power, but what if all Power slots are full?

patch_workhorse = '''    def is_valid_workhorse(w):
        # In the new logic, basically anything that isn't actively drafted as a Power or Sidearm MUST be allowed as a Workhorse
        # Otherwise the inventory stalls.
        return True'''
content = re.sub(r'    def is_valid_workhorse\(w\):.*?        return False', patch_workhorse, content, flags=re.DOTALL)


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Rules patched for 100% inclusion.")
