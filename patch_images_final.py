"""
1. Bytter hovedbilde fra images[3] til images[1]
2. Endrer Meta-feeden til å bruke image_link og additional_image_link
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Fix 1: Change main image from images[3] to images[1]
old_img = '''    # Images — use images[3] as main (third additional image, no graphics overlay)
    images = extract_images(soup, BASE_URL)
    if len(images) >= 4:
        main_image = images[3]
        extra_images = [img for i, img in enumerate(images) if i != 3]
    elif images:
        main_image = images[0]
        extra_images = images[1:]
    else:
        main_image = None
        extra_images = []'''

new_img = '''    # Images — use images[1] as main (second image, no graphics overlay)
    images = extract_images(soup, BASE_URL)
    if len(images) >= 2:
        main_image = images[1]
        extra_images = [img for i, img in enumerate(images) if i != 1]
    elif images:
        main_image = images[0]
        extra_images = []
    else:
        main_image = None
        extra_images = []'''

if old_img in content:
    content = content.replace(old_img, new_img)
    print("✅ Byttet til images[1] som hovedbilde!")
else:
    print("⚠️  Fant ikke bildelogikken")

# Fix 2: Update Meta feed to use image_link and additional_image_link
old_meta_images = '''        if v["main_image"]:
            lines.append(f'    <image><url>{esc(v["main_image"])}</url></image>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <image><url>{esc(img)}</url></image>')'''

new_meta_images = '''        if v["main_image"]:
            lines.append(f'    <image_link>{esc(v["main_image"])}</image_link>')
        for img in v["extra_images"][:9]:
            lines.append(f'    <additional_image_link>{esc(img)}</additional_image_link>')'''

if old_meta_images in content:
    content = content.replace(old_meta_images, new_meta_images)
    print("✅ Oppdatert Meta feed til image_link/additional_image_link!")
else:
    print("⚠️  Fant ikke bildeblokken i Meta feed")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nKjør: python3 rohneselmer_feed_generator.py")
