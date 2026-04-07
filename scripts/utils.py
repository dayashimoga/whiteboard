"""
Shared utilities for the Programmatic SEO Directory.
"""
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Resolve base directories, prioritizing environment variables, then falling back to local paths
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))

# SRC_DIR resolution
SRC_DIR = Path(os.environ.get("SRC_DIR", PROJECT_ROOT / "src"))

# Project identification logic (moved up for path resolution)
CONFIG_PATH = PROJECT_ROOT / "project_config.json"
_CONFIG = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _CONFIG = json.load(f)
    except Exception as exc:
        print(f"  ⚠️ Failed to load project_config.json: {exc}")

if not isinstance(_CONFIG, dict):
    _CONFIG = {}


def _detect_project_type() -> str:
    """Auto-detect the PROJECT_TYPE from environment or current working directory.

    Resolution order:
    1. PROJECT_TYPE environment variable (explicit override — set by Terraform/CI)
    2. CWD-based detection (if running inside a projects/* subdirectory)
    3. PROJECT_ROOT-based detection (if PROJECT_ROOT itself is a project dir)
    4. Default: "quickutils-master"
    """
    # 1. Explicit environment variable (set by Terraform for Cloudflare Pages)
    env_val = os.environ.get("PROJECT_TYPE")
    if env_val:
        return str(env_val)

    # 2. CWD-based detection — infer from current working directory
    cwd = Path.cwd().resolve()
    projects_dir = PROJECT_ROOT / "projects"
    if projects_dir.exists():
        try:
            rel = cwd.relative_to(projects_dir)
            top_dir = rel.parts[0] if rel.parts else None
            if top_dir and (projects_dir / top_dir).is_dir():
                return str(top_dir)
        except ValueError:
            pass

    # 3. PROJECT_ROOT-based detection — if PROJECT_ROOT is itself a project
    #    (e.g. when deployed individually, PROJECT_ROOT = the project dir)
    root_name = PROJECT_ROOT.name
    if root_name != "boring" and (PROJECT_ROOT / "data" / "database.json").exists():
        return root_name

    # 4. Default to quickutils-master (the main directory project)
    return "quickutils-master"


PROJECT_TYPE = _detect_project_type()


def get_project_database_path(project_name: str) -> Path:
    """Get the absolute path to a specific project's database.json.

    Args:
        project_name: The project directory name (e.g. 'cheatsheets-directory').

    Returns:
        Path to the project's data/database.json.
    """
    projects_dir = PROJECT_ROOT / "projects"
    project_dir = projects_dir / project_name
    if not project_dir.exists():
        # Try without -directory suffix
        project_dir = projects_dir / f"{project_name}-directory"
    return project_dir / "data" / "database.json"


def _normalize_project_name(name: str) -> str:
    """Normalize a project name by stripping the '-directory' suffix."""
    return name.replace("-directory", "") if name.endswith("-directory") else name


# ── Intelligent Path Resolution for Mono-repo ───────────────────────────────
# When running from the mono-repo root (h:/boring), resolve DATA_DIR and SRC_DIR
# to the correct project subdirectory based on PROJECT_TYPE.
#
# GUARD: Only apply when 'projects/' directory actually exists.
# Individual repos deployed on Cloudflare do NOT have a projects/ subdirectory.
_is_monorepo = (PROJECT_ROOT / "projects").exists() and "projects" not in str(PROJECT_ROOT)

if _is_monorepo and not DATA_DIR.exists():
    # DATA_DIR from env didn't resolve — try finding the project directory
    _norm = _normalize_project_name(PROJECT_TYPE)
    _candidates = [
        PROJECT_ROOT / "projects" / PROJECT_TYPE,
        PROJECT_ROOT / "projects" / f"{PROJECT_TYPE}-directory",
        PROJECT_ROOT / "projects" / f"{_norm}-directory" if _norm != PROJECT_TYPE else None,
    ]
    for _candidate in filter(None, _candidates):
        if (_candidate / "data").exists():
            DATA_DIR = _candidate / "data"
            break

if _is_monorepo and not SRC_DIR.exists():
    _candidates = [
        PROJECT_ROOT / "projects" / PROJECT_TYPE,
        PROJECT_ROOT / "projects" / f"{PROJECT_TYPE}-directory",
    ]
    for _candidate in filter(None, _candidates):
        if (_candidate / "src").exists():
            SRC_DIR = _candidate / "src"
            break

