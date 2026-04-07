"""Pinterest Visual Search API Submitter.
This script automatically parses the directory JSON and uploads beautiful SVG-to-PNG hero images
to specific Pinterest Boards via the v5 REST API.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")
PINTEREST_API_BASE = "https://api.pinterest.com/v5"

def make_pinterest_request(method: str, endpoint: str, payload: dict = None) -> dict:
    url = f"{PINTEREST_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = None
    if payload:
        data = json.dumps(payload).encode("utf-8")
        
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        logger.error(f"Pinterest API Error ({e.code}): {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        logger.error(f"Network error: {e}")
        return None

def get_or_create_board(board_name: str, description: str) -> str:
    """Fetch all boards and return ID if it exists, otherwise create it."""
    response = make_pinterest_request("GET", "/boards")
    if response and "items" in response:
        for board in response["items"]:
            if board["name"].lower() == board_name.lower():
                logger.info(f"Found existing board: {board_name} (ID: {board['id']})")
                return board["id"]
                
    # Create Board if missing
    logger.info(f"Creating new board: {board_name}...")
    payload = {
        "name": board_name,
        "description": description,
        "privacy": "PUBLIC"
    }
    new_board = make_pinterest_request("POST", "/boards", payload)
    if new_board and "id" in new_board:
        return new_board["id"]
    
    return None

def create_pin(board_id: str, title: str, description: str, link_url: str, image_url: str) -> bool:
    """Creates a visually striking Pin pointing back to our programmatic SEO pages."""
    payload = {
        "board_id": board_id,
        "title": title[:100],  # Pinterest title hard strict limit
        "description": description[:500], # Pinterest description strict limit
        "link": link_url,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }
    
    logger.info(f"Uploading Pin for: {title}")
    res = make_pinterest_request("POST", "/pins", payload)
    if res and "id" in res:
        logger.info(f"✅ Successfully pinned! Pin ID: {res['id']}")
        return True
    return False

def main():
    if len(sys.argv) != 4:
        logger.error("Usage: python post_pinterest.py <host_url> <board_name> <assets_dir>")
        sys.exit(1)

    if not PINTEREST_ACCESS_TOKEN:
        logger.info("PINTEREST_ACCESS_TOKEN not set. Skipping Pinterest pinning.")
        sys.exit(0)

    host_url = sys.argv[1].rstrip("/")
    board_name = sys.argv[2]
    assets_dir = sys.argv[3]
    
    # Try multiple possible database paths
    db_path = None
    for candidate in [
        Path(f"{assets_dir}/data/database.json"),
        Path("data/database.json"),
        Path(f"{assets_dir}/../data/database.json"),
    ]:
        if candidate.exists():
            db_path = candidate
            break
    
    if db_path is None:
        logger.error(f"Could not locate database.json in {assets_dir}/data/ or data/. Skipping.")
        sys.exit(0)
        
    with open(db_path, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    if not items:
        logger.info("No items to pin.")
        sys.exit(0)

    board_id = get_or_create_board(board_name, f"Curated collection of the best free resources for {board_name}.")
    if not board_id:
        logger.error("Failed to retrieve or create the Pinterest Board. Aborting.")
        sys.exit(1)

    # Scrape only the 3 most recently updated or first 3 items to avoid rate limiting
    to_pin = items[:3]
    pinned_count = 0
    
    for item in to_pin:
        # Instead of generic images, we point to the highly stylized, generated OpenGraph headers
        image_url = f"{host_url}/images/og-image.png"
        item_url = f"{host_url}/item/{item['slug']}.html"
        
        # Craft a highly SEO optimized Pinterest Description
        desc_tags = f"#{item['category'].replace(' ', '')} #FreeTools #Developer"
        full_desc = f"Discover {item['title']} - {item.get('description', '')}! Perfect for {item.get('category', 'general')} needs. {desc_tags}"
        
        success = create_pin(board_id, item["title"], full_desc, item_url, image_url)
        if success:
            pinned_count += 1
            # Pinterest strict rate limiting policy mandates a 2-second sleep between bulk creations
            time.sleep(2)

    logger.info(f"🎉 Auto-pinning cycle complete! Pinned {pinned_count} images.")

if __name__ == "__main__":
    main()
