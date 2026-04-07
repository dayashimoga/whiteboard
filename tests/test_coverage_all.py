"""Comprehensive coverage tests for scripts that need additional branch coverage."""
import sys
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open


def test_build_all_local():
    import pytest
    pytest.importorskip("scripts.build_all_local")
    import scripts.build_all_local
    mock_p = MagicMock()
    mock_p.name = "test-directory"
    (mock_p / "data" / "database.json").exists.return_value = True
    
    with patch("scripts.build_all_local.get_projects", return_value=[mock_p]), \
         patch("subprocess.run") as mock_run:
        scripts.build_all_local.main()
        assert mock_run.called

def test_verify_links_coverage():
    import pytest
    pytest.importorskip("scripts.verify_links_local")
    import scripts.verify_links_local
    with patch("scripts.verify_links_local.verify_links_in_dist") as mock_verify, \
         patch("pathlib.Path.iterdir") as mock_iter:
        mock_verify.return_value = (True, [])
        mock_p = MagicMock()
        mock_p.is_dir.return_value = True
        mock_p.name = "test-directory"
        mock_iter.return_value = [mock_p]
        with patch("sys.exit") as mock_exit:
            scripts.verify_links_local.main()
            mock_exit.assert_not_called()


# --- Coverage tests for generate_social_images.py ---

def test_generate_social_images_functions():
    """Test create_gradient, draw_text_centered, generate_pin, generate_og."""
    from scripts.generate_social_images import (
        create_gradient, draw_text_centered, generate_pin, generate_og
    )
    from PIL import Image, ImageDraw, ImageFont
    
    # Test create_gradient
    img = create_gradient((100, 100), (0, 0, 0), (255, 255, 255))
    assert img.size == (100, 100)
    
    # Test draw_text_centered
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw_text_centered(draw, "Test", font, 10, 100)
    
    # Test generate_pin and generate_og
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pin_path = Path(tmp) / "pin.png"
        og_path = Path(tmp) / "og.png"
        generate_pin("Test Title", "Test Category", pin_path)
        generate_og("Test Title", "Test Category", og_path)
        assert pin_path.exists()
        assert og_path.exists()


def test_generate_social_images_main(tmp_path):
    """Test the main() function with mocked database and paths."""
    import scripts.generate_social_images as gsi
    
    mock_db = [
        {"title": "API 1", "slug": "api-1", "category": "Cat1"},
        {"title": "API 2", "slug": "api-2", "category": "Cat1"},
        {"title": "API 3", "slug": "api-3", "category": "Cat1"},
    ]
    
    with patch.object(gsi, "load_database", return_value=mock_db), \
         patch.object(gsi, "DIST_DIR", tmp_path):
        gsi.main()
    
    social_dir = tmp_path / "images" / "social"
    assert social_dir.exists()
    assert (social_dir / "pin-index.png").exists()
    assert (social_dir / "og-index.png").exists()


# --- Coverage tests for generate_pins.py ---

def test_generate_pins_main():
    """Test generate_pinterest_images function and __main__ guard."""
    from scripts.generate_pins import generate_pinterest_images
    result = generate_pinterest_images()
    assert result is True


# --- Coverage tests for check_links.py ---

def test_check_links_main_with_projects(tmp_path):
    """Cover check_links.py main() with project iteration and report output."""
    import scripts.check_links
    
    # Create a mock project structure with a dist dir
    proj_dir = tmp_path / "projects" / "test-directory" / "dist"
    proj_dir.mkdir(parents=True)
    html_file = proj_dir / "index.html"
    html_file.write_text('<html><body><a href="/item/test.html">Test</a></body></html>')
    
    with patch("scripts.check_links.Path", side_effect=lambda x: Path(x) if isinstance(x, str) else x), \
         patch("sys.exit") as mock_exit:
        
        broken = scripts.check_links.check_links_in_dir(proj_dir)
        # The link to /item/test.html will be broken since it doesn't exist
        assert isinstance(broken, list)


def test_check_links_report_output(tmp_path):
    """Cover the output report writing branch in main()."""
    import scripts.check_links
    
    report_path = tmp_path / "report.md"
    
    # Create a dist dir with valid links only
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    html_file = dist_dir / "index.html"
    html_file.write_text('<html><body><a href="https://example.com">External</a></body></html>')
    
    with patch("sys.exit"):
        scripts.check_links.main(["--output-report", str(report_path)])
    
    # Report should mention no broken links (only external links which are skipped)


