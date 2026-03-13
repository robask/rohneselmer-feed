"""
Fikser:
1. City inneholder "Telefon: XX XX XX XX" - ryddes opp
2. Description henter fra gw-tabs_content riktig
"""
import re

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Fix 1: Clean up city field - remove "Telefon: XX XX XX XX" 
old_city = '''        match = re.search(r'(.*?)(\\d{4})\\s+(.*)', text)
        if match:
            result["street"] = match.group(1).strip().rstrip(",").strip()
            result["postal_code"] = match.group(2)
            result["city"] = match.group(3).strip()
        else:
            result["street"] = text'''

new_city = '''        match = re.search(r'(.*?)(\\d{4})\\s+(.*)', text)
        if match:
            result["street"] = match.group(1).strip().rstrip(",").strip()
            result["postal_code"] = match.group(2)
            city_raw = match.group(3).strip()
            # Remove "Telefon: XX XX XX XX" and similar
            city_raw = re.sub(r'Telefon:.*', '', city_raw).strip()
            city_raw = re.sub(r'\\s+', ' ', city_raw).strip()
            result["city"] = city_raw
        else:
            result["street"] = text'''

if old_city in content:
    content = content.replace(old_city, new_city)
    print("✅ Fikset city-parsing!")
else:
    print("⚠️  Fant ikke city-blokken")

# Fix 2: Replace extract_description with a simpler, more reliable version
old_func_start = "def extract_description(soup, fallback_title):"
old_func_end = "    return fallback_title\n\n"

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end, start_idx)

if start_idx != -1 and end_idx != -1:
    new_func = '''def extract_description(soup, fallback_title):
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

    return fallback_title

'''
    content = content[:start_idx] + new_func + content[end_idx + len(old_func_end):]
    print("✅ Oppdatert extract_description!")
else:
    print("⚠️  Fant ikke extract_description funksjonen")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
