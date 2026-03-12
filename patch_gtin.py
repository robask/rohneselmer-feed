"""
Safe patch - only removes gtin field and adds identifier_exists = no
Nothing else is touched.
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Remove gtin line
old = '        field("gtin",         v["vin"])'
new = '        field("identifier_exists", "no")'

if old in content:
    content = content.replace(old, new)
    print("✅ Replaced gtin with identifier_exists = no")
else:
    print("❌ Could not find gtin line - no changes made")
    exit()

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Done! Run: python3 rohneselmer_feed_generator.py")
