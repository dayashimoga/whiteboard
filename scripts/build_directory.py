"""
Static Site Generator for the Programmatic SEO Directory.

Reads data/database.json, renders Jinja2 templates, and outputs
thousands of static HTML pages into dist/.
"""
import json
import os
import re
import shutil
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is in sys.path for Cloudflare Pages environment
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jinja2 import Environment, FileSystemLoader

from scripts.utils import (
    ADSENSE_PUBLISHER_ID,
    AMAZON_AFFILIATE_TAG,
    DIST_DIR,
    ENABLE_ADSENSE,
    ENABLE_AMAZON,
    ENABLE_PINTEREST,
    GA_MEASUREMENT_ID,
    PROJECT_ROOT,
    SITE_DESCRIPTION,
    SITE_NAME,
    SITE_URL,
    SRC_DIR,
    TEMPLATES_DIR,
    ensure_dir,
    get_categories,
    GOOGLE_SITE_VERIFICATION,
    load_database,
    load_network_links,
    PINTEREST_DOMAIN_VERIFY,
    PROJECT_TYPE,
    SITE_TYPE,
    slugify,
    truncate,
)

# Amazon Affiliate tag
AMAZON_TAG = AMAZON_AFFILIATE_TAG

# Curated book recommendations per category (Amazon affiliate links)
BOOK_RECOMMENDATIONS = {
    "Development": [
        {"title": "Clean Code", "author": "Robert C. Martin", "asin": "0132350882"},
        {"title": "The Pragmatic Programmer", "author": "David Thomas & Andrew Hunt", "asin": "0135957052"},
    ],
    "Science": [
        {"title": "Python for Data Analysis", "author": "Wes McKinney", "asin": "109810403X"},
        {"title": "Automate the Boring Stuff with Python", "author": "Al Sweigart", "asin": "1593279922"},
    ],
    "Finance": [
        {"title": "Python for Finance", "author": "Yves Hilpisch", "asin": "1492024333"},
        {"title": "The Intelligent Investor", "author": "Benjamin Graham", "asin": "0060555661"},
    ],
    "Games": [
        {"title": "Game Programming Patterns", "author": "Robert Nystrom", "asin": "0990582906"},
        {"title": "Invent Your Own Computer Games with Python", "author": "Al Sweigart", "asin": "1593277954"},
    ],
    "Weather": [
        {"title": "Python Crash Course", "author": "Eric Matthes", "asin": "1718502702"},
        {"title": "Fluent Python", "author": "Luciano Ramalho", "asin": "1492056359"},
    ],
    "Music": [
        {"title": "Music and Technology", "author": "Julio d'Escrivan", "asin": "1501356860"},
    ],
    "Social": [
        {"title": "APIs: A Strategy Guide", "author": "Daniel Jacobson", "asin": "1449308929"},
    ],
    "Health": [
        {"title": "Python for Biologists", "author": "Martin Jones", "asin": "1492346136"},
        {"title": "Health Informatics", "author": "Ramona Nelson", "asin": "0323402313"},
    ],
    "Sports": [
        {"title": "Moneyball", "author": "Michael Lewis", "asin": "0393324818"},
        {"title": "Analyzing Baseball Data with R", "author": "Max Marchi", "asin": "0367233517"},
    ],
    "Transportation": [
        {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "asin": "1449373321"},
    ],
    "Photography": [
        {"title": "Understanding Exposure", "author": "Bryan Peterson", "asin": "1607748509"},
    ],
    "Movies & TV": [
        {"title": "Web Scraping with Python", "author": "Ryan Mitchell", "asin": "1491985577"},
    ],
    "Cloud & DevOps": [
        {"title": "The Phoenix Project", "author": "Gene Kim", "asin": "1942788290"},
        {"title": "Docker Deep Dive", "author": "Nigel Poulton", "asin": "1916585256"},
    ],
    "Machine Learning": [
        {"title": "Hands-On Machine Learning", "author": "Aurélien Géron", "asin": "1098125975"},
        {"title": "Deep Learning with Python", "author": "François Chollet", "asin": "1617296864"},
    ],
    "Cryptocurrency": [
        {"title": "Mastering Bitcoin", "author": "Andreas Antonopoulos", "asin": "1491954388"},
        {"title": "The Bitcoin Standard", "author": "Saifedean Ammous", "asin": "1119473861"},
    ],
    "Calendar & Time": [
        {"title": "Python Crash Course", "author": "Eric Matthes", "asin": "1718502702"},
    ],
    "Education": [
        {"title": "Learning Python", "author": "Mark Lutz", "asin": "1449355730"},
    ],
    "Email & Communication": [
        {"title": "APIs: A Strategy Guide", "author": "Daniel Jacobson", "asin": "1449308929"},
    ],
    "Security": [
        {"title": "Black Hat Python", "author": "Justin Seitz", "asin": "1718501129"},
        {"title": "The Web Application Hacker's Handbook", "author": "Dafydd Stuttard", "asin": "1118026470"},
    ],
    "Government": [
        {"title": "Open Data Now", "author": "Joel Gurin", "asin": "0071829776"},
    ],
    "Environment": [
        {"title": "Python for Data Analysis", "author": "Wes McKinney", "asin": "109810403X"},
    ],
    "Anime & Manga": [
        {"title": "The Anime Art Academy", "author": "Anime Art Academy", "asin": "B0C9ZPRW1C"},
    ],
    "Utilities": [
        {"title": "Designing Web APIs", "author": "Brenda Jin", "asin": "1492026921"},
    ],
    "Vehicles": [
        {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "asin": "1449373321"},
    ],
    "Open Data": [
        {"title": "Open Data Now", "author": "Joel Gurin", "asin": "0071829776"},
    ],
    "Online Courses": [
        {"title": "Ultralearning", "author": "Scott Young", "asin": "006285268X"},
        {"title": "Make It Stick", "author": "Peter C. Brown", "asin": "0674729013"},
    ],
    "Productivity": [
        {"title": "Getting Things Done", "author": "David Allen", "asin": "0143126563"},
        {"title": "Atomic Habits", "author": "James Clear", "asin": "0735211299"},
    ],
    "Student Essentials": [
        {"title": "A Mind for Numbers", "author": "Barbara Oakley", "asin": "039916524X"},
        {"title": "How to Become a Straight-A Student", "author": "Cal Newport", "asin": "0767922719"},
    ],
}

