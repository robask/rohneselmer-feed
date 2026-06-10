"""
1. Endrer User-Agent til Amidays-FeedBot/1.0
2. Øker forsinkelse til 5 sekunder
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Fix 1: Update User-Agent
old_ua = '"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",'
new_ua = '"User-Agent": "Amidays-FeedBot/1.0 (feed@amidays.com)",'

if old_ua in content:
    content = content.replace(old_ua, new_ua)
    print("✅ Oppdatert User-Agent!")
else:
    print("⚠️  Fant ikke User-Agent")

# Fix 2: Increase delay to 5 seconds
import re
old_delay = re.search(r'DELAY_SECONDS\s*=\s*[\d.]+', content)
if old_delay:
    content = content.replace(old_delay.group(), 'DELAY_SECONDS    = 5')
    print("✅ Forsinkelse satt til 5 sekunder!")
else:
    print("⚠️  Fant ikke DELAY_SECONDS")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
