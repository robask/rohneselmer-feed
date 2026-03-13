#!/usr/bin/env python3
"""
=============================================================
  Rohne Selmer — Product Feed Generator
  Generates XML feed compatible with:
    - Google Merchant Center
    - Meta (Facebook/Instagram) Automotive Inventory Ads
=============================================================

  HOW TO USE:
  1. Install dependencies:
       pip install requests beautifulsoup4 lxml

  2. Run the script:
       python rohneselmer_feed_generator.py

  3. Output:
       rohneselmer_feed.xml  ← upload this to GMC / Meta

  4. To keep it live, run on a schedule:
       - Mac/Linux: add to crontab (see bottom of file)
       - Windows: Task Scheduler
       - Cloud: Railway / Render / cron-job.org (free)

=============================================================
"""

import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
from bs4 import BeautifulSoup
import time
import re
import logging
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
BASE_URL        = "https://www.rohneselmer.no"
SITEMAP_BASE    = "https://www.rohneselmer.no/sitemap-vehicle-stock-{}.xml"
MAX_SITEMAPS    = 20        # Will stop early if sitemap not found
OUTPUT_FILE     = "rohneselmer_feed.xml"
DELAY_SECONDS   = 1.5      # Be polite — pause between requests
LOG_FILE        = "feed_generator.log"
# ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8",
}


# ══════════════════════════════════════════════════════════
#  STEP 1 — Collect all car URLs from sitemaps
# ══════════════════════════════════════════════════════════

def get_all_vehicle_urls():
    """Read all sitemap-vehicle-stock-N.xml files and return car URLs."""
    all_urls = []
    for i in range(1, MAX_SITEMAPS + 1):
        sitemap_url = SITEMAP_BASE.format(i)
        log.info(f"Reading sitemap: {sitemap_url}")
        try:
            r = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            if r.status_code == 404:
                log.info(f"Sitemap {i} not found — stopping.")
                break
            r.raise_for_status()
            root = ET.fromstring(r.content)
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [loc.text.strip() for loc in root.findall(".//sm:loc", ns)
                    if "/biler/lager/" in loc.text]
            log.info(f"  Found {len(urls)} vehicles in sitemap {i}")
            all_urls.extend(urls)
            time.sleep(0.5)
        except Exception as e:
            log.error(f"Error reading sitemap {i}: {e}")
            break
    log.info(f"Total vehicle URLs found: {len(all_urls)}")
    return all_urls


# ══════════════════════════════════════════════════════════
#  STEP 2 — Scrape data from each car listing page
# ══════════════════════════════════════════════════════════

def extract_price(soup):
    """Try multiple strategies to find the price."""
    # Strategy 1: Rohne Selmer — find price element and grab spans
    price_el = soup.select_one(".gw-inventory-summary__price--original")
    if price_el:
        for span in price_el.find_all("span"):
            txt = span.get_text(strip=True).replace("\xa0", "").replace("\u00a0", "")
            nums = re.sub(r"[^0-9]", "", txt)
            if len(nums) >= 4:
                return nums

    # Strategy 2: JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            if "offers" in data:
                price = data["offers"].get("price") or data["offers"].get("lowPrice")
                if price:
                    return str(price)
            if "price" in data:
                return str(data["price"])
        except:
            pass

    # Strategy 3: Any element with price class
    for sel in ["[class*='price']", "[class*='pris']"]:
        el = soup.select_one(sel)
        if el:
            txt = el.get_text(strip=True).replace("\xa0", "")
            nums = re.sub(r"[^0-9]", "", txt)
            if len(nums) >= 4:
                return nums

    return None


def extract_json_ld(soup):
    """Extract JSON-LD structured data if present."""
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0]
            if data.get("@type") in ("Car", "Vehicle", "Product", "AutoDealer"):
                return data
        except:
            pass
    return {}


def extract_images(soup, base_url):
    """Find all product images from gw-slider__slides."""
    images = []

    # Primary: get images from vehicle slider
    for slide in soup.select(".gw-slider__slides .gw-slider_slide"):
        img = slide.select_one("img.gw-image")
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = base_url + src
                # Only include actual vehicle images (stockvehicles), not promotions
                if "stockvehicles" in src and src not in images:
                    images.append(src)

    # Fallback: OG image if no slider images found
    if not images:
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            images.append(og["content"])

    return images[:10]  # Max 10 images


