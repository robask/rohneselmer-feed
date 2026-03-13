"""
Legger til dealer_name i Meta feed basert på lokasjon.
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Update region/dealer_name logic in extract_dealer_address
old_region = """    # Determine region from city/name
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

    return result"""

new_region = """    # Determine region and dealer_name from city/name
    name_lower = result["name"].lower() + " " + result["city"].lower()
    if any(x in name_lower for x in ["oslo"]):
        result["region"] = "Oslo"
        result["dealer_name"] = "Oslo"
    elif any(x in name_lower for x in ["lillestrøm", "lillestrøm", "romerike", "lørenskog"]):
        result["region"] = "Viken"
        result["dealer_name"] = "Lillestrøm"
    elif any(x in name_lower for x in ["asker", "bærum", "billingstad", "sandvika"]):
        result["region"] = "Viken"
        result["dealer_name"] = "Asker og Bærum"
    elif any(x in name_lower for x in ["hønefoss", "ringerike"]):
        result["region"] = "Viken"
        result["dealer_name"] = "Hønefoss"
    elif any(x in name_lower for x in ["lier", "lierstranda", "drammen"]):
        result["region"] = "Viken"
        result["dealer_name"] = "Lierstranda"
    else:
        result["region"] = "Viken"
        result["dealer_name"] = result["name"] or "Rohne Selmer"

    return result"""

if old_region in content:
    content = content.replace(old_region, new_region)
    print("✅ Oppdatert region/dealer_name logikk!")
else:
    print("⚠️  Fant ikke region-blokken")

# Add dealer_name to return dict in scrape_vehicle
old_return = '        "dealer_region":    dealer["region"],\n    }'
new_return = '        "dealer_region":    dealer["region"],\n        "dealer_name":      dealer.get("dealer_name", "Rohne Selmer"),\n    }'

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✅ Lagt til dealer_name i return!")
else:
    print("⚠️  Fant ikke return-blokken")

# Add dealer_name field in Meta feed after address block
old_addr_end = "        lines.append(f'    </address>')"
new_addr_end = "        lines.append(f'    </address>')\n        lines.append(f'    <dealer_name>{esc(v[\"dealer_name\"])}</dealer_name>')"

if old_addr_end in content:
    content = content.replace(old_addr_end, new_addr_end)
    print("✅ Lagt til dealer_name i Meta feed!")
else:
    print("⚠️  Fant ikke address-slutten")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
