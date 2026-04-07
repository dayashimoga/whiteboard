import os
import shutil
import glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

patterns = [
    "test_*.txt",
    "*.log",
    "final_test_report.txt",
    "link_report.md",
    "tests_report.txt",
    "pytest_debug.txt",
    "pytest_report.txt",
    "venv_pytest_out.txt",
    "test_output.txt",
    "test_output_utf8.txt",
    "tests_output.txt",
    ".coverage"
]

dirs_to_remove = [
    ".pytest_cache",
    "htmlcov"
]


def get_directories():
    """Return the list of directories to clean."""
    return [
        str(PROJECT_ROOT),
        str(PROJECT_ROOT / "projects" / "datasets-directory"),
        str(PROJECT_ROOT / "projects" / "opensource-directory"),
        str(PROJECT_ROOT / "projects" / "tools-directory"),
        str(PROJECT_ROOT / "projects" / "prompts-directory"),
        str(PROJECT_ROOT / "projects" / "cheatsheets-directory"),
        str(PROJECT_ROOT / "projects" / "boilerplates-directory"),
        str(PROJECT_ROOT / "projects" / "jobs-directory"),
        str(PROJECT_ROOT / "projects" / "apistatus-directory")
    ]


def clean_directory(directory):
    """Clean files and directories matching patterns from a single directory.

    Returns:
        Tuple of (files_removed, dirs_removed) counts.
    """
    files_removed = 0
    dirs_removed = 0

    if not os.path.exists(directory):
        return files_removed, dirs_removed

    print(f"Cleaning {directory}...")

    # Remove file patterns
    for pattern in patterns:
        for file_path in glob.glob(os.path.join(directory, pattern)):
            try:
                os.remove(file_path)
                print(f"  Removed file: {os.path.basename(file_path)}")
                files_removed += 1
            except Exception as e:
                print(f"  Error removing {file_path}: {e}")

    # Remove directories
    for dir_name in dirs_to_remove:
        dir_path = os.path.join(directory, dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"  Removed directory: {dir_name}")
                dirs_removed += 1
            except Exception as e:
                print(f"  Error removing directory {dir_path}: {e}")

    return files_removed, dirs_removed


def main():
    """Run cleanup across all project directories."""
    directories = get_directories()
    total_files = 0
    total_dirs = 0
    for d in directories:
        f, dr = clean_directory(d)
        total_files += f
        total_dirs += dr
    print("Cleanup complete.")
    return total_files, total_dirs


if __name__ == "__main__":
    main()