# Log warnings if paths still don't exist (makes debugging visible)
if not DATA_DIR.exists():
    print(f"  ⚠️  DATA_DIR does not exist: {DATA_DIR} (PROJECT_TYPE={PROJECT_TYPE})")
if not SRC_DIR.exists():
    print(f"  ⚠️  SRC_DIR does not exist: {SRC_DIR} (PROJECT_TYPE={PROJECT_TYPE})")

DIST_DIR = Path(os.environ.get("DIST_DIR", PROJECT_ROOT / "dist"))
TEMPLATES_DIR = SRC_DIR / "templates"
if not TEMPLATES_DIR.exists() and (SRC_DIR / "src" / "templates").exists():
    TEMPLATES_DIR = SRC_DIR / "src" / "templates"



def get_config(key, default):
    """Resolve a configuration value with cascading priority.

    Resolution order:
    1. Environment variable
    2. Project-specific override in project_config.json
    3. Root-level value in project_config.json
    4. Default value
    """
    # 1. Check environment variable
    val = os.environ.get(key)
    
    # 2. Check project-specific config overrides
    if val is None:
        projects_cfg = _CONFIG.get("projects", {})
        # Try: full name, short name, and with -directory suffix
        short_name = _normalize_project_name(PROJECT_TYPE)
        project_overrides = (
            projects_cfg.get(PROJECT_TYPE)
            or projects_cfg.get(short_name)
            or projects_cfg.get(f"{short_name}-directory")
            or {}
        )
        if key in project_overrides:
            val = project_overrides[key]
            
    # 3. Fallback to root level config json and finally default
    if val is None:
        val = _CONFIG.get(key, default)
        
    # Handle boolean strings from environment or config
    if isinstance(val, str):
        if val.lower() in ["true", "yes", "1"]:
            return True
        if val.lower() in ["false", "no", "0"]:
            return False
    return val

# Global Configuration Constants
GH_USERNAME = get_config("GH_USERNAME", "dayashimoga")
GA_MEASUREMENT_ID = get_config("GA_MEASUREMENT_ID", "G-QPDP38ZCCV")
ADSENSE_PUBLISHER_ID = get_config("ADSENSE_PUBLISHER_ID", "ca-pub-5193703345853377")
AMAZON_AFFILIATE_TAG = get_config("AMAZON_AFFILIATE_TAG", "quickutils-21")
GOOGLE_SITE_VERIFICATION = get_config("GOOGLE_SITE_VERIFICATION", "")
PINTEREST_DOMAIN_VERIFY = get_config("PINTEREST_DOMAIN_VERIFY", "c816c2b41079835efd234cb5afef59bf")

# Integration Flags
ENABLE_ADSENSE = get_config("ENABLE_ADSENSE", True)
ENABLE_AMAZON = get_config("ENABLE_AMAZON", True)
ENABLE_PINTEREST = get_config("ENABLE_PINTEREST", True)

# Site Identity — maps normalized project names to human-readable type labels
SITE_TYPE_MAP = {
    "apistatus": "Status Pages",
    "boilerplates": "Boilerplates",
    "cheatsheets": "Cheatsheets",
    "datasets": "Datasets",
    "jobs": "Jobs",
    "opensource": "Open Source",
    "prompts": "Prompts",
    "tools": "Tools",
    "dailyfacts": "Daily Facts",
}

# Normalize PROJECT_TYPE for lookups (strip -directory suffix)
_NORMALIZED_TYPE = _normalize_project_name(PROJECT_TYPE)
SITE_TYPE = SITE_TYPE_MAP.get(_NORMALIZED_TYPE, SITE_TYPE_MAP.get(PROJECT_TYPE, "APIs"))

_MASTER_TYPES = {"master", "directory", "boringwebsite", "quickutils-master"}
if _NORMALIZED_TYPE in _MASTER_TYPES or PROJECT_TYPE in _MASTER_TYPES:
    DEFAULT_SITE_URL = "https://quickutils.top"
    DEFAULT_SITE_NAME = "QuickUtils Directory"
    SITE_TYPE = "Directory"
else:
    # Use the normalized (short) name for subdomain
    DEFAULT_SITE_URL = f"https://{_NORMALIZED_TYPE}.quickutils.top"
    DEFAULT_SITE_NAME = f"QuickUtils {SITE_TYPE} Directory"

