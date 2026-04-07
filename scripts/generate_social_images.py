"""
Automated Social Image Generator.
Generates Pinterest Pins (vertical) and OG Cards (horizontal) for tools and categories.
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import load_database, DIST_DIR, ensure_dir, SITE_NAME, slugify

def create_gradient(size, color1, color2):
    """Create a vertical gradient image."""
    base = Image.new('RGB', size, color1)
    top = Image.new('RGB', size, color2)
    mask = Image.new('L', size)
    for y in range(size[1]):
        for x in range(size[0]):
            mask.putpixel((x, y), int(255 * (y / size[1])))
    base.paste(top, (0, 0), mask)
    return base

def draw_text_centered(draw, text, font, y, width, color=(255, 255, 255)):
    """Draw text centered horizontally."""
    # Use textbbox instead of deprecated textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) / 2, y), text, font=font, fill=color)

def generate_pin(title, category, output_path):
    """Generate a vertical Pinterest Pin (1000x1500)."""
    width, height = 1000, 1500
    img = create_gradient((width, height), (30, 30, 50), (10, 10, 15))
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fallback to default
    try:
        font_main = ImageFont.truetype("arial.ttf", 80)
        font_sub = ImageFont.truetype("arial.ttf", 40)
        font_logo = ImageFont.truetype("arial.ttf", 60)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_logo = ImageFont.load_default()

    # Draw Logo/Site Name
    draw_text_centered(draw, "⚡ " + SITE_NAME, font_logo, 100, width, (0, 200, 255))
    
    # Draw "FREE API" Badge
    draw.rectangle([400, 250, 600, 310], fill=(0, 200, 100))
    draw_text_centered(draw, "FREE API", font_sub, 260, width, (255, 255, 255))

    # Draw Category
    draw_text_centered(draw, category.upper(), font_sub, 600, width, (150, 150, 150))
    
    # Draw Title (Wrap if too long)
    words = title.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 15:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    
    y_start = 700
    for line in lines[:3]:
        draw_text_centered(draw, line, font_main, y_start, width)
        y_start += 100

    # Save
    ensure_dir(output_path.parent)
    img.save(output_path, quality=90)

def generate_og(title, category, output_path):
    """Generate a horizontal OG Card (1200x630)."""
    width, height = 1200, 630
    img = create_gradient((width, height), (20, 20, 30), (40, 40, 60))
    draw = ImageDraw.Draw(img)
    
    try:
        font_main = ImageFont.truetype("arial.ttf", 70)
        font_sub = ImageFont.truetype("arial.ttf", 35)
    except:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    draw_text_centered(draw, SITE_NAME, font_sub, 50, width, (0, 200, 255))
    draw_text_centered(draw, title, font_main, 250, width)
    draw_text_centered(draw, f"The Best Free {category} APIs", font_sub, 400, width, (180, 180, 180))
    
    ensure_dir(output_path.parent)
    img.save(output_path, quality=85)

def main():
    print("🎨 Generating Social Assets...")
    items = load_database()
    social_dir = DIST_DIR / "images" / "social"
    ensure_dir(social_dir)

    # Generate for Index
    generate_pin("Discover Global Tools", "Directory", social_dir / "pin-index.png")
    generate_og("The Ultimate Tool Directory", "Global", social_dir / "og-index.png")

    # Generate for Items
    count = 0
    categories = {}
    for item in items:
        slug = item['slug']
        generate_pin(item['title'], item['category'], social_dir / f"pin-{slug}.png")
        generate_og(item['title'], item['category'], social_dir / f"og-{slug}.png")
        count += 1
        
        # Track categories for listicle images
        cat = item['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
        
        if count % 20 == 0:
            print(f"  ✓ Processed {count} items...")

    # Generate for Listicles
    print("🎨 Generating Listicle Assets...")
    for name, cat_items in categories.items():
        if len(cat_items) < 3:
            continue
        cat_slug = slugify(name)
        generate_pin(f"Top 10 {name} APIs", name, social_dir / f"pin-best-{cat_slug}.png")
        generate_og(f"Best {name} APIs", name, social_dir / f"og-best-{cat_slug}.png")

    print(f"✅ Generated social assets in {social_dir}")

if __name__ == "__main__":
    main()
