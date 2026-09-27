"""
find_mistakes.py

Detects which file to check in this order:
  1. File passed as argument (absolute or relative path)
  2. The currently active file in VS Code (via VSCODE_ACTIVE_FILE env var)
  3. Falls back to showing usage tips
"""

import io
import os
import subprocess
import sys
from pathlib import Path

# Force UTF-8 so box-drawing chars render on Windows cp1252 terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="backslashreplace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="backslashreplace")

PYTHON = r".venv\Scripts\python.exe"
MBOX   = r".venv\Scripts\mistake-box.exe"
ROOT   = Path(__file__).parent

# Add skill dir to path so we can import box for problem-matcher output
sys.path.insert(0, str(ROOT / ".bob" / "skills" / "mistake-finder"))
import box as _box  # noqa: E402

ALL_FILES = [
    "mycode.py",
    "tests/pandas.test.py",
    "tests/numpy.test.py",
    "tests/matplotlib.test.py",
    "tests/sklearn.test.py",
    "tests/requests.test.py",
    "tests/json.test.py",
    "tests/math.test.py",
    "tests/openpyxl.test.py",
    "tests/bs4.test.py",
    "tests/sqlalchemy.test.py",
    "tests/pydantic.test.py",
    "tests/pillow.test.py",
    "tests/scipy.test.py",
    "tests/seaborn.test.py",
    "tests/tqdm.test.py",
]


def run_on(filepath: Path):
    """Run Python directly on one file, box the error, and emit a GCC-format
    diagnostic line so VS Code's problem matcher draws a red squiggle on the
    exact line in the editor:
        <file>:<line>:<col>: error: <kind>: <message>
    """
    print(f"\n  Checking: {filepath}")
    print("=" * 60)

    # Run Python directly so we own the raw stderr (mistake-box absorbs it)
    ret = subprocess.run(
        [PYTHON, str(filepath)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if ret.stdout:
        sys.stdout.write(ret.stdout)
        sys.stdout.flush()

    stderr_text = ret.stderr or ""

    # Print the pretty box (same as mistake-box would)
    finding = _box.parse_python_error(stderr_text)
    if finding is not None:
        finding.suggestions = _box.suggestions_for(finding)
        _box.emit(_box.box_title(finding), _box.build_body(finding), 88)

        # Emit GCC-format line for VS Code's problem matcher → red squiggle
        if finding.path and finding.line:
            col = finding.col + 1 if finding.col else 1   # 1-based
            fpath = Path(finding.path)
            if not fpath.is_absolute():
                fpath = ROOT / fpath
            print(f"{fpath}:{finding.line}:{col}: error: {finding.kind}: {finding.message}")
    elif stderr_text.strip():
        # Unrecognised output — print as-is so nothing is silently swallowed
        sys.stderr.write(stderr_text)
    elif ret.returncode == 0:
        _box.emit("NO MISTAKES DETECTED", [f"  {filepath}: exited 0 with no errors."], 88)

    return ret.returncode


def resolve_target(arg: str) -> Path | None:
    """Try to resolve arg as a path relative to CWD or project root."""
    p = Path(arg)
    if p.is_file():
        return p
    # Try relative to project root
    q = ROOT / arg
    if q.is_file():
        return q
    return None


def main():
    args = sys.argv[1:]
    target = None

    # --- 1. Argument passed (VS Code sends active file via task) ---
    if args and args[0].strip():
        candidate = args[0].strip()
        target = resolve_target(candidate)
        if target is None:
            print(f"[find-mistakes] File not found: {candidate}")
            sys.exit(1)

    # --- 2. VS Code active file env var ---
    if target is None:
        vscode_file = os.environ.get("VSCODE_ACTIVE_FILE", "").strip()
        if vscode_file:
            target = resolve_target(vscode_file)

    # --- 3. Check which .py file is open via VS Code CLI ---
    if target is None:
        try:
            result = subprocess.run(
                ["code", "--status"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                if line.strip().endswith(".py"):
                    candidate = line.strip()
                    p = resolve_target(candidate)
                    if p:
                        target = p
                        break
        except Exception:
            pass

    # --- 4. Found a specific file — run only that ---
    if target is not None:
        run_on(target)
        return

    # --- 5. No file detected — ask user to use it from VS Code terminal ---
    print("\n" + "=" * 60)
    print("  FIND-MISTAKES")
    print("=" * 60)
    print("\n  TIP: Open the file you want to check in VS Code,")
    print("  then right-click it in the Explorer and choose")
    print("  'Open in Integrated Terminal', then run:\n")
    print("      .\\find-mistakes.bat\n")
    print("  OR run it directly with the filename:\n")
    print("      .\\find-mistakes.bat tests\\math.test.py")
    print("      .\\find-mistakes.bat mycode.py\n")
    print("=" * 60)


if __name__ == "__main__":
    main()