# Dynamic Niche Titles for Index.html
HERO_TITLES = {
    "apistatus": "Track <span class='gradient-text'>API Status Pages</span>",
    "boilerplates": "Launch Faster with <span class='gradient-text'>Open-Source Boilerplates</span>",
    "cheatsheets": "Master Coding with <span class='gradient-text'>Dev Cheatsheets</span>",
    "dailyfacts": "Learn Something New with <span class='gradient-text'>Daily Facts</span>",
    "datasets": "Discover High-Quality <span class='gradient-text'>Open Datasets</span>",
    "jobs": "Find the Best <span class='gradient-text'>Tech Jobs</span>",
    "market": "Get the Latest <span class='gradient-text'>Market Digest</span>",
    "opensource": "Explore the Best <span class='gradient-text'>Open Source Projects</span>",
    "prices": "Compare <span class='gradient-text'>Software & Tech Prices</span>",
    "prompts": "Optimize AI with <span class='gradient-text'>Prompt Templates</span>",
    "master": "Discover <span class='gradient-text'>Free & Open APIs</span>",
    "directory": "Discover <span class='gradient-text'>Free & Open APIs</span>",
    "tools": "Boost Productivity with <span class='gradient-text'>Free Dev Tools</span>",
}

RESOURCE_NAMES = {
    "apistatus": "API status pages",
    "boilerplates": "boilerplates",
    "cheatsheets": "cheatsheets",
    "dailyfacts": "daily facts",
    "datasets": "datasets",
    "jobs": "job listings",
    "market": "market updates",
    "opensource": "open-source projects",
    "prices": "pricing pages",
    "prompts": "AI prompts",
    "master": "APIs",
    "directory": "APIs",
    "tools": "developer tools",
}

