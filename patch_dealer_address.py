"""
Scraper forhandleradresse fra hver bilside i stedet for hardkodet adresse.
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Add address scraping function before scrape_vehicle
address_func = '''
def extract_dealer_address(soup):
    """Extract dealer address from gw-contact-card on listing page."""
    result = {
        "name": "",
        "street": "",
        "city": "",
        "postal_code": "",
        "region": "Akershus",
    }
    card = soup.select_one(".gw-contact-card")
    if not card:
        return result

    # Dealer name
    title = card.select_one(".gw-card_title")
    if title:
        result["name"] = title.get_text(strip=True)

    # Address text from <address> tag
    addr = card.select_one("address")
    if addr:
        text = addr.get_text(separator=" ", strip=True)
        import re
        # Try to find postal code (4 digits) and split around it
        match = re.search(r'(.*?)(\d{4})\s+(.*)', text)
        if match:
            result["street"] = match.group(1).strip().rstrip(",").strip()
            result["postal_code"] = match.group(2)
            result["city"] = match.group(3).strip()
        else:
            result["street"] = text

    # Determine region from city/name
    name_lower = result["name"].lower() + result["city"].lower()
    if any(x in name_lower for x in ["oslo"]):
        result["region"] = "Oslo"
    elif any(x in name_lower for x in ["lillestrøm", "lillestrøm", "romerike", "lørenskog"]):
        result["region"] = "Viken"
    elif any(x in name_lower for x in ["asker", "bærum", "billingstad", "sandvika"]):
        result["region"] = "Viken"
    elif any(x in name_lower for x in ["drammen", "buskerud"]):
        result["region"] = "Viken"
    else:
        result["region"] = "Viken"

    return result

'''

if "def extract_dealer_address" not in content:
    content = content.replace("def scrape_vehicle(url):", address_func + "def scrape_vehicle(url):")
    print("✅ Lagt til extract_dealer_address funksjon!")
else:
    print("⚠️  Funksjonen finnes allerede")

# Use extract_dealer_address in scrape_vehicle — add after soup is parsed
old_soup = "    soup = BeautifulSoup(r.text, \"lxml\")\n    ld  = extract_json_ld(soup)"
new_soup = "    soup = BeautifulSoup(r.text, \"lxml\")\n    ld  = extract_json_ld(soup)\n    dealer = extract_dealer_address(soup)"

if old_soup in content:
    content = content.replace(old_soup, new_soup)
    print("✅ Lagt til dealer-scraping i scrape_vehicle!")
else:
    print("⚠️  Fant ikke soup-linjen")

# Add dealer to return dict
old_return = '        "reg_number":       reg_number or "",\n    }'
new_return = '        "reg_number":       reg_number or "",\n        "dealer_street":    dealer["street"],\n        "dealer_city":      dealer["city"],\n        "dealer_postal":    dealer["postal_code"],\n        "dealer_region":    dealer["region"],\n    }'

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✅ Lagt til dealer-felter i return!")
else:
    print("⚠️  Fant ikke return-blokken")

# Update Meta feed to use dealer address
old_addr = """        lines.append(f'    <address format="simple">')
        lines.append(f'      <component name="addr1">Bergerveien 12</component>')
        lines.append(f'      <component name="city">Billingstad</component>')
        lines.append(f'      <component name="region">Akershus</component>')
        lines.append(f'      <component name="postal_code">1396</component>')
        lines.append(f'      <component name="country">Norway</component>')
        lines.append(f'    </address>')"""

new_addr = """        lines.append(f'    <address format="simple">')
        lines.append(f'      <component name="addr1">{esc(v["dealer_street"])}</component>')
        lines.append(f'      <component name="city">{esc(v["dealer_city"])}</component>')
        lines.append(f'      <component name="region">{esc(v["dealer_region"])}</component>')
        lines.append(f'      <component name="postal_code">{esc(v["dealer_postal"])}</component>')
        lines.append(f'      <component name="country">Norway</component>')
        lines.append(f'    </address>')"""

if old_addr in content:
    content = content.replace(old_addr, new_addr)
    print("✅ Oppdatert Meta feed med dynamisk adresse!")
else:
    print("⚠️  Fant ikke adresse-blokken i Meta feed")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
