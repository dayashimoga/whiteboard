import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

import pytest

from scripts.post_pinterest import get_or_create_board, create_pin, main, make_pinterest_request


@patch("scripts.post_pinterest.urlopen")
def test_make_pinterest_request_success(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"id": "123"}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    res = make_pinterest_request("GET", "/test")
    assert res == {"id": "123"}


@patch("scripts.post_pinterest.urlopen")
def test_make_pinterest_request_error(mock_urlopen):
    mock_urlopen.side_effect = Exception("Network error")
    res = make_pinterest_request("GET", "/test")
    assert res is None


@patch("scripts.post_pinterest.make_pinterest_request")
def test_get_or_create_board_exists(mock_request):
    mock_request.return_value = {"items": [{"name": "Test Board", "id": "board123"}]}
    board_id = get_or_create_board("Test Board", "Desc")
    assert board_id == "board123"


@patch("scripts.post_pinterest.make_pinterest_request")
def test_get_or_create_board_creates_new(mock_request):
    mock_request.side_effect = [
        {"items": []},  # GET /boards returns empty
        {"id": "newboard123"}  # POST /boards returns new
    ]
    board_id = get_or_create_board("New Board", "Desc")
    assert board_id == "newboard123"


@patch("scripts.post_pinterest.make_pinterest_request")
def test_create_pin_success(mock_request):
    mock_request.return_value = {"id": "pin123"}
    success = create_pin("board1", "Title", "Desc", "http://link", "http://image")
    assert success is True


@patch("scripts.post_pinterest.make_pinterest_request")
def test_create_pin_failure(mock_request):
    mock_request.return_value = {}
    success = create_pin("board1", "Title", "Desc", "http://link", "http://image")
    assert success is False


@patch("sys.argv", ["post_pinterest.py", "http://host", "Board", "dist"])
@patch("os.environ.get")
def test_main_no_token(mock_env_get):
    mock_env_get.return_value = ""
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@patch("sys.argv", ["post_pinterest.py", "http://host", "Board", "dist"])
@patch("scripts.post_pinterest.PINTEREST_ACCESS_TOKEN", "valid_token")
@patch("pathlib.Path.exists")
def test_main_no_db(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@patch("sys.argv", ["post_pinterest.py", "http://host", "Board", "dist"])
@patch("scripts.post_pinterest.PINTEREST_ACCESS_TOKEN", "valid_token")
@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps([]))
def test_main_empty_db(mock_file, mock_exists):
    mock_exists.return_value = True
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@patch("sys.argv", ["post_pinterest.py", "http://host", "Board", "dist"])
@patch("scripts.post_pinterest.PINTEREST_ACCESS_TOKEN", "valid_token")
@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
    {"title": "Tool 1", "description": "Desc", "category": "Cat", "slug": "slug1"}
]))
@patch("scripts.post_pinterest.get_or_create_board")
@patch("scripts.post_pinterest.create_pin")
@patch("time.sleep")
def test_main_success(mock_sleep, mock_create_pin, mock_get_board, mock_file, mock_exists):
    mock_exists.return_value = True
    mock_get_board.return_value = "board123"
    mock_create_pin.return_value = True
    
    # Should complete without sys.exit error
    main()
    
    mock_create_pin.assert_called_once()
    assert mock_sleep.call_count == 1


@patch("sys.argv", ["post_pinterest.py", "http://host", "Board", "dist"])
@patch("scripts.post_pinterest.PINTEREST_ACCESS_TOKEN", "valid_token")
@patch("pathlib.Path.exists")
@patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
    {"title": "Tool 1", "description": "Desc", "category": "Cat", "slug": "slug1"}
]))
@patch("scripts.post_pinterest.get_or_create_board")
def test_main_no_board(mock_get_board, mock_file, mock_exists):
    mock_exists.return_value = True
    mock_get_board.return_value = None
    
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
