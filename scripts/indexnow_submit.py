"""Automated Search Engine Pinging via IndexNow Protocol.
This script automatically pushes all dynamically generated URLs directly to Bing, Yahoo, Yandex, and Seznam.
"""
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def parse_sitemap(sitemap_path: str) -> list[str]:
    """Parse the XML sitemap to extract all URLs."""
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//ns:loc', namespace) if elem.text]
        return urls
    except Exception as e:
        logger.error(f"Failed to parse sitemap: {e}")
        return []

def submit_to_indexnow(host: str, key: str, url_list: list[str]) -> bool:
    """Submit URLs to the unified IndexNow API endpoint."""
    if not url_list:
        logger.warning("No URLs found to submit.")
        return False

    api_endpoint = "https://api.indexnow.org/indexnow"
    
    payload = {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": url_list
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(api_endpoint, data=data, headers={"Content-Type": "application/json; charset=utf-8"})

    try:
        with urlopen(req, timeout=15) as response:
            if response.status in (200, 202):
                logger.info(f"✅ Successfully submitted {len(url_list)} URLs to IndexNow for {host}!")
                return True
            else:
                logger.error(f"Failed to submit: HTTP {response.status}")
                return False
    except HTTPError as e:
        logger.error(f"HTTPError submitting to IndexNow: {e.code} - {e.reason}")
        return False
    except URLError as e:
        logger.error(f"URLError submitting to IndexNow: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def main():
    if len(sys.argv) != 4:
        logger.error("Usage: python indexnow_submit.py <host> <dist_dir> <key>")
        sys.exit(1)

    host_url = sys.argv[1]
    dist_dir = sys.argv[2]
    key = sys.argv[3]
    
    # Strip protocols to get pure hostname (e.g., tools.quickutils.top)
    parsed_url = urlparse(host_url)
    host = parsed_url.netloc if parsed_url.netloc else host_url.replace("https://", "").replace("http://", "").strip("/")

    sitemap_path = os.path.join(dist_dir, "sitemap.xml")
    
    if not os.path.exists(sitemap_path):
        logger.error(f"Sitemap not found at {sitemap_path}. Please run generate_sitemap.py first.")
        sys.exit(1)

    urls = parse_sitemap(sitemap_path)
    if not urls:
        sys.exit(1)

    success = submit_to_indexnow(host, key, urls)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
