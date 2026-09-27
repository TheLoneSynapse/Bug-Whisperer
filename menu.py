"""
menu.py - Interactive menu for mistake-finder.
Just run: .\test.bat
Pick a number, press Enter — done.
"""

import subprocess
import sys

FILES = [
    ("mycode.py",                  "pandas    — your main demo file"),
    ("tests/pandas.test.py",       "pandas    — KeyError (wrong column name)"),
    ("tests/numpy.test.py",        "numpy     — ValueError (shape mismatch)"),
    ("tests/matplotlib.test.py",   "matplotlib— ValueError (invalid color)"),
    ("tests/sklearn.test.py",      "sklearn   — ValueError (1D array to fit)"),
    ("tests/requests.test.py",     "requests  — MissingSchema (no https://)"),
    ("tests/json.test.py",         "json      — JSONDecodeError (single quotes)"),
    ("tests/math.test.py",         "math      — ValueError (sqrt of negative)"),
    ("tests/openpyxl.test.py",     "openpyxl  — ValueError (bad cell ref)"),
    ("tests/bs4.test.py",          "bs4       — FeatureNotFound (bad parser)"),
    ("tests/sqlalchemy.test.py",   "sqlalchemy— NoSuchModuleError (bad URL)"),
    ("tests/pydantic.test.py",     "pydantic  — ValidationError (wrong type)"),
    ("tests/pillow.test.py",       "pillow    — FileNotFoundError (missing image)"),
    ("tests/scipy.test.py",        "scipy     — LinAlgError (singular matrix)"),
    ("tests/seaborn.test.py",      "seaborn   — ValueError (None data)"),
    ("tests/tqdm.test.py",         "tqdm      — TypeError (None iterable)"),
]

def show_menu():
    print("\n" + "="*55)
    print("   MISTAKE-FINDER — Pick a file to check")
    print("="*55)
    for i, (_, label) in enumerate(FILES, 1):
        print(f"  [{i:2}]  {label}")
    print("  [ 0]  Exit")
    print("="*55)

def main():
    while True:
        show_menu()
        try:
            choice = input("\n  Enter number: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Bye!")
            sys.exit(0)

        if choice == "0":
            print("  Bye!")
            sys.exit(0)

        if not choice.isdigit() or not (1 <= int(choice) <= len(FILES)):
            print(f"\n  Invalid choice. Please enter a number between 1 and {len(FILES)}.")
            continue

        filepath, label = FILES[int(choice) - 1]
        print(f"\n  >> Running mistake-finder on: {filepath}\n")
        subprocess.run([
            r".venv\Scripts\mistake-box.exe",
            r".venv\Scripts\python.exe",
            filepath
        ])

        input("\n  Press Enter to go back to menu...")

if __name__ == "__main__":
    main()
