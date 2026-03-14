"""
Fikser Google feed:
1. Oversetter fuel_type til engelsk
2. Fjerner dobbel identifier_exists
3. Legger til vehicle_fulfillment og store_code basert på lokasjon
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Fix 1: Remove duplicate identifier_exists (keep only the first one)
# Find both occurrences and remove the second
first = content.find('field("identifier_exists", "no")')
second = content.find('field("identifier_exists", "no")', first + 1)
if second != -1:
    line_start = content.rfind('\n', 0, second) + 1
    line_end = content.find('\n', second) + 1
    content = content[:line_start] + content[line_end:]
    print("✅ Fjernet dobbel identifier_exists!")
else:
    print("⚠️  Ingen dobbel identifier_exists funnet")

# Fix 2: Add fuel translation function for Google feed before build_feed
google_fuel_func = '''
def translate_fuel_type_google(val):
    """Translate Norwegian fuel type to Google accepted values."""
    if not val:
        return None
    v = val.strip().lower()
    if v in ("el", "elektrisk", "electric"):
        return "Electric"
    if v in ("bensin", "gasoline", "petrol"):
        return "Gasoline"
    if v in ("diesel", "forbrenningsmotor"):
        return "Diesel"
    if "plug" in v or "plugin" in v or "plug-in" in v:
        return "Plug-in Hybrid"
    if "hybrid" in v:
        return "Hybrid"
    return val

def get_store_code(dealer_name):
    """Map dealer name to Google store code."""
    mapping = {
        "Oslo": "rohneselmer-oslo",
        "Lillestrøm": "rohneselmer-lillestrom",
        "Asker og Bærum": "rohneselmer-asker-baerum",
        "Hønefoss": "rohneselmer-honefoss",
        "Lierstranda": "rohneselmer-lierstranda",
    }
    return mapping.get(dealer_name, "rohneselmer-asker-baerum")

'''

if "def translate_fuel_type_google" not in content:
    content = content.replace("def build_feed(vehicles):", google_fuel_func + "def build_feed(vehicles):")
    print("✅ Lagt til translate_fuel_type_google og get_store_code!")
else:
    print("⚠️  Funksjonene finnes allerede")

# Fix 3: Use translation in Google feed and add store_code + vehicle_fulfillment
old_fields = (
    '        field("fuel_type",                 v["fuel_type"])\n'
    '        field("transmission",              v["transmission"])\n'
    '        field("body_style",                v["body_type"])\n'
    '        field("color",                     v["color"])\n'
    '        field("drive_wheel_configuration", v["drive_type"])\n'
    '        field("number_of_doors",           v["doors"])\n'
    '        field("horsepower",                v["horsepower"])\n'
    '        field("engine_size",               v["engine_size"])\n'
    '        field("number_of_seats",           v["seats"])\n'
    '        for img in v["extra_images"][:9]:\n'
    '            field("additional_image_link", img)\n'
    '        field("google_product_category", "916")'
)

new_fields = (
    '        field("fuel_type",                 translate_fuel_type_google(v["fuel_type"]))\n'
    '        field("transmission",              v["transmission"])\n'
    '        field("body_style",                v["body_type"])\n'
    '        field("color",                     v["color"])\n'
    '        field("drive_wheel_configuration", v["drive_type"])\n'
    '        field("number_of_doors",           v["doors"])\n'
    '        field("horsepower",                v["horsepower"])\n'
    '        field("engine_size",               v["engine_size"])\n'
    '        field("number_of_seats",           v["seats"])\n'
    '        field("vehicle_fulfillment",       "in_store")\n'
    '        field("store_code",                get_store_code(v.get("dealer_name", "")))\n'
    '        for img in v["extra_images"][:9]:\n'
    '            field("additional_image_link", img)\n'
    '        field("google_product_category", "916")'
)

if old_fields in content:
    content = content.replace(old_fields, new_fields)
    print("✅ Fikset fuel_type, lagt til vehicle_fulfillment og store_code!")
else:
    print("⚠️  Fant ikke feltene i build_feed")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
