"""
Fikser extract_images til å hente bilder fra gw-slider__slides
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

old_images = '''def extract_images(soup, base_url):
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

    return images[:10]  # Max 10 images'''

new_images = '''def extract_images(soup, base_url):
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

    return images[:10]  # Max 10 images'''

if old_images in content:
    content = content.replace(old_images, new_images)
    print("✅ Fikset extract_images!")
else:
    print("⚠️  Fant ikke extract_images funksjonen")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("Kjør: python3 rohneselmer_feed_generator.py")