# Default books for categories without specific recommendations
DEFAULT_BOOKS = [
    {"title": "Designing Web APIs", "author": "Brenda Jin", "asin": "1492026921"},
    {"title": "RESTful Web APIs", "author": "Leonard Richardson", "asin": "1449358063"},
]

# Try HTML minification, but don't fail if not available
try:
    import htmlmin

    def minify_html(html: str) -> str:
        try:
            return htmlmin.minify(
                html,
                remove_comments=True,
                remove_empty_space=True,
                reduce_boolean_attributes=True,
            )
        except Exception as e:
            print(f"  ⚠️ Minification failed: {e}")
            return html
except ImportError:
    def minify_html(html: str) -> str:
        return html

def minify_css(css: str) -> str:
    css = re.sub(r'/\*[\s\S]*?\*/', '', css)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([\{\}\:\;\,\>])\s*', r'\1', css)
    return css.strip()

def minify_js(js: str) -> str:
    js = re.sub(r'//.*', '', js)
    js = re.sub(r'/\*[\s\S]*?\*/', '', js)
    js = re.sub(r'\s+', ' ', js)
    return js.strip()
def create_jinja_env() -> Environment:
    """Create and configure the Jinja2 template environment."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters
    env.filters["slugify"] = slugify
    env.filters["truncate_text"] = truncate

    # Register global variables
    env.globals.update(
        {
            "site_name": SITE_NAME,
            "site_url": SITE_URL,
            "site_description": SITE_DESCRIPTION,
            "build_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "current_year": datetime.now(timezone.utc).year,
            "ga_measurement_id": GA_MEASUREMENT_ID,
            "adsense_publisher_id": ADSENSE_PUBLISHER_ID,
            "amazon_affiliate_tag": AMAZON_TAG,
            "enable_adsense": ENABLE_ADSENSE,
            "enable_amazon": ENABLE_AMAZON,
            "enable_pinterest": ENABLE_PINTEREST,
            "google_site_verification": GOOGLE_SITE_VERIFICATION,
            "pinterest_domain_verify": PINTEREST_DOMAIN_VERIFY,
            "project_type": PROJECT_TYPE,
            "site_type": SITE_TYPE,
            "network_links": load_network_links(),
        }
    )

    return env


def copy_static_assets():
    """Copy static assets (CSS, JS, images, ads.txt, robots.txt) to dist/."""
    asset_dirs = ["css", "js", "images"]

    # Ensure we use absolute paths resolved relative to the actual project root where the script runs
    absolute_src = Path(SRC_DIR).resolve()
    absolute_dist = Path(DIST_DIR).resolve()

    for asset_dir in asset_dirs:
        src = absolute_src / asset_dir
        dst = absolute_dist / asset_dir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    # Copy root-level files
    for filename in ["_headers", "_redirects"]:
        src_file = absolute_src / filename
        if src_file.exists():
            shutil.copy2(src_file, absolute_dist / filename)

    # robots.txt handling
    src_robots = absolute_src / "robots.txt"
    robots_path = absolute_dist / "robots.txt"
    if src_robots.exists():
        shutil.copy2(src_robots, robots_path)
        # Ensure Sitemap link is present
        content = robots_path.read_text(encoding="utf-8")
        if "Sitemap:" not in content:
            with open(robots_path, "a", encoding="utf-8") as f:
                f.write(f"\nSitemap: {SITE_URL}/sitemap.xml\n")
    else:
        robots_content = f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n"
        robots_path.write_text(robots_content, encoding="utf-8")

    # ads.txt handling
    src_ads = absolute_src / "ads.txt"
    ads_txt_path = absolute_dist / "ads.txt"
    if src_ads.exists():
        shutil.copy2(src_ads, ads_txt_path)
    elif ENABLE_ADSENSE and ADSENSE_PUBLISHER_ID:
        publisher_id = ADSENSE_PUBLISHER_ID.replace("ca-pub-", "")
        ads_txt_content = f"google.com, pub-{publisher_id}, DIRECT, f08c47fec0942fa0\n"
        ads_txt_path.write_text(ads_txt_content, encoding="utf-8")

    # Automatically generate HTML verification file
    if GOOGLE_SITE_VERIFICATION:
        verify_path = absolute_dist / f"{GOOGLE_SITE_VERIFICATION}.html"
        verify_content = f"google-site-verification: {GOOGLE_SITE_VERIFICATION}.html"
        verify_path.write_text(verify_content, encoding="utf-8")

    # Optimize CSS and JS (Minification)
    for ext, minify_fn in [('.css', minify_css), ('.js', minify_js)]:
        for p in absolute_dist.rglob(f"*{ext}"):
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8")
                    p.write_text(minify_fn(content), encoding="utf-8")
                except Exception as e:
                    print(f"  ⚠️ Failed to minify {p.name}: {e}")



def optimize_images():
    """Optimize images in the dist/images directory using Pillow."""
    images_dir = DIST_DIR / "images"
    if not images_dir.exists():
        return

    try:
        from PIL import Image
    except ImportError:
        print("  ⚠️ Pillow not installed. Skipping image optimization.")
        return

    print("  🖼 Optimizing images...")
    processed_count = 0
    total_saved = 0

    for img_path in images_dir.glob("*"):
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                original_size = img_path.stat().st_size
                with Image.open(img_path) as img:
                    # Keep original format
                    fmt = img.format
                    
                    if fmt == "PNG":
                        # Optimize PNG
                        img.save(img_path, format=fmt, optimize=True)
                    elif fmt in ["JPEG", "JPG"]:
                        # Optimize JPEG/JPG
                        img.save(img_path, format=fmt, quality=85, optimize=True)
                    else:
                        # Other formats (WebP, etc.)
                        img.save(img_path, format=fmt, optimize=True)
                        
                    # Also save as WebP
                    webp_path = img_path.with_suffix('.webp')
                    img.save(webp_path, format="WEBP", quality=85, optimize=True)
                
                new_size = img_path.stat().st_size
                saved = original_size - new_size
                if saved > 0:
                    total_saved += saved
                    processed_count += 1
            except Exception as e:
                print(f"    ✗ Failed to optimize {img_path.name}: {e}")

    if processed_count > 0:
        print(f"    ✓ Optimized {processed_count} images (Saved {total_saved / 1024:.1f} KB)")

def _escape_xml(text: str) -> str:
    """Escape special characters for safe XML/RSS output."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_breadcrumb_schema(crumbs: list) -> dict:
    """Build a BreadcrumbList JSON-LD schema for rich Google snippets.

    Args:
        crumbs: List of (name, url) tuples representing the breadcrumb trail.

    Returns:
        JSON-LD dict for a BreadcrumbList.
    """
    items_list = []
    for i, (name, url) in enumerate(crumbs, start=1):
        items_list.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": url,
        })
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": items_list,
    }


