"""
Erstatter build_meta_feed med korrekt Meta Automotive Inventory Ads format.
Bruker <listings>/<listing> struktur som Meta krever.
"""

import re

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

new_meta_function = '''def build_meta_feed(vehicles):
    """Generate Meta Automotive Inventory Ads feed in correct <listings> format."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<listings>')

    def esc(val):
        if not val:
            return ""
        return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for v in vehicles:
        if not v:
            continue
        lines.append('  <listing>')
        lines.append(f'    <vehicle_id>{esc(v["id"])}</vehicle_id>')
        lines.append(f'    <title>{esc(v["title"])}</title>')
        lines.append(f'    <description>{esc(v["description"] or v["title"])}</description>')
        lines.append(f'    <url>{esc(v["url"])}</url>')

        if v["main_image"]:
            lines.append(f'    <image><url>{esc(v["main_image"])}</url></image>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <image><url>{esc(img)}</url></image>')

        lines.append(f'    <make>{esc(v["brand"])}</make>')
        lines.append(f'    <model>{esc(v["model"])}</model>')
        lines.append(f'    <year>{esc(v["year"])}</year>')
        lines.append(f'    <state_of_vehicle>USED</state_of_vehicle>')

        price_num = v["price"].replace(" NOK", "").strip() if v["price"] else "0"
        lines.append(f'    <price>{esc(price_num)} NOK</price>')

        if v["mileage"]:
            lines.append(f'    <mileage>')
            lines.append(f'      <unit>KM</unit>')
            lines.append(f'      <value>{esc(v["mileage"])}</value>')
            lines.append(f'    </mileage>')

        if v["body_type"]:
            lines.append(f'    <body_style>{esc(v["body_type"])}</body_style>')
        if v["transmission"]:
            lines.append(f'    <transmission>{esc(v["transmission"])}</transmission>')
        if v["fuel_type"]:
            lines.append(f'    <fuel_type>{esc(v["fuel_type"])}</fuel_type>')
        if v["color"]:
            lines.append(f'    <exterior_color>{esc(v["color"])}</exterior_color>')
        if v["drive_type"]:
            lines.append(f'    <drivetrain>{esc(v["drive_type"])}</drivetrain>')
        if v["vin"]:
            lines.append(f'    <vin>{esc(v["vin"])}</vin>')

        lines.append('  </listing>')

    lines.append('</listings>')
    return chr(10).join(lines)

'''

# Replace existing build_meta_feed function
pattern = r'def build_meta_feed\(vehicles\):.*?(?=\ndef |\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_meta_function, content, flags=re.DOTALL)
    print("✅ Erstattet build_meta_feed med korrekt Meta-format!")
else:
    print("⚠️  Fant ikke build_meta_feed — sjekk scriptet")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
