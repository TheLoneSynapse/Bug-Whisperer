"""
smart_run.py - Run mistake-finder directly on a .py file.

If the file is inside the tests/ folder (a *.test.py), run it directly
via mistake-box — no test_libraries.py involvement at all.

For any other file, detect which libraries it imports and run only those
matching test files from tests/.

Usage:
    python smart_run.py mycode.py
    python smart_run.py tests/pandas.test.py
"""

import re
import subprocess
import sys
from pathlib import Path

# Map: primary import name -> matching tests/*.test.py filename
LIBRARY_TEST_FILE = {
    "pandas":     "tests/pandas.test.py",
    "numpy":      "tests/numpy.test.py",
    "matplotlib": "tests/matplotlib.test.py",
    "sklearn":    "tests/sklearn.test.py",
    "requests":   "tests/requests.test.py",
    "json":       "tests/json.test.py",
    "math":       "tests/math.test.py",
    "openpyxl":   "tests/openpyxl.test.py",
    "bs4":        "tests/bs4.test.py",
    "sqlalchemy": "tests/sqlalchemy.test.py",
    "pydantic":   "tests/pydantic.test.py",
    "PIL":        "tests/pillow.test.py",
    "tqdm":       "tests/tqdm.test.py",
    "scipy":      "tests/scipy.test.py",
    "seaborn":    "tests/seaborn.test.py",
}

# Libraries that have no dedicated test file yet
KNOWN_NO_TEST = {"flask", "django", "fastapi", "httpx", "psutil", "lxml"}

# Libraries that commonly appear as helpers inside other test files —
# ignore these when scanning for the PRIMARY library of a file
HELPER_LIBS = {"numpy", "pandas", "matplotlib"}


def detect_primary_libraries(filepath: str) -> list:
    """
    Scan the file for import statements.
    Returns only the libraries that are the clear primary subject of the file,
    not helper imports that seaborn/sklearn/etc. pull in for data.
    """
    source = Path(filepath).read_text(encoding="utf-8", errors="replace")
    stem = Path(filepath).stem.replace(".test", "").lower()  # e.g. "seaborn"

    found = []
    for lib in LIBRARY_TEST_FILE:
        pattern = rf"^\s*(?:import {lib}|from {lib}[\. ])"
        if re.search(pattern, source, re.MULTILINE):
            found.append(lib)

    # If the filename stem matches one of the found libs, keep only that one.
    # e.g. seaborn.test.py → only "seaborn", even if pandas is also imported.
    stem_match = [lib for lib in found if lib.lower() == stem or
                  (stem == "pillow" and lib == "PIL")]
    if stem_match:
        return stem_match

    # For non-named files (e.g. mycode.py), return all found libs
    return found


def run_mistake_box(target: str) -> None:
    """Run mistake-box on the target file and print its output."""
    print(f"\n{'='*60}")
    print(f"  Running mistake-finder on: {target}")
    print(f"{'='*60}\n")
    subprocess.run([
        r".venv\Scripts\mistake-box.exe",
        r".venv\Scripts\python.exe",
        target
    ])


def main():
    if len(sys.argv) < 2:
        print("Usage: python smart_run.py <yourfile.py>")
        sys.exit(1)

    target = sys.argv[1]
    if not Path(target).is_file():
        print(f"Error: '{target}' not found.")
        sys.exit(1)

    target_path = Path(target)

    # Case 1: File IS a *.test.py inside tests/ — run it directly, nothing else
    if target_path.parent.name == "tests" and target_path.name.endswith(".test.py"):
        run_mistake_box(target)
        return

    # Case 2: Any other .py file — detect libraries and run matching test files
    run_mistake_box(target)

    detected = detect_primary_libraries(target)
    if not detected:
        print("\n[smart_run] No known libraries detected in your file.")
        return

    testable = [lib for lib in detected if lib in LIBRARY_TEST_FILE]
    print(f"\n[smart_run] Libraries detected in '{target}': {', '.join(detected)}")

    if not testable:
        print("[smart_run] No library-specific test files available for those libraries.")
        return

    print(f"[smart_run] Running test files only for: {', '.join(testable)}\n")
    for lib in testable:
        test_file = LIBRARY_TEST_FILE[lib]
        print(f"\n--- {lib} → {test_file} ---")
        subprocess.run([
            r".venv\Scripts\mistake-box.exe",
            r".venv\Scripts\python.exe",
            test_file
        ])


if __name__ == "__main__":
    main()
