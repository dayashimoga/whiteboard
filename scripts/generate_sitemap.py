"""
Sitemap Generator for the Programmatic SEO Directory.

Walks the dist/ directory and generates a valid XML sitemap
containing URLs for every generated page.
"""
import io
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

# Ensure project root is in sys.path for Cloudflare Pages environment
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import DIST_DIR, SITE_URL, ensure_dir


def collect_pages(dist_dir: Path = None) -> list:
    """Walk the dist directory and collect all HTML file paths.

    Args:
        dist_dir: Path to the dist directory. Defaults to DIST_DIR.

    Returns:
        List of relative paths (e.g., 'api/dog-api.html', 'index.html').
    """
    if dist_dir is None:
        dist_dir = DIST_DIR

    pages = []
    for root, dirs, files in os.walk(dist_dir):
        for f in sorted(files):
            if f.endswith(".html") and f != "404.html":
                rel_path = os.path.relpath(
                    os.path.join(root, f), dist_dir
                ).replace("\\", "/")
                pages.append(rel_path)

    return sorted(pages)


def get_priority(page: str) -> str:
    """Determine the sitemap priority based on page type.

    Args:
        page: Relative path to the page.

    Returns:
        Priority string (0.0 to 1.0).
    """
    if page == "index.html":
        return "1.0"
    elif page.startswith("category/"):
        return "0.8"
    elif page.startswith("best/"):
        return "0.7"
    elif page.startswith("item/"):
        return "0.6"
    else:
        return "0.5"


def get_changefreq(page: str) -> str:
    """Determine the change frequency based on page type.

    Args:
        page: Relative path to the page.

    Returns:
        Change frequency string.
    """
    if page == "index.html":
        return "weekly"
    elif page.startswith("category/"):
        return "weekly"
    elif page.startswith("best/"):
        return "weekly"
    else:
        return "monthly"


def build_sitemap_xml(pages: list, site_url: str = None) -> str:
    """Build a sitemap XML string from a list of pages.

    Args:
        pages: List of relative paths to HTML files.
        site_url: Base URL. Defaults to SITE_URL.

    Returns:
        Valid XML sitemap string.
    """
    if site_url is None:
        site_url = SITE_URL

    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for page in pages:
        url_elem = SubElement(urlset, "url")

        # Build the full URL
        if page == "index.html":
            full_url = f"{site_url}/"
        else:
            full_url = f"{site_url}/{page}"

        loc = SubElement(url_elem, "loc")
        loc.text = full_url

        lastmod_elem = SubElement(url_elem, "lastmod")
        lastmod_elem.text = lastmod

        changefreq = SubElement(url_elem, "changefreq")
        changefreq.text = get_changefreq(page)

        priority = SubElement(url_elem, "priority")
        priority.text = get_priority(page)

    # Pretty-print
    indent(urlset, space="  ")

    # Convert to string
    tree = ElementTree(urlset)

    output = io.BytesIO()
    tree.write(output, encoding="UTF-8", xml_declaration=True)
    return output.getvalue().decode("utf-8")


def build_robots_txt(site_url: str = None) -> str:
    """Generate a robots.txt file content.

    Args:
        site_url: Base URL. Defaults to SITE_URL.

    Returns:
        robots.txt content string.
    """
    if site_url is None:
        site_url = SITE_URL

    return (
        f"User-agent: *\n"
        f"Allow: /\n"
        f"\n"
        f"Sitemap: {site_url}/sitemap.xml\n"
    )


def generate_sitemap(dist_dir: Path = None, site_url: str = None):
    """Main entry point: collect pages and generate sitemap.xml + robots.txt.

    Args:
        dist_dir: Path to dist directory. Defaults to DIST_DIR.
        site_url: Base URL. Defaults to SITE_URL.
    """
    if dist_dir is None:
        dist_dir = DIST_DIR
    if site_url is None:
        site_url = SITE_URL

    print("🗺️  Generating sitemap...")

    pages = collect_pages(dist_dir)
    if not pages:
        print("  ✗ No pages found in dist/. Aborting sitemap generation.")
        return

    # Generate sitemap.xml
    sitemap_xml = build_sitemap_xml(pages, site_url)
    sitemap_path = dist_dir / "sitemap.xml"
    sitemap_path.write_text(sitemap_xml, encoding="utf-8")
    print(f"  ✓ Generated sitemap.xml with {len(pages)} URLs")

    # Generate robots.txt if it doesn't exist
    robots_path = dist_dir / "robots.txt"
    if not robots_path.exists():
        robots_txt = build_robots_txt(site_url)
        robots_path.write_text(robots_txt, encoding="utf-8")
        print("  ✓ Generated robots.txt")
    else:
        print("  ℹ robots.txt already exists, skipping.")

    print("✅ Sitemap generation complete.")


def main():
    generate_sitemap()


if __name__ == "__main__":
    main()
