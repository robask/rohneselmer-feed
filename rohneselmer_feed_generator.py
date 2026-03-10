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
    """Find all product images."""
    images = []
    # OG image first (usually main photo)
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        images.append(og["content"])

    # Look for gallery images
    for img in soup.select("[class*='gallery'] img, [class*='slider'] img, [class*='photo'] img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy")
        if src:
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = base_url + src
            if src not in images and not src.endswith(".svg"):
                images.append(src)

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

    # Description
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
    price = f"{price_raw} NOK" if price_raw else None

    # Images
    images = extract_images(soup, BASE_URL)
    main_image = images[0] if images else None
    extra_images = images[1:] if len(images) > 1 else []

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
    }


# ══════════════════════════════════════════════════════════
#  STEP 3 — Build XML feed (GMC + Meta compatible)
# ══════════════════════════════════════════════════════════

def build_feed(vehicles):
    """Generate Google Merchant Center + Meta compatible XML feed."""

    rss = ET.Element("rss", {
        "version": "2.0",
        "xmlns:g": "http://base.google.com/ns/1.0",
        "xmlns:atom": "http://www.w3.org/2005/Atom",
    })
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text       = "Rohne Selmer — Bruktbiler"
    ET.SubElement(channel, "link").text        = BASE_URL
    ET.SubElement(channel, "description").text = "Bruktbil-lager fra Rohne Selmer"

    # Atom self-link — required for Meta/RSS validation
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", "https://robask.github.io/rohneselmer-feed/rohneselmer_feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for v in vehicles:
        if not v:
            continue

        item = ET.SubElement(channel, "item")

        def add(tag, value, ns="g"):
            if value:
                el = ET.SubElement(item, f"{ns}:{tag}" if ns else tag)
                el.text = str(value)

        # ── Required fields ──────────────────────────────
        add("id",           v["id"])
        add("title",        v["title"])
        add("description",  v["description"] or v["title"])
        add("link",         v["url"])
        add("image_link",   v["main_image"])
        add("availability", v["availability"])
        add("condition",    v["condition"])
        add("price",        v["price"] or "0 NOK")

        # ── Vehicle-specific fields ───────────────────────
        if v["brand"]:        add("brand",                    v["brand"])
        if v["model"]:        add("model",                    v["model"])
        if v["year"]:         add("vehicle_year",             v["year"])
        if v["vin"]:          add("gtin",                     v["vin"])
        if v["mileage"]:      add("mileage",                  f"{v['mileage']} km")
        if v["fuel_type"]:    add("fuel_type",                v["fuel_type"])
        if v["transmission"]: add("transmission",             v["transmission"])
        if v["body_type"]:    add("body_style",               v["body_type"])
        if v["color"]:        add("color",                    v["color"])
        if v["drive_type"]:   add("drive_wheel_configuration",v["drive_type"])

        # ── Extra vehicle details ────────────────────────
        if v["doors"]:       add("number_of_doors",  v["doors"])
        if v["horsepower"]:  add("horsepower",        v["horsepower"])
        if v["engine_size"]: add("engine_size",       v["engine_size"])
        if v["seats"]:       add("number_of_seats",   v["seats"])

        # ── Additional images (up to 9 extra) ────────────
        for img in v["extra_images"][:9]:
            add("additional_image_link", img)

        # ── Google product category for vehicles ─────────
        add("google_product_category", "916")  # Vehicles & Parts > Vehicles > Motor Vehicles

    # Pretty-print XML — manually inject namespaces so Meta accepts it
    xml_str = ET.tostring(rss, encoding="unicode")
    # ET strips custom namespaces from root element, so we inject them manually
    xml_str = xml_str.replace(
        '<rss version="2.0">',
        '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0" xmlns:atom="http://www.w3.org/2005/Atom">'
    )
    reparsed = minidom.parseString(xml_str.encode("utf-8"))
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

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

    log.info(f"\n✅ Feed saved to: {OUTPUT_FILE}")
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
