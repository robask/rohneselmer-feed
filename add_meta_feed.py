"""
Run this script once to add Meta Automotive feed support
to the existing rohneselmer_feed_generator.py
"""

import re

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

meta_function = '''
def build_meta_feed(vehicles):
    """Generate Meta Automotive Inventory Ads compatible XML feed."""
    from datetime import datetime as dt
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<feed xmlns="http://www.w3.org/2005/Atom" xmlns:g="http://base.google.com/ns/1.0">')
    lines.append('  <title>Rohne Selmer — Bruktbiler Meta Feed</title>')
    lines.append('  <link rel="self" href="https://robask.github.io/rohneselmer-feed/rohneselmer_feed_meta.xml"/>')
    lines.append('  <updated>' + dt.now().strftime('%Y-%m-%dT%H:%M:%SZ') + '</updated>')

    def esc(val):
        if not val:
            return ""
        return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for v in vehicles:
        if not v:
            continue
        lines.append('  <entry>')

        def field(tag, value):
            if value:
                lines.append(f'    <g:{tag}>{esc(value)}</g:{tag}>')

        field("id",               v["id"])
        field("title",            v["title"])
        field("description",      v["description"] or v["title"])
        field("url",              v["url"])
        field("image_url",        v["main_image"])
        field("make",             v["brand"])
        field("model",            v["model"])
        field("year",             v["year"])
        field("mileage.value",    v["mileage"])
        field("mileage.unit",     "KM" if v["mileage"] else None)
        field("price",            v["price"])
        field("currency",         "NOK")
        field("availability",     "available")
        field("state_of_vehicle", "used")
        field("vin",              v["vin"])
        field("fuel_type",        v["fuel_type"])
        field("transmission",     v["transmission"])
        field("body_style",       v["body_type"])
        field("exterior_color",   v["color"])
        field("drivetrain",       v["drive_type"])

        for img in v["extra_images"][:9]:
            field("image_url",    img)

        lines.append('  </entry>')

    lines.append('</feed>')
    return "\\n".join(lines)

'''

# Insert before the main() function
content = content.replace("def main():", meta_function + "def main():")

# Update main() to also save meta feed
old_save = '''    log.info(f"\\n✅ Feed saved to: {OUTPUT_FILE}")
    log.info(f"   Total items: {len(vehicles)}")
    log.info("=" * 60)'''

new_save = '''    log.info(f"\\n✅ Google feed saved to: {OUTPUT_FILE}")

    # Save Meta feed
    meta_xml = build_meta_feed(vehicles)
    with open("rohneselmer_feed_meta.xml", "w", encoding="utf-8") as f:
        f.write(meta_xml)
    log.info(f"✅ Meta feed saved to: rohneselmer_feed_meta.xml")
    log.info(f"   Total items: {len(vehicles)}")
    log.info("=" * 60)'''

content = content.replace(old_save, new_save)

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("✅ Meta feed function added successfully!")
print("Run: python3 rohneselmer_feed_generator.py")
