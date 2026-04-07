"""
Shared test fixtures for the Programmatic SEO Directory test suite.
"""
import json
import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is in sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set PROJECT_TYPE for tests — ensures utils.py resolves to quickutils-master
# in all environments (local, CI, GitHub Actions) instead of detecting wrong project
if "PROJECT_TYPE" not in os.environ:
    os.environ["PROJECT_TYPE"] = "quickutils-master"


@pytest.fixture
def sample_items():
    """A small sample dataset for testing."""
    return [
        {
            "title": "Dog API",
            "description": "Dog facts and images",
            "category": "Animals",
            "url": "https://dog.ceo/dog-api/",
            "auth": "None",
            "https": True,
            "cors": "yes",
            "slug": "dog-api",
            "pricing": "Free",
        },
        {
            "title": "Cat Facts",
            "description": "Random cat facts",
            "category": "Animals",
            "url": "https://catfact.ninja/",
            "auth": "None",
            "https": True,
            "cors": "yes",
            "slug": "cat-facts",
            "pricing": "Free",
        },
        {
            "title": "OpenWeatherMap",
            "description": "Current and forecast weather data with global coverage",
            "category": "Weather",
            "url": "https://openweathermap.org/api",
            "auth": "apiKey",
            "https": True,
            "cors": "yes",
            "slug": "openweathermap",
            "pricing": "Freemium",
        },
        {
            "title": "Alpha Vantage",
            "description": "Real-time and historical stock market data",
            "category": "Finance",
            "url": "https://www.alphavantage.co/",
            "auth": "apiKey",
            "https": True,
            "cors": "unknown",
            "slug": "alpha-vantage",
            "pricing": "Free",
        },
        {
            "title": "Spotify",
            "description": "Music metadata, streaming, and playlist management",
            "category": "Music",
            "url": "https://developer.spotify.com/",
            "auth": "OAuth",
            "https": True,
            "cors": "unknown",
            "slug": "spotify",
            "pricing": "Free",
        },
    ]


@pytest.fixture
def sample_database_path(tmp_path, sample_items):
    """Creates a temporary database.json file with sample data."""
    db_path = tmp_path / "database.json"
    db_path.write_text(json.dumps(sample_items, indent=2), encoding="utf-8")
    return db_path


@pytest.fixture
def sample_raw_api_entries():
    """Raw API entries as returned by the public-apis API."""
    return [
        {
            "API": "Dog API",
            "Description": "Dog facts and images",
            "Auth": "",
            "HTTPS": True,
            "Cors": "yes",
            "Link": "https://dog.ceo/dog-api/",
            "Category": "Animals",
        },
        {
            "API": "Cat Facts",
            "Description": "Random cat facts",
            "Auth": "",
            "HTTPS": True,
            "Cors": "yes",
            "Link": "https://catfact.ninja/",
            "Category": "Animals",
        },
        {
            "API": "OpenWeatherMap",
            "Description": "Weather data",
            "Auth": "apiKey",
            "HTTPS": True,
            "Cors": "yes",
            "Link": "https://openweathermap.org/api",
            "Category": "Weather",
        },
    ]


@pytest.fixture
def templates_dir(tmp_path):
    """Creates a temporary templates directory with minimal templates."""
    tpl_dir = tmp_path / "src" / "templates"
    tpl_dir.mkdir(parents=True)

    # Minimal base template
    base = tpl_dir / "base.html"
    base.write_text(
        '<!DOCTYPE html><html lang="en"><head>'
        "<title>{{ page_title }}</title>"
        '<meta name="description" content="{{ page_description }}">'
        '<link rel="canonical" href="{{ canonical_url }}">'
        "</head><body>"
        "{% block content %}{% endblock %}"
        "</body></html>",
        encoding="utf-8",
    )

    # Index template
    index = tpl_dir / "index.html"
    index.write_text(
        '{% extends "base.html" %}'
        "{% block content %}"
        "<h1>{{ site_name }}</h1>"
        "<p>{{ total_apis }} APIs in {{ total_categories }} categories</p>"
        "{% for cat in categories %}"
        '<a href="/category/{{ cat.slug }}.html">{{ cat.name }} ({{ cat.count }})</a>'
        "{% endfor %}"
        "{% for item in featured_items %}"
        '<a href="/item/{{ item.slug }}.html">{{ item.title }}</a>'
        "{% endfor %}"
        "{% endblock %}",
        encoding="utf-8",
    )
 
    # Item template
    item = tpl_dir / "item.html"
    item.write_text(
        '{% extends "base.html" %}'
        "{% block content %}"
        "<h1>{{ item.title }}</h1>"
        "<p>{{ item.description }}</p>"
        "<p>Category: {{ item.category }}</p>"
        "<p>Auth: {{ item.auth }}</p>"
        '<a href="{{ item.url }}">Visit</a>'
        "{% for rel in related_items %}"
        '<a href="/item/{{ rel.slug }}.html">{{ rel.title }}</a>'
        "{% endfor %}"
        "{% endblock %}",
        encoding="utf-8",
    )

    # Category template
    category = tpl_dir / "category.html"
    category.write_text(
        '{% extends "base.html" %}'
        "{% block content %}"
        "<h1>{{ category_name }}</h1>"
        "<p>{{ item_count }} APIs</p>"
        "{% for item in items %}"
        '<a href="/item/{{ item.slug }}.html">{{ item.title }}</a>'
        "{% endfor %}"
        "{% for cat in all_categories %}"
        '<a href="/category/{{ cat.slug }}.html">{{ cat.name }}</a>'
        "{% endfor %}"
        "{% endblock %}",
        encoding="utf-8",
    )

    # 404 template
    notfound = tpl_dir / "404.html"
    notfound.write_text(
        '{% extends "base.html" %}'
        "{% block content %}"
        "<h1>404</h1><p>Not Found</p>"
        "{% endblock %}",
        encoding="utf-8",
    )

    # Listicle template
    listicle = tpl_dir / "listicle.html"
    listicle.write_text(
        '{% extends "base.html" %}'
        "{% block content %}"
        "<h1>{{ category_name }}</h1>"
        "{% for item in items %}"
        "<div>{{ item.title }}</div>"
        "{% endfor %}"
        "{% endblock %}",
        encoding="utf-8",
    )

    return tpl_dir
