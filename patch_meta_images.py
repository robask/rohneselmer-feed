"""
Fikser Meta feed bildene tilbake til original:
- Hovedbilde: <image><url>...</url></image>
- Ekstrabilder: <image><url>...</url></image>
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

old = '''        if v["main_image"]:
            lines.append(f'    <image_link>{esc(v["main_image"])}</image_link>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <additional_image_link>{esc(img)}</additional_image_link>')'''

new = '''        if v["main_image"]:
            lines.append(f'    <image><url>{esc(v["main_image"])}</url></image>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <image><url>{esc(img)}</url></image>')'''

if old in content:
    content = content.replace(old, new)
    print("✅ Fikset!")
else:
    print("⚠️  Ikke funnet")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
