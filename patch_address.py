"""
Legger til address og body_style fallback i build_meta_feed
"""

import re

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Add address and body_style fallback after state_of_vehicle in meta feed
old = "        lines.append(f'    <state_of_vehicle>USED</state_of_vehicle>')"
new = """        lines.append(f'    <state_of_vehicle>USED</state_of_vehicle>')
        lines.append(f'    <address format=\"simple\">')
        lines.append(f'      <component name=\"addr1\">Bergerveien 12</component>')
        lines.append(f'      <component name=\"city\">Billingstad</component>')
        lines.append(f'      <component name=\"postal_code\">1396</component>')
        lines.append(f'      <component name=\"country\">Norway</component>')
        lines.append(f'    </address>')"""

if old in content:
    content = content.replace(old, new)
    print("✅ Lagt til address!")
else:
    print("⚠️  Fant ikke state_of_vehicle-linjen")

# Add body_style fallback
old2 = "        if v[\"body_type\"]:\n            lines.append(f'    <body_style>{esc(v[\"body_type\"])}</body_style>')"
new2 = "        lines.append(f'    <body_style>{esc(v[\"body_type\"]) if v[\"body_type\"] else \"Sedan\"}</body_style>')"

if old2 in content:
    content = content.replace(old2, new2)
    print("✅ Lagt til body_style fallback!")
else:
    print("⚠️  Fant ikke body_style-linjen")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