def extract_keywords(text):
    words = re.findall(r'\w+', str(text).lower())
    stopwords = {"and", "the", "a", "an", "is", "for", "to", "of", "in", "it", "with", "as", "on", "this", "that"}
    return set(w for w in words if len(w) > 3 and w not in stopwords)

def build_item_pages(env: Environment, items: list, categories: dict):
    """Generate individual item pages.

    Args:
        env: Jinja2 environment.
        items: All items from the database.
        categories: Items grouped by category.
    """
    template = env.get_template("item.html")
    items_dir = DIST_DIR / "item"
    ensure_dir(items_dir)
    
    # Precompute keywords for TF-IDF cross-linking logic
    item_keywords = {i["slug"]: extract_keywords(i.get("title", "") + " " + i.get("description", "")) for i in items}

    for item in items:
        if "auth" not in item:
            item["auth"] = "None"
            
        # Algorithmic Cross-Linking logic (TF-IDF approximation via Jaccard-like tag overlap + category boost)
        item_kws = item_keywords[item["slug"]]
        scored_items = []
        for other in items:
            if other["slug"] == item["slug"]: continue
            score = 0
            if other["category"] == item["category"]:
                score += 5
            other_kws = item_keywords[other["slug"]]
            score += len(item_kws.intersection(other_kws))
            if score > 0:
                scored_items.append((score, other))
        
        scored_items.sort(key=lambda x: x[0], reverse=True)
        related = [i[1] for i in scored_items[:6]]

        # Incremental Builds Logic
        item_data_str = json.dumps({"item": item, "related": [r["slug"] for r in related]}, sort_keys=True)
        content_hash = hashlib.md5(item_data_str.encode('utf-8')).hexdigest()
        output_path = items_dir / f"{item['slug']}.html"
        
        if output_path.exists():
            try:
                existing_html = output_path.read_text(encoding="utf-8")
                if f"<!-- hash:{content_hash} -->" in existing_html[:100]:
                    continue
            except Exception:
                pass

        # Get book recommendations for this category
        raw_books = BOOK_RECOMMENDATIONS.get(item["category"], DEFAULT_BOOKS)
        books = [
            {
                "title": b["title"],
                "author": b["author"],
                "url": f"https://www.amazon.com/dp/{b['asin']}?tag={AMAZON_TAG}",
            }
            for b in raw_books
        ]

        # Breadcrumb: Home > Category > Item
        cat_slug = slugify(item["category"])
        breadcrumb = build_breadcrumb_schema([
            (SITE_NAME, SITE_URL),
            (item["category"], f"{SITE_URL}/category/{cat_slug}.html"),
            (item["title"], f"{SITE_URL}/item/{item['slug']}.html"),
        ])

        html = template.render(
            item=item,
            related_items=related,
            recommended_books=books,
            page_title=f"{item['title']} - Free API | {SITE_NAME}",
            page_description=truncate(item["description"]),
            page_url=f"{SITE_URL}/item/{item['slug']}.html",
            canonical_url=f"{SITE_URL}/item/{item['slug']}.html",
            # Social Image Metadata
            og_image=f"{SITE_URL}/images/social/og-{item['slug']}.png",
            pinterest_image=f"{SITE_URL}/images/social/pin-{item['slug']}.png",
            # Breadcrumb JSON-LD for rich snippets
            breadcrumb_schema=breadcrumb,
            # Automated Schema.org (SoftwareApplication)
            item_schema={
                "@context": "https://schema.org",
                "@type": "SoftwareApplication" if PROJECT_TYPE in ["master", "directory", "tools"] else "WebPage",
                "name": item['title'],
                "description": truncate(item["description"]),
                "applicationCategory": item["category"],
                "operatingSystem": "Web",
                "offers": {
                    "@type": "Offer",
                    "price": "0",
                    "priceCurrency": "USD"
                }
            }
        )

        html = f"<!-- hash:{content_hash} -->\n" + html
        output_path.write_text(minify_html(html), encoding="utf-8")

    print(f"  ✓ Generated {len(items)} item pages → dist/item/")