def parse_url_slug(url):
    """Extract make/model hint from URL slug."""
    # URL pattern: /biler/lager/ID/BRANCH_ID/make-model-variant
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        slug = parts[-1]  # e.g. "ford-kuga-2-0-tdci-awd"
        return slug
    return ""


def parse_specs_table(soup):
    """
    Parse the gw-table specs table on rohneselmer.no listing pages.
    Returns a dict of all th/td pairs, e.g.:
    {"km-stand": "73 360 Km", "drivstoff": "Diesel", ...}
    """
    specs = {}
    table = soup.find("table", class_="gw-table")
    if not table:
        return specs
    for row in table.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th and td:
            key   = th.get_text(strip=True).lower()
            value = td.get_text(strip=True).replace("\xa0", " ").strip()
            specs[key] = value
    return specs



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
            city_raw = match.group(3).strip()
            # Remove "Telefon: XX XX XX XX" and similar
            city_raw = re.sub(r'Telefon:.*', '', city_raw).strip()
            city_raw = re.sub(r'\s+', ' ', city_raw).strip()
            result["city"] = city_raw
        else:
            result["street"] = text

    # Determine region and dealer_name from city/name
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

    return result


def extract_description(soup, fallback_title):
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
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            # Stop at spec-like short lines
            if len(text) < 35 and re.search(r"\d|hestekrefter|varme|seter|dør|km|motor|gir|hjul|lakk|ratt|felg|navi|skinn|led|pdc|dab", text.lower()):
                break
            if len(text) > 20:
                paragraphs.append(text)
            if sum(len(p) for p in paragraphs) >= 500:
                break

        if paragraphs:
            return " ".join(paragraphs)[:600]

    return fallback_title

    sentences = []
    total_len = 0

    for el in tab.find_all(["p", "span", "strong", "br"]):
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue

        # Stop if line looks like a spec bullet (short, contains numbers/keywords)
        if len(text) < 40 and re.search(r'\d|hestekrefter|varme|seter|dør|km|motor|gir|hjul|lakk|ratt|felg|navi|skinn|led|pdc|dab', text.lower()):
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
        description = re.sub(r'\s+', ' ', description).strip()
        return description[:600]

    return fallback_title

