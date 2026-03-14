"""
Fikser extract_description:
1. Riktig CSS-klasse: gw-tabs__content (to understreker)
2. Fjerner selger-info og kontaktinfo fra beskrivelsen
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

old_func = '''def extract_description(soup, fallback_title):
    """
    Extract free-text description from Beskrivelse tab.
    Stops before spec bullet lines. Max 600 chars.
    """
    import re

    # Try all tab panels
    for tab in soup.select(".gw-tabs_content, [role='tabpanel']"):
        paragraphs = []
        for p in tab.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            text = re.sub(r"\\s+", " ", text).strip()
            if not text:
                continue
            # Stop at spec-like short lines
            if len(text) < 35 and re.search(r"\\d|hestekrefter|varme|seter|dør|km|motor|gir|hjul|lakk|ratt|felg|navi|skinn|led|pdc|dab", text.lower()):
                break
            if len(text) > 20:
                paragraphs.append(text)
            if sum(len(p) for p in paragraphs) >= 500:
                break

        if paragraphs:
            return " ".join(paragraphs)[:600]

    return fallback_title'''

new_func = '''def extract_description(soup, fallback_title):
    """
    Extract free-text description from Beskrivelse tab.
    Uses correct class gw-tabs__content (double underscore).
    Stops before seller/contact info. Max 600 chars.
    """
    import re

    # Stop keywords — seller info, contact details etc
    stop_keywords = [
        "selger", "salgssjef", "mobil:", "finansiering", "forsikring",
        "innbytte", "visning", "facetime", "santander", "ta kontakt"
    ]

    for tab in soup.select(".gw-tabs__content"):
        paragraphs = []
        for p in tab.find_all("p"):
            text = p.get_text(separator=" ", strip=True)
            text = re.sub(r"\\s+", " ", text).strip()
            if not text:
                continue

            # Stop at seller/contact info
            text_lower = text.lower()
            if any(kw in text_lower for kw in stop_keywords):
                break

            # Stop at spec-like bullet lines
            if len(text) < 35 and re.search(r"\\d|hestekrefter|varme|seter|dør|km|motor|gir|hjul|lakk|ratt|felg|navi|skinn|led|pdc|dab", text_lower):
                break

            if len(text) > 20:
                paragraphs.append(text)

            if sum(len(x) for x in paragraphs) >= 500:
                break

        if paragraphs:
            return " ".join(paragraphs)[:600]

    return fallback_title'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print("✅ Fikset extract_description med riktig CSS-klasse!")
else:
    print("⚠️  Fant ikke extract_description funksjonen")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
