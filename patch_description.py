"""
Henter beskrivelse fra gw-tabs_content i stedet for meta description.
Stopper før spec-linjer og begrenser til 500 tegn.
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Add description extraction function
desc_func = '''
def extract_description(soup, fallback_title):
    """
    Extract the free-text description from the Beskrivelse tab.
    Stops before bullet/spec lines and limits to 500 chars.
    """
    import re

    tab = soup.select_one(".gw-tabs_content")
    if not tab:
        return fallback_title

    sentences = []
    total_len = 0

    for el in tab.find_all(["p", "span", "strong", "br"]):
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue

        # Stop if line looks like a spec bullet (short, contains numbers/keywords)
        if len(text) < 40 and re.search(r'\\d|hestekrefter|varme|seter|dør|km|motor|gir|hjul|lakk|ratt|felg|navi|skinn|led|pdc|dab', text.lower()):
            break

        # Stop if line is very short and looks like a list item
        if len(text) < 20:
            continue

        sentences.append(text)
        total_len += len(text)

        if total_len >= 500:
            break

    if sentences:
        description = " ".join(sentences)
        # Clean up extra whitespace
        description = re.sub(r'\\s+', ' ', description).strip()
        return description[:600]

    return fallback_title

'''

if "def extract_description" not in content:
    content = content.replace("def scrape_vehicle(url):", desc_func + "def scrape_vehicle(url):")
    print("✅ Lagt til extract_description funksjon!")
else:
    print("⚠️  Funksjonen finnes allerede")

old_desc = (
    '    # Description\n'
    '    description = (\n'
    '        ld.get("description") or\n'
    '        (soup.find("meta", {"name": "description"}) and\n'
    '         soup.find("meta", {"name": "description"}).get("content")) or\n'
    '        (soup.find("meta", property="og:description") and\n'
    '         soup.find("meta", property="og:description").get("content")) or\n'
    '        title\n'
    '    )\n'
    '    description = description[:5000] if description else ""'
)

new_desc = (
    '    # Description — from Beskrivelse tab first, fallback to meta\n'
    '    description = extract_description(soup, title)\n'
    '    if not description or description == title:\n'
    '        description = (\n'
    '            ld.get("description") or\n'
    '            (soup.find("meta", {"name": "description"}) and\n'
    '             soup.find("meta", {"name": "description"}).get("content")) or\n'
    '            (soup.find("meta", property="og:description") and\n'
    '             soup.find("meta", property="og:description").get("content")) or\n'
    '            title\n'
    '        )\n'
    '    description = description[:5000] if description else ""'
)

if old_desc in content:
    content = content.replace(old_desc, new_desc)
    print("✅ Oppdatert description-scraping!")
else:
    print("⚠️  Fant ikke description-blokken")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