def scrape_vehicle(url):
    """Scrape all available data from a car listing page."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        log.error(f"Failed to fetch {url}: {e}")
        return None

    soup = BeautifulSoup(r.text, "lxml")
    ld  = extract_json_ld(soup)
    dealer = extract_dealer_address(soup)

    # Extract listing ID from URL
    url_parts = url.split("/")
    listing_id = None
    for i, part in enumerate(url_parts):
        if part == "lager" and i + 1 < len(url_parts):
            listing_id = url_parts[i + 1]
            break

    # Title
    title = (
        ld.get("name") or
        (soup.find("h1") and soup.find("h1").get_text(separator=" ", strip=True)) or
        soup.find("meta", property="og:title") and soup.find("meta", property="og:title").get("content") or
        parse_url_slug(url).replace("-", " ").title()
    )

    # Description — from Beskrivelse tab first, fallback to meta
    description = extract_description(soup, title)
    if not description or description == title:
        description = (
            ld.get("description") or
            (soup.find("meta", {"name": "description"}) and
             soup.find("meta", {"name": "description"}).get("content")) or
            (soup.find("meta", property="og:description") and
             soup.find("meta", property="og:description").get("content")) or
            title
        )
    description = description[:5000] if description else ""

    # Price
    price_raw = extract_price(soup)
    price = price_raw if price_raw else None

    # Images — use images[3] as main (third additional image, no graphics overlay)
    images = extract_images(soup, BASE_URL)
    if len(images) >= 4:
        main_image = images[3]
        extra_images = [img for i, img in enumerate(images) if i != 3]
    elif images:
        main_image = images[0]
        extra_images = images[1:]
    else:
        main_image = None
        extra_images = []

    # VIN
    vin = ld.get("vehicleIdentificationNumber")
    if not vin:
        vin_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', r.text)
        if vin_match:
            vin = vin_match.group()

    # Parse specs table — rohneselmer.no has a gw-table with all specs
    specs = parse_specs_table(soup)

    # Vehicle specifics — specs table takes priority over JSON-LD
    make         = ld.get("brand", {}).get("name") if isinstance(ld.get("brand"), dict) else ld.get("brand")
    model        = ld.get("model")
    model_year   = ld.get("modelDate") or ld.get("vehicleModelDate")

    # Mileage — from property attribute or specs table
    mileage_td = soup.find("td", property="mileageFromOdometer")
    if mileage_td:
        mileage = re.sub(r"[^\d]", "", mileage_td.get_text())
    else:
        mileage_raw = ld.get("mileageFromOdometer", {})
        if isinstance(mileage_raw, dict):
            mileage = str(mileage_raw.get("value", ""))
        elif isinstance(mileage_raw, (str, int)):
            mileage = str(mileage_raw)
        else:
            mileage = specs.get("km-stand", "")
            mileage = re.sub(r"[^\d]", "", mileage)

    # All other specs from table
    fuel_type    = ld.get("fuelType")    or specs.get("drivstoff")    or specs.get("fuel type")
    transmission = ld.get("vehicleTransmission") or specs.get("girkasse") or specs.get("transmisjon")
    body_type    = ld.get("bodyType")    or specs.get("karosseri")    or specs.get("body type")
    color        = ld.get("color")       or specs.get("farge")        or specs.get("colour")
    drive_type   = ld.get("driveWheelConfiguration") or specs.get("hjuldrift")
    doors        = specs.get("antall dører") or specs.get("dører")   or specs.get("doors")
    horsepower   = specs.get("hestekrefter") or specs.get("effekt")  or specs.get("motor")
    engine_size  = specs.get("sylindervolum") or specs.get("motor")
    seats        = specs.get("seter")    or specs.get("antall seter")
    reg_number   = specs.get("reg.nr")   or specs.get("registreringsnummer")

    # Availability — assume in stock unless we find otherwise
    availability = "in stock"

    # Smart brand/model/year extraction from title
    # Title pattern: "2016 Volkswagen Golf e-Golf"
    if title:
        title_parts = title.strip().split()
        if title_parts and re.match(r'^(19|20)\d{2}$', title_parts[0]):
            if not model_year:
                model_year = title_parts[0]
            if len(title_parts) > 1 and not make:
                make = title_parts[1]
            if len(title_parts) > 2 and not model:
                model = " ".join(title_parts[2:])
        elif not make:
            make = title_parts[0] if title_parts else ""
            if len(title_parts) > 1 and not model:
                model = " ".join(title_parts[1:])

    # Clean up duplicate words in model name
    # e.g. "Kuga Kuga Plug-In Hybrid" → "Kuga Plug-In Hybrid"
    # e.g. "Leaf Leaf" → "Leaf"
    if model:
        words = model.split()
        cleaned = []
        for i, word in enumerate(words):
            if i > 0 and word.lower() == cleaned[-1].lower():
                continue
            cleaned.append(word)
        model = " ".join(cleaned).strip()

    return {
        "id":               listing_id or url.split("/")[-2],
        "url":              url,
        "title":            title,
        "description":      description,
        "price":            price,
        "main_image":       main_image,
        "extra_images":     extra_images,
        "availability":     availability,
        "condition":        "used",
        "brand":            make or "",
        "model":            model or "",
        "year":             model_year or "",
        "vin":              vin or "",
        "mileage":          mileage or "",
        "fuel_type":        fuel_type or "",
        "transmission":     transmission or "",
        "body_type":        body_type or "",
        "color":            color or "",
        "drive_type":       drive_type or "",
        "doors":            doors or "",
        "horsepower":       horsepower or "",
        "engine_size":      engine_size or "",
        "seats":            seats or "",
        "reg_number":       reg_number or "",
        "dealer_street":    dealer["street"],
        "dealer_city":      dealer["city"],
        "dealer_postal":    dealer["postal_code"],
        "dealer_region":    dealer["region"],
        "dealer_name":      dealer.get("dealer_name", "Rohne Selmer"),
    }


# ══════════════════════════════════════════════════════════
#  STEP 3 — Build XML feed (GMC + Meta compatible)
# ══════════════════════════════════════════════════════════

def build_feed(vehicles):
    """Generate Google Merchant Center + Meta compatible XML feed."""

    # Build XML manually as string to guarantee namespaces are preserved
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0" xmlns:atom="http://www.w3.org/2005/Atom">')
    lines.append('  <channel>')
    lines.append('    <title>Rohne Selmer — Bruktbiler</title>')
    lines.append(f'    <link>{BASE_URL}</link>')
    lines.append('    <description>Bruktbil-lager fra Rohne Selmer</description>')
    lines.append('    <atom:link href="https://robask.github.io/rohneselmer-feed/rohneselmer_feed.xml" rel="self" type="application/rss+xml"/>')

    def esc(val):
        if not val:
            return ""
        return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for v in vehicles:
        if not v:
            continue
        lines.append('    <item>')

        def field(tag, value):
            if value:
                lines.append(f'      <g:{tag}>{esc(value)}</g:{tag}>')

        field("id",           v["id"])
        field("title",        v["title"])
        field("description",  v["description"] or v["title"])
        field("link",         v["url"])
        field("image_link",   v["main_image"])
        field("availability", v["availability"])
        field("condition",    v["condition"])
        field("identifier_exists", "no")
        field("product_type",     "Vehicles & Parts > Vehicles > Motor Vehicles > Cars, Trucks & Vans")
        field("price",        (v["price"] or "0") + " NOK")
        field("brand",        v["brand"])
        field("model",        v["model"])
        field("vehicle_year", v["year"])
        field("identifier_exists", "no")
        if v["mileage"]:
            field("mileage",  v["mileage"] + " km")
        field("fuel_type",                 v["fuel_type"])
        field("transmission",              v["transmission"])
        field("body_style",                v["body_type"])
        field("color",                     v["color"])
        field("drive_wheel_configuration", v["drive_type"])
        field("number_of_doors",           v["doors"])
        field("horsepower",                v["horsepower"])
        field("engine_size",               v["engine_size"])
        field("number_of_seats",           v["seats"])
        for img in v["extra_images"][:9]:
            field("additional_image_link", img)
        field("google_product_category", "916")

        lines.append('    </item>')

    lines.append('  </channel>')
    lines.append('</rss>')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════



def translate_fuel_type(val):
    if not val:
        return "OTHER"
    v = val.strip().lower()
    if v in ("el", "elektrisk", "electric", "ev"):
        return "ELECTRIC"
    if v in ("bensin", "gasoline", "petrol"):
        return "GASOLINE"
    if v in ("diesel", "forbrenningsmotor"):
        return "DIESEL"
    if "plug" in v or "plugin" in v or "plug-in" in v:
        return "PLUGIN_HYBRID"
    if "hybrid" in v:
        return "HYBRID"
    return "OTHER"

def translate_transmission(val):
    if not val:
        return "OTHER"
    v = val.strip().lower()
    if v in ("automat", "automatic", "automatisk"):
        return "AUTOMATIC"
    if v in ("manuell", "manual"):
        return "MANUAL"
    return "OTHER"

def build_meta_feed(vehicles):
    """Generate Meta Automotive Inventory Ads feed in correct <listings> format."""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<listings>')

    def esc(val):
        if not val:
            return ""
        return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    for v in vehicles:
        if not v:
            continue
        lines.append('  <listing>')
        lines.append(f'    <vehicle_id>{esc(v["id"])}</vehicle_id>')
        lines.append(f'    <title>{esc(v["title"])}</title>')
        lines.append(f'    <description>{esc(v["description"] or v["title"])}</description>')
        lines.append(f'    <url>{esc(v["url"])}</url>')

        if v["main_image"]:
            lines.append(f'    <image><url>{esc(v["main_image"])}</url></image>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <image><url>{esc(img)}</url></image>')

        lines.append(f'    <make>{esc(v["brand"])}</make>')
        lines.append(f'    <model>{esc(v["model"])}</model>')
        lines.append(f'    <year>{esc(v["year"])}</year>')
        lines.append(f'    <state_of_vehicle>USED</state_of_vehicle>')
        lines.append(f'    <address format="simple">')
        lines.append(f'      <component name="addr1">{esc(v["dealer_street"])}</component>')
        lines.append(f'      <component name="city">{esc(v["dealer_city"])}</component>')
        lines.append(f'      <component name="region">{esc(v["dealer_region"])}</component>')
        lines.append(f'      <component name="postal_code">{esc(v["dealer_postal"])}</component>')
        lines.append(f'      <component name="country">Norway</component>')
        lines.append(f'    </address>')
        lines.append(f'    <dealer_name>{esc(v["dealer_name"])}</dealer_name>')

        price_num = v["price"].replace(" NOK", "").strip() if v["price"] else "0"
        lines.append(f'    <price>{esc(price_num)} NOK</price>')

        if v["mileage"]:
            lines.append(f'    <mileage>')
            lines.append(f'      <unit>KM</unit>')
            lines.append(f'      <value>{esc(v["mileage"])}</value>')
            lines.append(f'    </mileage>')

        lines.append(f'    <body_style>{esc(v["body_type"]) if v["body_type"] else "Sedan"}</body_style>')
        lines.append(f'    <transmission>{translate_transmission(v["transmission"])}</transmission>')
        lines.append(f'    <fuel_type>{translate_fuel_type(v["fuel_type"])}</fuel_type>')
        if v["color"]:
            lines.append(f'    <exterior_color>{esc(v["color"])}</exterior_color>')
        if v["drive_type"]:
            lines.append(f'    <drivetrain>{esc(v["drive_type"])}</drivetrain>')
        if v["vin"]:
            lines.append(f'    <vin>{esc(v["vin"])}</vin>')

        lines.append('  </listing>')

    lines.append('</listings>')
    return chr(10).join(lines)


def main():
    log.info("=" * 60)
    log.info(f"Feed generation started: {datetime.now()}")
    log.info("=" * 60)

    # Step 1: Get all vehicle URLs
    urls = get_all_vehicle_urls()
    if not urls:
        log.error("No vehicle URLs found. Exiting.")
        return

    # Step 2: Scrape each listing
    vehicles = []
    for i, url in enumerate(urls, 1):
        log.info(f"[{i}/{len(urls)}] Scraping: {url}")
        data = scrape_vehicle(url)
        if data:
            vehicles.append(data)
            log.info(f"  ✓ {data['title']} | {data['price'] or 'No price'}")
        else:
            log.warning(f"  ✗ Failed: {url}")
        time.sleep(DELAY_SECONDS)

    log.info(f"\nSuccessfully scraped: {len(vehicles)}/{len(urls)} vehicles")

    # Step 3: Build and save XML feed
    feed_xml = build_feed(vehicles)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(feed_xml)

    log.info(f"\n✅ Google feed saved to: {OUTPUT_FILE}")

    # Save Meta feed
    meta_xml = build_meta_feed(vehicles)
    with open("rohneselmer_feed_meta.xml", "w", encoding="utf-8") as f:
        f.write(meta_xml)
    log.info(f"✅ Meta feed saved to: rohneselmer_feed_meta.xml")
    log.info(f"   Total items: {len(vehicles)}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()


# ══════════════════════════════════════════════════════════
#  SCHEDULING (run this automatically)
# ══════════════════════════════════════════════════════════
#
#  Mac/Linux — add to crontab (crontab -e):
#  Run every 2 hours:
#    0 */2 * * * /usr/bin/python3 /path/to/rohneselmer_feed_generator.py
#
#  To serve the XML file at a public URL (free options):
#  1. Upload to Google Drive → share publicly → use direct link
#  2. Host on Railway.app or Render.com (free tier)
#  3. Use GitHub Actions to run script + commit XML to repo
#     → GitHub Pages gives you a free public URL!
#
# ══════════════════════════════════════════════════════════
