"""
Legger til region og oversetter fuel_type + transmission i build_meta_feed
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Add region after address block
old = "        lines.append(f'    </address>')"
new = """        lines.append(f'    </address>')
        lines.append(f'    <region>Akershus</region>')"""

if old in content:
    content = content.replace(old, new)
    print("✅ Lagt til region!")
else:
    print("⚠️  Fant ikke address-blokken")

# Add fuel_type translation function before build_meta_feed
fuel_translation = '''
def translate_fuel_type(val):
    if not val:
        return "OTHER"
    v = val.strip().lower()
    if v in ("el", "elektrisk", "electric", "ev"):
        return "ELECTRIC"
    if v in ("bensin", "gasoline", "petrol"):
        return "GASOLINE"
    if v in ("diesel", "forbrenningsmotor"):
        return "DIESEL"
    if "plug" in v or "plugin" in v or "plug-in" in v:
        return "PLUGIN_HYBRID"
    if "hybrid" in v:
        return "HYBRID"
    return "OTHER"

def translate_transmission(val):
    if not val:
        return "OTHER"
    v = val.strip().lower()
    if v in ("automat", "automatic", "automatisk"):
        return "AUTOMATIC"
    if v in ("manuell", "manual"):
        return "MANUAL"
    return "OTHER"

'''

if "def translate_fuel_type" not in content:
    content = content.replace("def build_meta_feed(vehicles):", fuel_translation + "def build_meta_feed(vehicles):")
    print("✅ Lagt til oversetterfunksjoner!")
else:
    print("⚠️  Oversetterfunksjoner allerede der")

# Use translation functions in build_meta_feed
old_fuel = "        if v[\"fuel_type\"]:\n            lines.append(f'    <fuel_type>{esc(v[\"fuel_type\"])}</fuel_type>')"
new_fuel = "        lines.append(f'    <fuel_type>{translate_fuel_type(v[\"fuel_type\"])}</fuel_type>')"

if old_fuel in content:
    content = content.replace(old_fuel, new_fuel)
    print("✅ Oversatt fuel_type!")
else:
    print("⚠️  Fant ikke fuel_type-linjen")

old_trans = "        if v[\"transmission\"]:\n            lines.append(f'    <transmission>{esc(v[\"transmission\"])}</transmission>')"
new_trans = "        lines.append(f'    <transmission>{translate_transmission(v[\"transmission\"])}</transmission>')"

if old_trans in content:
    content = content.replace(old_trans, new_trans)
    print("✅ Oversatt transmission!")
else:
    print("⚠️  Fant ikke transmission-linjen")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
