"""
Fjerner duplikat identifier_exists fra build_feed
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# The duplicate comes from an old identifier_exists line further down
# Remove the second occurrence only
first = content.find('field("identifier_exists", "no")')
second = content.find('field("identifier_exists", "no")', first + 1)

if second != -1:
    # Remove the second occurrence + newline
    content = content[:second] + content[second + len('        field("identifier_exists", "no")\n'):]
    print("✅ Fjernet duplikat identifier_exists!")
else:
    print("⚠️  Ingen duplikat funnet")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
