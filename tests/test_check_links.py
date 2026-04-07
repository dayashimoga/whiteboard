"""Tests for the local link checker."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.check_links import check_links_in_dir, main

def test_check_links_in_dir_success(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_html = dist_dir / "index.html"
    index_html.write_text('<a href="item/test.html">link</a>', encoding="utf-8")
    
    item_dir = dist_dir / "item"
    item_dir.mkdir()
    test_html = item_dir / "test.html"
    test_html.write_text("item", encoding="utf-8")
    
    broken = check_links_in_dir(dist_dir)
    assert len(broken) == 0

def test_check_links_in_dir_broken(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_html = dist_dir / "index.html"
    index_html.write_text('<a href="missing.html">link</a>', encoding="utf-8")
    
    broken = check_links_in_dir(dist_dir)
    assert len(broken) == 1
    assert "missing.html" in broken[0][1]

def test_main_success(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    
    with patch("scripts.check_links.Path", return_value=tmp_path), \
         patch("scripts.check_links.check_links_in_dir", return_value=[]), \
         patch("scripts.check_links.check_database_urls"), \
         patch("sys.exit") as mock_exit:
        # Mock Path("dist").exists()
        tmp_path.joinpath("dist").mkdir(exist_ok=True)
        main([])
        # Should exit with 0
        mock_exit.assert_called_once_with(0)

def test_main_failure(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    
    with patch("scripts.check_links.Path", return_value=tmp_path), \
         patch("scripts.check_links.check_links_in_dir", return_value=[("index.html", "broken")]), \
         patch("scripts.check_links.check_database_urls"), \
         patch("sys.exit") as mock_exit:
        tmp_path.joinpath("dist").mkdir(exist_ok=True)
        main([])
        # Should exit with 1
        mock_exit.assert_called_once_with(1)

def test_check_links_branches(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_html = dist_dir / "index.html"
    # Line 25: External
    content = '<a href="http://ext.com">ext</a>'
    # Line 30: Empty/Slash
    content += '<a href="/">root</a>'
    # Line 34: Absolute
    sub_dir = dist_dir / "sub"
    sub_dir.mkdir()
    (sub_dir / "index.html").write_text("index")
    content += '<a href="/sub">abs</a>'
    # Line 41: Directory
    item_dir = dist_dir / "item"
    item_dir.mkdir()
    (item_dir / "index.html").write_text("index")
    content += '<a href="item">dir</a>'
    
    index_html.write_text(content, encoding="utf-8")
    
    broken = check_links_in_dir(dist_dir)
    assert len(broken) == 0

def test_main_report(tmp_path):
    report_file = tmp_path / "report.md"
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    
    with patch("scripts.check_links.Path", return_value=tmp_path), \
         patch("scripts.check_links.check_links_in_dir", return_value=[("index.html", "broken")]), \
         patch("scripts.check_links.check_database_urls"), \
         patch("sys.exit") as mock_exit:
        tmp_path.joinpath("dist").mkdir(exist_ok=True)
        main(["--output-report", str(report_file)])
        assert report_file.exists()
        assert "broken" in report_file.read_text()

def test_legacy_exports():
    from scripts.check_links import main_async, check_url, generate_report
    assert main_async is not None
    assert check_url is not None
    assert generate_report is not None

def test_check_database_urls_no_items():
    from scripts.check_links import check_database_urls
    with patch("scripts.check_links.load_database", return_value=[]), \
         patch("builtins.print") as mock_print:
        check_database_urls()
        mock_print.assert_any_call("  ✗ No items to check.")

def test_check_database_urls_changes():
    from scripts.check_links import check_database_urls
    items = [
        {"url": "http://ok.com", "status": "Down"},
        {"url": "http://fail.com", "status": "Up"},
        {"url": "http://fail_all.com", "status": "Up"},
        {"url": "#", "status": "Up"} # skip
    ]
    
    def mock_urlopen(req, timeout=5):
        url = req.full_url
        if url == "http://ok.com":
            return True
        elif url == "http://fail.com" and req.get_method() == "HEAD":
            raise Exception("HEAD fail")
        elif url == "http://fail.com" and req.get_method() != "HEAD":
            return True # GET succeeds
        elif url == "http://fail_all.com":
            raise Exception("Fail all")
            
    with patch("scripts.check_links.load_database", return_value=items), \
         patch("urllib.request.urlopen", side_effect=mock_urlopen), \
         patch("scripts.check_links.save_database") as mock_save:
        check_database_urls()
        
        assert items[0]["status"] == "Up"
        assert items[1]["status"] == "Up"
        assert items[2]["status"] == "Down"
        mock_save.assert_called_once()

def test_check_database_urls_no_changes():
    from scripts.check_links import check_database_urls
    items = [
        {"url": "http://ok.com", "status": "Up"}
    ]
    with patch("scripts.check_links.load_database", return_value=items), \
         patch("urllib.request.urlopen"), \
         patch("scripts.check_links.save_database") as mock_save, \
         patch("builtins.print") as mock_print:
        check_database_urls()
        mock_save.assert_not_called()
        mock_print.assert_any_call("  ✓ No status changes detected.")
