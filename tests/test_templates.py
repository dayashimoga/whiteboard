"""Tests for Jinja2 template rendering."""
from pathlib import Path
from unittest.mock import patch

import pytest
from jinja2 import Environment, FileSystemLoader

from scripts.utils import slugify, truncate

ROOT_DIR = Path(__file__).resolve().parent.parent

@pytest.fixture
def real_env():
    """Create Jinja2 env from the actual project templates."""
    # Always use quickutils-master templates — other projects (price-comparator,
    # market-digest) are standalone HTML/JS apps without Jinja2 templates.
    master_templates = ROOT_DIR / "projects" / "quickutils-master" / "src" / "templates"
    if not master_templates.exists():
        # CI fallback: if running inside a distributed repo, try src/templates
        master_templates = ROOT_DIR / "src" / "templates"
    if not master_templates.exists():
        pytest.skip(f"Templates directory not found at {master_templates}. "
                    "Skipping template tests (likely a pure HTML/JS project).")

    env = Environment(
        loader=FileSystemLoader(str(master_templates)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["slugify"] = slugify
    env.filters["truncate_text"] = truncate
    env.globals.update({
        "site_name": "Test Site",
        "site_url": "https://test.com",
        "site_description": "Test description",
        "build_date": "2025-01-01",
        "current_year": 2025,
        "ga_measurement_id": "G-TEST",
        "adsense_publisher_id": "ca-pub-TEST",
        "amazon_affiliate_tag": "test-20",
        "enable_adsense": True,
        "enable_amazon": True,
        "enable_pinterest": True,
        "google_site_verification": "google-test",
        "pinterest_domain_verify": "c816c2b41079835efd234cb5afef59bf",
        "project_type": "master",
        "site_type": "Tools",
        "social_image_url": "https://test.com/social.png",
    })
    return env


class TestBaseTemplate:
    """Test the base template."""

    def test_renders_title(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test Title",
            page_description="Test desc",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert "<title>Test Title</title>" in html

    def test_contains_meta_description(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="My description",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert 'content="My description"' in html

    def test_contains_ga_script(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert "G-TEST" in html

    def test_contains_adsense(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert "ca-pub-TEST" in html

    def test_contains_open_graph(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="OG Test",
            page_description="OG desc",
            page_url="https://test.com/og",
            canonical_url="https://test.com/og",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert 'property="og:title"' in html
        assert 'property="og:description"' in html

    def test_contains_pinterest_verify(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert 'name="p:domain_verify"' in html
        assert 'content="c816c2b41079835efd234cb5afef59bf"' in html


class TestItemTemplate:
    """Test the item detail template."""

    def test_renders_item_data(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        item = sample_items[0]
        html = tpl.render(
            item=item,
            related_items=sample_items[1:2],
            page_title=f"{item['title']} | Test Site",
            page_description=item["description"],
            page_url=f"https://test.com/api/{item['slug']}.html",
            canonical_url=f"https://test.com/api/{item['slug']}.html",
        )
        assert item["title"] in html
        assert item["description"] in html

    def test_contains_json_ld(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        item = sample_items[0]
        html = tpl.render(
            item=item,
            related_items=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "application/ld+json" in html
        assert "BreadcrumbList" in html

    def test_contains_breadcrumb(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        item = sample_items[0]
        html = tpl.render(
            item=item,
            related_items=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "breadcrumb" in html.lower()

    def test_contains_ad_slots(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        item = sample_items[0]
        html = tpl.render(
            item=item,
            related_items=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "adsbygoogle" in html

    def test_shows_related_items(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        html = tpl.render(
            item=sample_items[0],
            related_items=[sample_items[1]],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert sample_items[1]["title"] in html


class TestCategoryTemplate:
    """Test the category listing template."""

    def test_renders_category(self, real_env, sample_items):
        tpl = real_env.get_template("category.html")
        all_cats = [{"name": "Animals", "slug": "animals", "count": 2}]
        html = tpl.render(
            category_name="Animals",
            category_slug="animals",
            items=sample_items[:2],
            item_count=2,
            all_categories=all_cats,
            page_title="Animals APIs",
            page_description="Browse animals APIs",
            page_url="https://test.com/category/animals.html",
            canonical_url="https://test.com/category/animals.html",
        )
        assert "Animals" in html
        assert "Dog API" in html

    def test_contains_search_filter(self, real_env, sample_items):
        tpl = real_env.get_template("category.html")
        html = tpl.render(
            category_name="Animals",
            category_slug="animals",
            items=sample_items[:2],
            item_count=2,
            all_categories=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "category-search" in html


class TestErrorTemplate:
    """Test the 404 template."""

    def test_renders_404(self, real_env):
        tpl = real_env.get_template("404.html")
        html = tpl.render(
            page_title="Not Found",
            page_description="Page not found",
            page_url="https://test.com/404",
            canonical_url="https://test.com",
        )
        assert "404" in html
        assert "Not Found" in html


class TestAmazonAffiliateBooks:
    """Test Amazon affiliate book recommendations in item template."""

    def test_shows_book_links(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        books = [
            {"title": "Test Book", "author": "Test Author", "url": "https://www.amazon.com/dp/1234?tag=test-20"},
        ]
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=books,
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "Test Book" in html
        assert "Test Author" in html
        assert "amazon.com/dp/1234" in html

    def test_shows_affiliate_disclosure(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        books = [
            {"title": "Book", "author": "Author", "url": "https://amazon.com/dp/X?tag=t"},
        ]
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=books,
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "Amazon Associate" in html

    def test_no_books_section_without_data(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            enable_amazon=True,
        )
        assert "sidebar-books" not in html

    def test_multiple_books_rendered(self, real_env, sample_items):
        tpl = real_env.get_template("item.html")
        books = [
            {"title": "Book One", "author": "Author A", "url": "https://amazon.com/dp/A"},
            {"title": "Book Two", "author": "Author B", "url": "https://amazon.com/dp/B"},
        ]
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=books,
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
        )
        assert "Book One" in html
        assert "Book Two" in html


class TestAdSensePlaceholder:
    """Test AdSense conditional rendering."""

    def test_shows_placeholder_when_unconfigured(self, real_env, sample_items):
        """When adsense_publisher_id is the default placeholder, show ad-placeholder."""
        real_env.globals["adsense_publisher_id"] = "ca-pub-XXXXXXXXXX"
        tpl = real_env.get_template("item.html")
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
        )
        assert "ad-placeholder" in html
        assert "adsbygoogle" not in html
        # Restore
        real_env.globals["adsense_publisher_id"] = "ca-pub-TEST"

    def test_shows_real_ads_when_configured(self, real_env, sample_items):
        """When adsense_publisher_id is a real ID, show real ad code."""
        tpl = real_env.get_template("item.html")
        html = tpl.render(
            item=sample_items[0],
            related_items=[],
            recommended_books=[],
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
        )
        assert "adsbygoogle" in html
        assert "ca-pub-TEST" in html


class TestWorldClock:
    """Test world clock widget in base template."""

    def test_world_clock_present(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert "world-clock" in html
        assert "clock-time" in html

    def test_ten_timezone_cities(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        for city in ["New York", "London", "Dubai", "Mumbai", "Singapore",
                      "Tokyo", "Sydney"]:
            assert city in html, f"Missing city: {city}"

    def test_time_converter_present(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        assert "time-converter" in html
        assert "converter-datetime" in html
        assert "converter-from-tz" in html
        assert "converter-to-tz" in html
        assert "converter-from-display" in html
        assert "converter-to-display" in html
        assert "converter-now-btn" in html

    def test_converter_has_from_to_selectors(self, real_env):
        tpl = real_env.get_template("index.html")
        html = tpl.render(
            page_title="Test",
            page_description="Test",
            page_url="https://test.com",
            canonical_url="https://test.com",
            categories=[],
            featured_items=[],
            total_categories=0,
            enable_pinterest=True,
        )
        # Check that both From and To selectors have timezone options
        assert "My Local Time" in html  # LOCAL option in from-tz
        assert "datetime-local" in html  # Date/time picker input
        assert "Use Current Time" in html  # Now button


