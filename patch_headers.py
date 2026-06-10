"""
Fikser 403-blokkering med bedre headers og requests.Session
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

old_headers = '''HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8",
}'''

new_headers = '''HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8,en-US;q=0.7,en;q=0.6",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

def make_session():
    """Create a requests session that mimics a real browser."""
    import requests as req
    session = req.Session()
    session.headers.update(HEADERS)
    # Visit homepage first to get cookies
    try:
        session.get("https://www.rohneselmer.no", timeout=15)
    except Exception:
        pass
    return session

SESSION = make_session()'''

if old_headers in content:
    content = content.replace(old_headers, new_headers)
    print("✅ Oppdatert headers!")
else:
    print("⚠️  Fant ikke HEADERS-blokken")

# Replace requests.get with SESSION.get
old_get1 = "r = requests.get(sitemap_url, headers=HEADERS, timeout=15)"
new_get1 = "r = SESSION.get(sitemap_url, timeout=15)"

if old_get1 in content:
    content = content.replace(old_get1, new_get1)
    print("✅ Oppdatert sitemap-kall!")
else:
    print("⚠️  Fant ikke sitemap-kallet")

old_get2 = "r = requests.get(url, headers=HEADERS, timeout=20)"
new_get2 = "r = SESSION.get(url, timeout=20)"

if old_get2 in content:
    content = content.replace(old_get2, new_get2)
    print("✅ Oppdatert bil-kall!")
else:
    print("⚠️  Fant ikke bil-kallet")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