def test_check_links_legacy_exports():
    """Cover the legacy export functions for backward compatibility."""
    import asyncio
    from scripts.check_links import check_url, generate_report, main_async
    
    # Test legacy check_url
    loop = asyncio.new_event_loop()
    url, status, _ = loop.run_until_complete(check_url(None, "http://test.com"))
    assert url == "http://test.com"
    assert status is True
    loop.close()
    
    # Test legacy generate_report
    report = generate_report()
    assert report == "Report placeholder"
    
    # Test legacy main_async
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(main_async())
    assert result == (0, 0, 0, [], {})
    loop.close()


# --- Coverage tests for build_directory.py breadcrumb ---

def test_build_breadcrumb_schema():
    """Test the new breadcrumb JSON-LD schema builder."""
    from scripts.build_directory import build_breadcrumb_schema
    
    crumbs = [
        ("Home", "https://example.com"),
        ("Category", "https://example.com/category/test.html"),
        ("Item", "https://example.com/item/test.html"),
    ]
    schema = build_breadcrumb_schema(crumbs)
    
    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "BreadcrumbList"
    assert len(schema["itemListElement"]) == 3
    assert schema["itemListElement"][0]["position"] == 1
    assert schema["itemListElement"][0]["name"] == "Home"
    assert schema["itemListElement"][2]["position"] == 3



# --- Coverage tests for generate_sitemap.py new priorities ---

def test_sitemap_best_page_priority():
    """Test that listicle/best pages get proper priority and frequency."""
    from scripts.generate_sitemap import get_priority, get_changefreq
    
    assert get_priority("best/best-dev-apis.html") == "0.7"
    assert get_changefreq("best/best-dev-apis.html") == "weekly"

# --- Coverage tests for smoke_test.py ---

def test_smoke_test_main_coverage(tmp_path):
    import subprocess
    import sys
    import os
    import pytest
    from pathlib import Path
    
    if not Path("scripts/smoke_test.py").exists():
        pytest.skip("smoke_test.py not sync to child repo")
        
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    # Create valid index
    index = tmp_path / "index.html"
    index.write_text("<html><body>Hello QuickUtils keywords testing</body></html>", encoding="utf-8")
    
    # test pass
    result = subprocess.run([sys.executable, "scripts/smoke_test.py", str(tmp_path), "QuickUtils", "testing"], capture_output=True, env=env)
    assert result.returncode == 0
    
    # test fail keyword
    result = subprocess.run([sys.executable, "scripts/smoke_test.py", str(tmp_path), "missingkw"], capture_output=True, env=env)
    assert result.returncode == 1
    
    # test empty file
    index.write_text("  ", encoding="utf-8")
    result = subprocess.run([sys.executable, "scripts/smoke_test.py", str(tmp_path)], capture_output=True, env=env)
    assert result.returncode == 1
    
    # test file missing
    index.unlink()
    result = subprocess.run([sys.executable, "scripts/smoke_test.py", str(tmp_path)], capture_output=True, env=env)
    assert result.returncode == 1
    
    # test no args
    result = subprocess.run([sys.executable, "scripts/smoke_test.py"], capture_output=True, env=env)
    assert result.returncode == 1

# --- Coverage tests for verify_repos.py ---

def test_verify_repos_coverage(tmp_path):
    import pytest
    pytest.importorskip("scripts.verify_repos")
    import scripts.verify_repos as vr
    from unittest.mock import patch, MagicMock
    
    # Test JSON decode error
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json", encoding="utf-8")
    
    with patch("os.environ.get", return_value="token123"), \
         patch("scripts.verify_repos.Path", return_value=bad_json):
        vr.main()
        
    # Test rest of flows
    good_json = tmp_path / "good.json"
    good_json.write_text('{"proj1": {"repo_name": "repo1"}, "proj2": {}}', encoding="utf-8")
    
    with patch("os.environ.get", return_value="token123"), \
         patch("scripts.verify_repos.Path", return_value=good_json), \
         patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post:
         
        # mock user response
        mock_user = MagicMock()
        mock_user.status_code = 200
        mock_user.json.return_value = {"login": "testuser"}
        
        # mock repo 404
        mock_repo = MagicMock()
        mock_repo.status_code = 404
        
        mock_get.side_effect = [mock_user, mock_repo]
        
        # mock post failed
        mock_post_res = MagicMock()
        mock_post_res.status_code = 500
        mock_post_res.text = "Server Error"
        mock_post.return_value = mock_post_res
        
        vr.main()

# --- Coverage tests for generate_pins.py missing lines ---

def test_generate_pins_main_block():
    import sys
    import subprocess
    result = subprocess.run([sys.executable, "scripts/generate_pins.py"], capture_output=True)
    assert result.returncode == 0