SITE_URL = get_config("SITE_URL", DEFAULT_SITE_URL)
SITE_NAME = get_config("SITE_NAME", DEFAULT_SITE_NAME)
SITE_DESCRIPTION = get_config("SITE_DESCRIPTION", f"The Ultimate Directory of Free, Open {SITE_TYPE} — searchable and categorized.")


_SLUG_CACHE = {}

def slugify(text: Any) -> str:
    """Convert text to a URL-safe slug with caching for performance."""
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""
    if text in _SLUG_CACHE:
        return _SLUG_CACHE[text]
        
    # Normalize unicode to ASCII
    n_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    # Lowercase
    n_text = n_text.lower()
    # Replace non-alphanumeric with hyphens
    n_text = re.sub(r"[^a-z0-9]+", "-", n_text)
    # Strip leading/trailing hyphens
    n_text = n_text.strip("-")
    # Collapse multiple hyphens
    n_text = re.sub(r"-{2,}", "-", n_text)
    
    _SLUG_CACHE[text] = n_text
    return n_text


def load_database(path: Optional[Path] = None) -> list:
    """Load the database JSON file and return a list of items with optimized slug generation."""
    if path is None:
        path = DATA_DIR / "database.json"

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Database at {path} must contain a JSON array")

    # Inject slugs and titles if missing (optimized)
    for item in data:
        title = item.get("title", item.get("name", "Unknown Item"))
        if "title" not in item:
            item["title"] = title
        
        if "slug" not in item:
            # Prefer 'id' if available for stable slugs, otherwise title
            slug_source = str(item.get("id", title))
            item["slug"] = slugify(slug_source)
        
        # Ensure critical fields have defaults for templates
        if "description" not in item:
            item["description"] = "No description provided."
        if "auth" not in item:
            item["auth"] = "None"
        if "cors" not in item:
            item["cors"] = "unknown"
        if "https" not in item:
            item["https"] = True
        if "category" not in item:
            item["category"] = "Uncategorized"
        if "url" not in item:
            item["url"] = "#"
                
    return data


def save_database(items: list, path: Optional[Path] = None) -> bool:
    """Save items to the database JSON file with deterministic sorting.

    Args:
        items: List of item dictionaries.
        path: Optional path. Defaults to data/database.json.
    
    Returns:
        True if saved successfully, False otherwise.
    """
    if path is None:
        path = DATA_DIR / "database.json"

    try:
        ensure_dir(path.parent)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        return True
    except Exception as e:
        print(f"  ✗ Error saving database: {e}")
        return False


def ensure_dir(path: Path) -> None:
    """Create a directory and its parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)


def get_categories(items: list) -> dict:
    """Group items by category.

    Args:
        items: List of item dicts, each with a 'category' key.

    Returns:
        Dict mapping category name -> list of items.
    """
    categories = {}
    for item in items:
        cat = item.get("category", "Uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    # Sort categories alphabetically
    return dict(sorted(categories.items()))


def truncate(text: str, max_length: int = 160) -> str:
    """Truncate text to max_length, adding ellipsis if needed."""
    if not text or len(text) <= max_length:
        return text or ""

    # Ensure we have at least 3 characters room for ellipsis
    limit = int(max(0, max_length - 3))
    content = str(text)
    trimmed = content[:limit]

    # Try to break at a space to avoid cutting words
    if " " in trimmed:
        return trimmed.rsplit(" ", 1)[0] + "..."
    return trimmed + "..."


def load_network_links() -> list:
    """Return a list of network sites for dynamic cross-linking from project_config.json."""
    projects_cfg = _CONFIG.get("projects", {})
    links = []
    
    # Always include the main directory/portal
    links.append({
        "name": "Main Site",
        "url": "https://quickutils.top"
    })
    
    # Add actual projects from config
    for p_id, p_config in projects_cfg.items():
        if p_id in ["master", "directory", "boringwebsite"]:
            continue
            
        url = p_config.get("SITE_URL", "")
        # Fallback if somehow missing
        if not url:
            subdomain = p_id.replace('-directory', '')
            url = f"https://{subdomain}.quickutils.top"
            
        # Clean name
        name = p_config.get("SITE_NAME", p_id.replace('-directory', '').replace('-', ' ').title())
        # Make name shorter for footer (e.g. 'Boilerplates Directory' -> 'Boilerplates')
        if name.endswith(" Directory") and name != "Open Source Directory":
            name = name[:-10]
            
        links.append({
            "name": name,
            "url": url
        })
        
    return sorted(links, key=lambda x: x["name"])