def build_category_pages(env: Environment, categories: dict):
    """Generate category listing pages.

    Args:
        env: Jinja2 environment.
        categories: Items grouped by category.
    """
    template = env.get_template("category.html")
    cat_dir = DIST_DIR / "category"
    ensure_dir(cat_dir)

    all_categories = [
        {"name": name, "slug": slugify(name), "count": len(items)}
        for name, items in categories.items()
    ]

    for name, items in categories.items():
        cat_slug = slugify(name)

        # Breadcrumb: Home > Category
        breadcrumb = build_breadcrumb_schema([
            (SITE_NAME, SITE_URL),
            (name, f"{SITE_URL}/category/{cat_slug}.html"),
        ])

        html = template.render(
            category_name=name,
            category_slug=cat_slug,
            items=items,
            item_count=len(items),
            all_categories=all_categories,
            page_title=f"{name} APIs - Free & Open | {SITE_NAME}",
            page_description=f"Browse {len(items)} free {name} APIs. Find the best open APIs for {name.lower()} development.",
            page_url=f"{SITE_URL}/category/{cat_slug}.html",
            canonical_url=f"{SITE_URL}/category/{cat_slug}.html",
            breadcrumb_schema=breadcrumb,
        )

        output_path = cat_dir / f"{cat_slug}.html"
        output_path.write_text(minify_html(html), encoding="utf-8")

    print(f"  ✓ Generated {len(categories)} category pages → dist/category/")


