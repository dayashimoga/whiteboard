import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.generate_sitemap import (
    collect_pages,
    get_priority,
    get_changefreq,
    build_sitemap_xml,
    build_robots_txt,
    generate_sitemap,
    main
)

def test_collect_pages(tmp_path):
    (tmp_path / "index.html").touch()
    (tmp_path / "404.html").touch()
    (tmp_path / "category").mkdir()
    (tmp_path / "category" / "test.html").touch()
    
    pages = collect_pages(tmp_path)
    assert len(pages) == 2
    assert "index.html" in pages
    assert "category/test.html" in pages
    assert "404.html" not in pages

def test_get_priority():
    assert get_priority("index.html") == "1.0"
    assert get_priority("category/test") == "0.8"
    assert get_priority("best/test") == "0.7"
    assert get_priority("item/test") == "0.6"
    assert get_priority("other") == "0.5"

def test_get_changefreq():
    assert get_changefreq("index.html") == "weekly"
    assert get_changefreq("category/test") == "weekly"
    assert get_changefreq("best/test") == "weekly"
    assert get_changefreq("item/test") == "monthly"

def test_build_sitemap_xml():
    xml = build_sitemap_xml(["index.html", "category/test.html"], "https://test.com")
    assert "https://test.com/" in xml
    assert "https://test.com/category/test.html" in xml
    assert "<priority>1.0</priority>" in xml
    assert "<changefreq>weekly</changefreq>" in xml
    
    # testing default param
    with patch("scripts.generate_sitemap.SITE_URL", "https://default.com"):
        xml2 = build_sitemap_xml(["index.html"])
        assert "https://default.com/" in xml2

def test_build_robots_txt():
    txt = build_robots_txt("https://test.com")
    assert "Sitemap: https://test.com/sitemap.xml" in txt
    
    with patch("scripts.generate_sitemap.SITE_URL", "https://default.com"):
        txt2 = build_robots_txt()
        assert "Sitemap: https://default.com/sitemap.xml" in txt2

def test_generate_sitemap_success(tmp_path):
    (tmp_path / "index.html").touch()
    generate_sitemap(tmp_path, "https://test.com")
    
    assert (tmp_path / "sitemap.xml").exists()
    assert (tmp_path / "robots.txt").exists()
    
    # run again to hit the "robots.txt already exists" branch
    generate_sitemap(tmp_path, "https://test.com")

def test_generate_sitemap_no_pages(tmp_path):
    generate_sitemap(tmp_path, "https://test.com")
    assert not (tmp_path / "sitemap.xml").exists()

def test_generate_sitemap_defaults(tmp_path):
    (tmp_path / "index.html").touch()
    with patch("scripts.generate_sitemap.DIST_DIR", tmp_path), \
         patch("scripts.generate_sitemap.SITE_URL", "https://def.com"):
        generate_sitemap()
        assert (tmp_path / "sitemap.xml").exists()
        assert "https://def.com/" in (tmp_path / "sitemap.xml").read_text()

@patch("scripts.generate_sitemap.generate_sitemap")
def test_main(mock_gen):
    main()
    mock_gen.assert_called_once()
