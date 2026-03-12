"""
Patcher rohneselmer_feed_generator.py:
1. Legger til identifier_exists = no
2. Legger til product_type
3. Bytter hovedbilde til TREDJE additional_image (images[3])
"""

with open("rohneselmer_feed_generator.py", "r") as f:
    content = f.read()

# Fix 1 & 2: Add identifier_exists and product_type after condition field in build_feed
old = '        field("condition",    v["condition"])\n        field("price",'
new = '        field("condition",    v["condition"])\n        field("identifier_exists", "no")\n        field("product_type",     "Vehicles & Parts > Vehicles > Motor Vehicles > Cars, Trucks & Vans")\n        field("price",'

if old in content:
    content = content.replace(old, new)
    print("✅ Fikset identifier_exists og product_type")
else:
    print("⚠️  Allerede lagt til, hopper over")

# Fix 3: Use images[3] as main image (third additional image, no graphics overlay)
old_images = '''    # Images
    images = extract_images(soup, BASE_URL)
    main_image = images[0] if images else None
    extra_images = images[1:] if len(images) > 1 else []'''

new_images = '''    # Images — use images[3] as main (third additional image, no graphics overlay)
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

if old_images in content:
    content = content.replace(old_images, new_images)
    print("✅ Fikset hovedbilde til tredje additional_image")
else:
    print("⚠️  Bildelogikk allerede endret, hopper over")

with open("rohneselmer_feed_generator.py", "w") as f:
    f.write(content)

print("\nDone! Kjør: python3 rohneselmer_feed_generator.py")