def build_listicle_pages(env: Environment, categories: dict):
    """Generate programmatic 'Top 10' listicle pages for each category."""
    try:
        template = env.get_template("listicle.html")
    except Exception:
        print("  ⚠️ listicle.html not found. Skipping listicle generation.")
        return

    listicle_dir = DIST_DIR / "best"
    ensure_dir(listicle_dir)

    for name, items in categories.items():
        if len(items) < 3: # Only generate for categories with enough content
            continue
            
        cat_slug = slugify(name)
        
        html = template.render(
            category_name=name,
            category_slug=cat_slug,
            items=items,
            page_title=f"Top 10 Best {name} APIs (Free & Open-Source) | {SITE_NAME}",
            page_description=f"Discover the top 10 best {name.lower()} APIs for your next project. Curated list of free, high-quality {name.lower()} data sources.",
            page_url=f"{SITE_URL}/best/best-{cat_slug}-apis.html",
            canonical_url=f"{SITE_URL}/best/best-{cat_slug}-apis.html",
            # Social Cards
            og_image=f"{SITE_URL}/images/social/og-best-{cat_slug}.png",
            pinterest_image=f"{SITE_URL}/images/social/pin-best-{cat_slug}.png",
        )

        output_path = listicle_dir / f"best-{cat_slug}-apis.html"
        output_path.write_text(minify_html(html), encoding="utf-8")

    print(f"  ✓ Generated listicle pages → dist/best/")


def build_index_page(env: Environment, items: list, categories: dict):
    """Generate the homepage.

    Args:
        env: Jinja2 environment.
        items: All items from the database.
        categories: Items grouped by category.
    """
    template = env.get_template("index.html")

    category_cards = [
        {"name": name, "slug": slugify(name), "count": len(cat_items)}
        for name, cat_items in categories.items()
    ]

    # Pick featured items (first 8 from the database)
    featured = items[:8]

    # Categories context
    hero_title = HERO_TITLES.get(PROJECT_TYPE, "Discover <span class='gradient-text'>Free & Open APIs</span>")
    resource_name = RESOURCE_NAMES.get(PROJECT_TYPE, "APIs")

    html = template.render(
        categories=category_cards,
        featured_items=featured,
        total_apis=len(items),
        total_categories=len(categories),
        page_title=f"{SITE_NAME} — Discover Free & Open APIs",
        page_description=SITE_DESCRIPTION,
        page_url=SITE_URL,
        canonical_url=SITE_URL,
        hero_title=hero_title,
        resource_name=resource_name,
        # Social Presence Metadata
        og_image=f"{SITE_URL}/images/social/og-index.png",
        pinterest_image=f"{SITE_URL}/images/social/pin-index.png",
    )

    output_path = DIST_DIR / "index.html"
    output_path.write_text(minify_html(html), encoding="utf-8")
    print("  ✓ Generated homepage → dist/index.html")


def build_404_page(env: Environment):
    """Generate a custom 404 page."""
    template = env.get_template("404.html")

    html = template.render(
        page_title=f"Page Not Found | {SITE_NAME}",
        page_description="The page you're looking for doesn't exist.",
        page_url=f"{SITE_URL}/404.html",
        canonical_url=SITE_URL,
    )

    output_path = DIST_DIR / "404.html"
    output_path.write_text(minify_html(html), encoding="utf-8")
    print("  ✓ Generated 404 page → dist/404.html")

