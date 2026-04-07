"""Tests for scripts/build_directory.py"""
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.build_directory import (
    build_404_page,
    build_category_pages,
    build_index_page,
    build_item_pages,
    build_site,
    copy_static_assets,
    create_jinja_env,
)
from scripts.utils import get_categories


class TestCreateJinjaEnv:
    """Test Jinja2 environment creation."""

    def test_env_created(self, templates_dir):
        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir):
            env = create_jinja_env()
        assert env is not None
        assert "slugify" in env.filters
        assert "truncate_text" in env.filters

    def test_global_variables(self, templates_dir):
        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir):
            env = create_jinja_env()
        assert "site_name" in env.globals
        assert "site_url" in env.globals
        assert "build_date" in env.globals
        assert "current_year" in env.globals
        assert "ga_measurement_id" in env.globals
        assert "adsense_publisher_id" in env.globals
        assert "amazon_affiliate_tag" in env.globals
        assert "enable_adsense" in env.globals
        assert "google_site_verification" in env.globals


class TestBuildItemPages:
    """Test item page generation."""

    def test_generates_item_files(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_item_pages(env, sample_items, categories)

        item_dir = dist_dir / "item"
        assert item_dir.exists()

        # Check each item has a page
        for item in sample_items:
            page = item_dir / f"{item['slug']}.html"
            assert page.exists(), f"Missing page: {page}"
            content = page.read_text(encoding="utf-8")
            assert item["title"] in content

    def test_item_page_contains_meta(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_item_pages(env, sample_items, categories)

        page = dist_dir / "item" / "dog-api.html"
        content = page.read_text(encoding="utf-8")
        assert "<title>" in content
        # htmlmin may strip attribute quotes, so check for both forms
        assert 'name="description"' in content or 'name=description' in content
        assert 'rel="canonical"' in content or 'rel=canonical' in content

    def test_item_page_has_related_items(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_item_pages(env, sample_items, categories)

        # Dog API is in Animals category, Cat Facts is also in Animals
        page = dist_dir / "item" / "dog-api.html"
        content = page.read_text(encoding="utf-8")
        assert "Cat Facts" in content


class TestBuildCategoryPages:
    """Test category page generation."""

    def test_generates_category_files(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_category_pages(env, categories)

        cat_dir = dist_dir / "category"
        assert cat_dir.exists()
        assert (cat_dir / "animals.html").exists()
        assert (cat_dir / "weather.html").exists()

    def test_category_page_contains_items(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_category_pages(env, categories)

        content = (dist_dir / "category" / "animals.html").read_text(encoding="utf-8")
        assert "Dog API" in content
        assert "Cat Facts" in content


class TestBuildIndexPage:
    """Test homepage generation."""

    def test_generates_index(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_index_page(env, sample_items, categories)

        index = dist_dir / "index.html"
        assert index.exists()

    def test_index_contains_stats(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_index_page(env, sample_items, categories)

        content = (dist_dir / "index.html").read_text(encoding="utf-8")
        assert "5" in content  # total_apis
        assert str(len(categories)) in content

    def test_index_contains_categories(self, tmp_path, templates_dir, sample_items):
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            categories = get_categories(sample_items)
            build_index_page(env, sample_items, categories)

        content = (dist_dir / "index.html").read_text(encoding="utf-8")
        assert "Animals" in content
        assert "Weather" in content


class TestBuild404Page:
    """Test 404 page generation."""

    def test_generates_404(self, tmp_path, templates_dir):
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            env = create_jinja_env()
            build_404_page(env)

        page = dist_dir / "404.html"
        assert page.exists()
        content = page.read_text(encoding="utf-8")
        assert "404" in content


class TestCopyStaticAssets:
    """Test static asset copying."""

    def test_copies_css(self, tmp_path):
        src_dir = tmp_path / "src"
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()

        css_dir = src_dir / "css"
        css_dir.mkdir(parents=True)
        (css_dir / "styles.css").write_text("body{}", encoding="utf-8")

        with patch("scripts.build_directory.SRC_DIR", src_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            copy_static_assets()

        assert (dist_dir / "css" / "styles.css").exists()

    def test_copies_ads_txt(self, tmp_path):
        src_dir = tmp_path / "src"
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        src_dir.mkdir(parents=True)

        (src_dir / "ads.txt").write_text("test", encoding="utf-8")

        with patch("scripts.build_directory.SRC_DIR", src_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            copy_static_assets()

        assert (dist_dir / "ads.txt").exists()

    def test_handles_missing_dirs(self, tmp_path):
        src_dir = tmp_path / "src"
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        src_dir.mkdir(parents=True)

        # Should not raise even with missing css/js/images dirs
        with patch("scripts.build_directory.SRC_DIR", src_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            copy_static_assets()


class TestBuildSite:
    """Test the full build pipeline."""

    def test_full_build(self, tmp_path, templates_dir, sample_database_path):
        dist_dir = tmp_path / "dist"
        src_dir = templates_dir.parent.parent / "src"

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir), \
             patch("scripts.build_directory.SRC_DIR", templates_dir.parent), \
             patch("scripts.generate_social_images.main"), \
             patch("scripts.build_directory.optimize_images"):
            build_site(sample_database_path)

        assert dist_dir.exists()
        assert (dist_dir / "index.html").exists()
        assert (dist_dir / "404.html").exists()
        assert (dist_dir / "feed.xml").exists(), "RSS feed missing"
        assert (dist_dir / "search.json").exists(), "Search index missing"
        assert (dist_dir / "item").is_dir()
        assert (dist_dir / "category").is_dir()

    def test_empty_database(self, tmp_path, templates_dir):
        dist_dir = tmp_path / "dist"
        empty_db = tmp_path / "empty.json"
        empty_db.write_text("[]", encoding="utf-8")

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir), \
             patch("scripts.build_directory.SRC_DIR", templates_dir.parent):
            build_site(empty_db)

        # Should not create dist when database is empty
        assert not (dist_dir / "index.html").exists()

    def test_cleans_old_dist(self, tmp_path, templates_dir, sample_database_path):
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        old_file = dist_dir / "old_file.html"
        old_file.write_text("old", encoding="utf-8")
        # Add a dir to trigger rmtree
        old_dir = dist_dir / "old_dir"
        old_dir.mkdir()

        with patch("scripts.build_directory.TEMPLATES_DIR", templates_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir), \
             patch("scripts.build_directory.SRC_DIR", templates_dir.parent), \
             patch("scripts.generate_social_images.main"), \
             patch("scripts.build_directory.optimize_images"):
            build_site(sample_database_path)

        assert not old_file.exists()
        assert not old_dir.exists()

class TestOptimizeImages:
    """Test image optimization."""

    def test_optimizes_images(self, tmp_path):
        from PIL import Image
        dist_dir = tmp_path / "dist"
        images_dir = dist_dir / "images"
        images_dir.mkdir(parents=True)
        
        # Create dummy images
        img_png = images_dir / "test.png"
        Image.new('RGB', (100, 100), color = 'red').save(img_png)
        
        img_jpg = images_dir / "test.jpg"
        Image.new('RGB', (100, 100), color = 'blue').save(img_jpg, format='JPEG')
        
        with patch("scripts.build_directory.DIST_DIR", dist_dir):
            from scripts.build_directory import optimize_images
            optimize_images()
        
        assert img_png.exists()
        assert img_jpg.exists()

    def test_handles_optimization_error(self, tmp_path):
        dist_dir = tmp_path / "dist"
        images_dir = dist_dir / "images"
        images_dir.mkdir(parents=True)
        (images_dir / "bad.png").write_text("not an image")
        
        with patch("scripts.build_directory.DIST_DIR", dist_dir):
            from scripts.build_directory import optimize_images
            optimize_images() # Should handle exception and continue

class TestMinifyHtml:
    """Test HTML minification."""

    def test_minify_failure_returns_original(self):
        from scripts.build_directory import minify_html
        try:
            import htmlmin
            with patch("scripts.build_directory.htmlmin.minify", side_effect=Exception("Minify error")):
                result = minify_html("<html></html>")
                assert result == "<html></html>"
        except ImportError:
            pytest.skip("htmlmin not installed")

class TestCopyStaticAssetsExtended:
    """Extended tests for static asset copying."""

    def test_cleans_existing_asset_dir(self, tmp_path):
        src_dir = tmp_path / "src"
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        
        # Source asset
        css_src = src_dir / "css"
        css_src.mkdir(parents=True)
        (css_src / "new.css").write_text("new", encoding="utf-8")
        
        # Existing destination asset dir
        css_dst = dist_dir / "css"
        css_dst.mkdir()
        (css_dst / "old.css").write_text("old", encoding="utf-8")
        
        with patch("scripts.build_directory.SRC_DIR", src_dir), \
             patch("scripts.build_directory.DIST_DIR", dist_dir):
            copy_static_assets()
            
        assert (css_dst / "new.css").exists()
        assert not (css_dst / "old.css").exists()
