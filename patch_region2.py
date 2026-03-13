"""
Flytter region inn i address-blokken
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

old = """        lines.append(f'    <address format="simple">')
        lines.append(f'      <component name="addr1">Bergerveien 12</component>')
        lines.append(f'      <component name="city">Billingstad</component>')
        lines.append(f'      <component name="postal_code">1396</component>')
        lines.append(f'      <component name="country">Norway</component>')
        lines.append(f'    </address>')
        lines.append(f'    <region>Akershus</region>')"""

new = """        lines.append(f'    <address format="simple">')
        lines.append(f'      <component name="addr1">Bergerveien 12</component>')
        lines.append(f'      <component name="city">Billingstad</component>')
        lines.append(f'      <component name="region">Akershus</component>')
        lines.append(f'      <component name="postal_code">1396</component>')
        lines.append(f'      <component name="country">Norway</component>')
        lines.append(f'    </address>')"""

if old in content:
    content = content.replace(old, new)
    print("✅ Flyttet region inn i address-blokken!")
else:
    print("⚠️  Fant ikke address-blokken")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