def build_legal_pages(env: Environment):
    """Generate static legal and info pages."""
    pages = [
        {"file": "privacy.html", "title": f"Privacy Policy | {SITE_NAME}", "desc": "Privacy policy and terms of data usage."},
        {"file": "terms.html", "title": f"Terms of Service | {SITE_NAME}", "desc": "Terms of service and usage guidelines."},
        {"file": "about.html", "title": f"About Us | {SITE_NAME}", "desc": f"About {SITE_NAME}."}
    ]
    
    for page in pages:
        try:
            template = env.get_template(page["file"])
            html = template.render(
                page_title=page["title"],
                page_description=page["desc"],
                page_url=f"{SITE_URL}/{page['file']}",
                canonical_url=f"{SITE_URL}/{page['file']}",
            )
            output_path = DIST_DIR / page["file"]
            output_path.write_text(minify_html(html), encoding="utf-8")
        except Exception as e:
            print(f"  ⚠️ Could not generate {page['file']}: {e}")
            
    print("  ✓ Generated legal pages → dist/")


def build_site(database_path: Path = None):
    """Main build pipeline.

    Args:
        database_path: Optional path to database.json. Defaults to data/database.json.
    """
    print("🔨 Building static directory site...")

    # Load data
    items = load_database(database_path)
    if not items:
        print("  ✗ No items in database. Aborting build.")
        return

    categories = get_categories(items)

    # Clean and create dist directory
    if DIST_DIR.exists():
        # Soft-clean dist directory (leave item/ category/ best/ intact for incremental builds)
        for child in DIST_DIR.iterdir():
            if child.name not in ["item", "category", "best", "images", "css", "js", "social"]:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
    ensure_dir(DIST_DIR)

    # Set up Jinja2
    env = create_jinja_env()

    # Build pages
    build_item_pages(env, items, categories)
    build_category_pages(env, categories)
    build_listicle_pages(env, categories)
    build_index_page(env, items, categories)
    build_404_page(env)
    build_legal_pages(env)

    # Copy static assets
    copy_static_assets()
    

    # Optimize images
    optimize_images()

    # Generate Social Images (Pins/OG Cards)
    try:
        from scripts.generate_social_images import main as gen_social
        gen_social()
    except Exception as e:
        print(f"  ⚠️ Social image generation failed: {e}")
    # Search Index Generation
    search_items = []
    for item in items:
        title = item.get('name', item.get('title', 'Unknown'))
        desc = item.get('description', '')
        cat = item.get('category', '')
        link = f"/item/{item['slug']}.html"
        search_items.append({'title': title, 'description': desc, 'category': cat, 'url': link})
        
    (DIST_DIR / "search.json").write_text(
        json.dumps(search_items, ensure_ascii=False), encoding="utf-8"
    )

    # RSS Feed Generation
    rss_items = []
    for item in items[:20]:
        title = _escape_xml(item.get('name', item.get('title', 'Unknown')))
        desc = _escape_xml(item.get('description', ''))
        link = f"{SITE_URL}/item/{item['slug']}.html"
        rss_items.append({'title': title, 'description': desc, 'link': link})
        
    site_name_esc = _escape_xml(SITE_NAME)
    site_desc_esc = _escape_xml(SITE_DESCRIPTION)
    rss_content = f'''<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{site_name_esc}</title>
  <link>{SITE_URL}</link>
  <description>{site_desc_esc}</description>
'''
    for rss_item in rss_items:
        rss_content += f'''  <item>
    <title>{rss_item['title']}</title>
    <link>{rss_item['link']}</link>
    <description>{rss_item['description']}</description>
    <guid>{rss_item['link']}</guid>
  </item>
'''
    rss_content += '''</channel>
</rss>'''
    (DIST_DIR / "feed.xml").write_text(rss_content, encoding="utf-8")

    print("  ✓ Copied static assets (CSS, JS, images)")

    print(
        f"✅ Build complete: {len(items)} items, {len(categories)} categories, "
        f"{len(items) + len(categories) + 2} total pages."
    )


def main():
    build_site()


if __name__ == "__main__":
    main()
