import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from scripts.fetch_data import (
    fetch_from_primary,
    fetch_from_alternative,
    normalize_entry,
    deduplicate,
    fetch_and_save,
    main,
    get_seed_data
)

def test_fetch_from_primary_success():
    with patch("scripts.fetch_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"entries": [{"API": "Test", "Description": "A test api"}]}
        mock_get.return_value = mock_response
        
        result = fetch_from_primary()
        assert result is not None
        assert len(result) == 1
        assert result[0]["API"] == "Test"

def test_fetch_from_primary_failure():
    with patch("scripts.fetch_data.requests.get", side_effect=requests.RequestException("error")):
        assert fetch_from_primary() is None

def test_fetch_from_alternative_success():
    with patch("scripts.fetch_data.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = [{"API": "Alt", "Description": "Alt api"}]
        mock_get.return_value = mock_response
        
        result = fetch_from_alternative()
        assert result is not None
        assert len(result) == 1
        assert result[0]["API"] == "Alt"

def test_fetch_from_alternative_failure():
    with patch("scripts.fetch_data.requests.get", side_effect=json.JSONDecodeError("error", "doc", 0)):
        assert fetch_from_alternative() is None

def test_normalize_entry():
    raw = {
        "API": "My Test API",
        "Description": "It is a test",
        "Category": "Science",
        "Link": "https://test.com",
        "Auth": "apiKey",
        "HTTPS": True,
        "Cors": "yes"
    }
    norm = normalize_entry(raw)
    assert norm["title"] == "My Test API"
    assert norm["slug"] == "my-test-api"
    assert norm["category"] == "Science"
    assert norm["auth"] == "apiKey"

def test_normalize_entry_missing_fields():
    assert normalize_entry({}) is None
    assert normalize_entry({"API": "No Desc"}) is None

def test_deduplicate():
    items = [
        {"title": "B API", "slug": "b-api"},
        {"title": "A API", "slug": "a-api"},
        {"title": "A API Duplicate", "slug": "a-api"}
    ]
    uniq = deduplicate(items)
    assert len(uniq) == 2
    assert uniq[0]["slug"] == "a-api"  # sorted alphabetically
    assert uniq[1]["slug"] == "b-api"

@patch("scripts.fetch_data.save_database")
@patch("scripts.fetch_data.ensure_dir")
def test_fetch_and_save_success_master(mock_ensure, mock_save, monkeypatch):
    with patch("scripts.utils._NORMALIZED_TYPE", "master"), \
         patch("scripts.fetch_data.fetch_from_primary", return_value=[{"API": "Master Test", "Description": "..."}]):
        assert fetch_and_save() is True
        mock_save.assert_called_once()

@patch("scripts.fetch_data.save_database")
@patch("scripts.fetch_data.ensure_dir")
def test_fetch_and_save_datasets(mock_ensure, mock_save, monkeypatch):
    raw_data = [{"name": "Science Dataset", "description": "data", "Category": "Science"}]
    with patch("scripts.utils._NORMALIZED_TYPE", "datasets"), \
         patch("scripts.fetch_data.fetch_from_alternative", return_value=raw_data):
        assert fetch_and_save() is True

@patch("scripts.fetch_data.save_database")
@patch("scripts.fetch_data.ensure_dir")
def test_fetch_and_save_fallback_to_existing_db(mock_ensure, mock_save, monkeypatch, tmp_path):
    with patch("scripts.utils._NORMALIZED_TYPE", "apistatus"), \
         patch("scripts.fetch_data.DATA_DIR", tmp_path):
        # Create a fake db
        db_path = tmp_path / "database.json"
        db_path.write_text('[{"title": "Existing", "description": "..."}]')
        
        assert fetch_and_save() is True

@patch("scripts.fetch_data.save_database")
@patch("scripts.fetch_data.ensure_dir")
def test_fetch_and_save_fallback_to_seed(mock_ensure, mock_save, monkeypatch, tmp_path):
    with patch("scripts.utils._NORMALIZED_TYPE", "apistatus"), \
         patch("scripts.fetch_data.DATA_DIR", tmp_path):
        
        assert fetch_and_save() is True
        mock_save.assert_called_once()

@patch("scripts.fetch_data.fetch_and_save", return_value=True)
@patch("sys.exit")
def test_main_success(mock_exit, mock_func):
    main()
    mock_exit.assert_called_with(0)

@patch("scripts.fetch_data.fetch_and_save", return_value=False)
@patch("sys.exit")
def test_main_failure(mock_exit, mock_func):
    main()
    mock_exit.assert_called_with(0)
