"""
Social Media Bot for the Programmatic SEO Directory.

Picks a random API from the database and posts a promotional message
to Mastodon via REST API. Designed to run daily via GitHub Actions.
"""
import hashlib
import os
import random
import sys
from datetime import datetime, timezone

import requests

from scripts.utils import SITE_URL, load_database, slugify


def get_daily_seed() -> int:
    """Generate a deterministic seed based on the current date.

    This ensures the same item isn't posted twice on the same day,
    and provides variety across days.

    Returns:
        Integer seed based on the date string hash.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)


def pick_random_item(items: list) -> dict:
    """Pick a random item using a date-seeded RNG.

    Args:
        items: List of item dicts from the database.

    Returns:
        A randomly selected item dict.
    """
    seed = get_daily_seed()
    rng = random.Random(seed)
    return rng.choice(items)


def platform_post(item: dict) -> str:
    """Format a promotional post for the given item.

    Args:
        item: Item dict with title, description, category, url, slug.

    Returns:
        Formatted post string within Mastodon's 500-char limit.
    """
    item_url = f"{SITE_URL}/item/{item['slug']}.html"
    category = item.get("category", "API")
    auth = item.get("auth", "None")
    pricing = item.get("pricing", "Free")

    # Build hashtags from category
    hashtag = f"#{slugify(category).replace('-', '')}"

    lines = [
        f"🔗 {item['title']}",
        f"",
        f"{item['description']}",
        f"",
        f"🏷️ Category: {category}",
        f"💰 Pricing: {pricing}",
        f"🔐 Auth: {auth}",
        f"🌐 {'HTTPS ✅' if item.get('https') else 'HTTP only'}",
        f"",
        f"Check it out → {item_url}",
        f"",
        f"#API #OpenSource #FreeDev {hashtag} #WebDev #WebTools #DeveloperTools",
    ]

    post = "\n".join(lines)

    # Ensure we stay within Mastodon's 500-char limit
    if len(post) > 500:
        post = post[:497] + "..."

    return post


def post_to_mastodon(message: str) -> bool:
    """Post a status update to Mastodon.

    Requires environment variables:
        MASTODON_ACCESS_TOKEN: API token with write:statuses scope.
        MASTODON_INSTANCE_URL: Instance domain (e.g., mastodon.social).

    Args:
        message: The status text to post.

    Returns:
        True if the post was successful, False otherwise.
    """
    access_token = os.environ.get("MASTODON_ACCESS_TOKEN")
    instance_url = os.environ.get("MASTODON_INSTANCE_URL", "mastodon.social")

    if not access_token:
        print("  ✗ MASTODON_ACCESS_TOKEN not set. Skipping post.")
        return False

    # Ensure the instance URL has the protocol
    if not instance_url.startswith("http"):
        instance_url = f"https://{instance_url}"

    api_url = f"{instance_url}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"status": message, "visibility": "public"}

    try:
        response = requests.post(api_url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        print(f"  ✓ Posted to Mastodon: {result.get('url', 'success')}")
        return True
    except requests.RequestException as e:
        print(f"  ✗ Failed to post to Mastodon: {e}")
        return False


def main():
    """CLI entry point."""
    print("📣 Social media bot starting...")

    items = load_database()
    if not items:
        print("  ✗ No items in database. Aborting.")
        sys.exit(0)

    item = pick_random_item(items)
    print(f"  → Selected: {item['title']} ({item['category']})")

    message = platform_post(item)
    print(f"  → Post preview ({len(message)} chars):")
    print(f"    {message[:100]}...")

    success = post_to_mastodon(message)

    if success:
        print("✅ Social post complete.")
    else:
        print("⚠️  Social post skipped.")

    # Always exit 0 for CI safety
    sys.exit(0)


if __name__ == "__main__":
    main()
