import os
import re
from pathlib import Path


def update_utils_py(path):
    """Update the load_database function in a utils.py file to inject slugs.

    Args:
        path: Path to the utils.py file to update.

    Returns:
        True if the file was updated, False otherwise.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # New load_database with slug injection:
    new_load_db = """def load_database(path: Path = None) -> list:
    \"\"\"Load the database JSON file and return a list of items with slugs generated if missing.\"\"\"
    if path is None:
        path = DATA_DIR / "database.json"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("database.json must contain a JSON array")

    # Inject slugs and titles if missing
    for item in data:
        # Title can be 'name' or 'title'
        if "title" not in item:
            item["title"] = item.get("name", "Unknown Item")

        # Slug can be 'slug' or 'id' or slugified title
        if "slug" not in item:
            if "id" in item:
                item["slug"] = slugify(str(item["id"]))
            else:
                item["slug"] = slugify(item["title"])

    return data"""

    # Look for the old function and replace it
    # Match the function definition until the return statement
    pattern = r"def load_database\(path: Path = None\) -> list:.*?\n    return data"
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_load_db, content, flags=re.DOTALL)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {path}")
        return True
    else:
        print(f"Could not find load_database pattern in {path}")
        return False


def get_directories():
    """Return directories to scan for utils.py files."""
    project_root = Path(__file__).resolve().parent.parent
    return [
        str(project_root),
        str(project_root / "projects" / "datasets-directory"),
        str(project_root / "projects" / "opensource-directory"),
        str(project_root / "projects" / "tools-directory"),
        str(project_root / "projects" / "prompts-directory"),
        str(project_root / "projects" / "cheatsheets-directory"),
        str(project_root / "projects" / "boilerplates-directory"),
        str(project_root / "projects" / "jobs-directory"),
        str(project_root / "projects" / "apistatus-directory")
    ]


def main():
    """Run slug fix across all project directories."""
    directories = get_directories()
    updated = 0
    for d in directories:
        utils_path = os.path.join(d, "scripts", "utils.py")
        if os.path.exists(utils_path):
            if update_utils_py(utils_path):
                updated += 1
    print("Global utils.py update complete.")
    return updated


if __name__ == "__main__":
    main()
