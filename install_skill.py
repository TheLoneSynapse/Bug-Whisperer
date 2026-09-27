#!/usr/bin/env python3
"""Install the mistake-finder skill globally for IBM Bob.

Copies the project-scoped skill (`.bob/skills/mistake-finder/`) into Bob's
global skill directory (`~/.bob/skills/mistake-finder/`), so the skill is
available in **every** project you open in Bob — not just this repository.

Usage:
    python install_skill.py            # install or refresh the global copy
    python install_skill.py --check    # show install status only
    python install_skill.py --remove   # remove the global copy

No third-party dependencies; any Python 3.8+ works.
"""

import argparse
import shutil
import sys
from pathlib import Path

SKILL_NAME = "mistake-finder"
PROJECT_SKILL_DIR = Path(__file__).resolve().parent / ".bob" / "skills" / SKILL_NAME
GLOBAL_SKILL_DIR = Path.home() / ".bob" / "skills" / SKILL_NAME


def _status() -> str:
    if not PROJECT_SKILL_DIR.is_dir():
        return "missing-project-copy"
    if not (PROJECT_SKILL_DIR / "SKILL.md").is_file():
        return "invalid-project-copy"
    if GLOBAL_SKILL_DIR.is_dir():
        return "installed"
    return "not-installed"


def _install() -> int:
    status = _status()
    if status in ("missing-project-copy", "invalid-project-copy"):
        print(
            f"ERROR: expected the skill at {PROJECT_SKILL_DIR} with a SKILL.md inside. "
            "Run this script from the repository root.",
            file=sys.stderr,
        )
        return 1
    if status == "installed":
        print(f"Refreshing existing install: {GLOBAL_SKILL_DIR}")
        shutil.rmtree(GLOBAL_SKILL_DIR)
    else:
        print(f"Installing skill globally: {GLOBAL_SKILL_DIR}")
    GLOBAL_SKILL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PROJECT_SKILL_DIR, GLOBAL_SKILL_DIR, dirs_exist_ok=True)
    copied = sorted(p.name for p in GLOBAL_SKILL_DIR.iterdir())
    print("Copied files: " + ", ".join(copied))
    print(
        "\nDone. Restart Bob (or open a new conversation) and check\n"
        "Settings -> Skills: 'mistake-finder' should be listed as a global skill.\n"
        "Then, in any project: 'run mistake-finder on the failing tests' or\n"
        "'check my code for mistakes'."
    )
    return 0


def _remove() -> int:
    if not GLOBAL_SKILL_DIR.is_dir():
        print("Nothing to remove: no global install found.")
        return 0
    shutil.rmtree(GLOBAL_SKILL_DIR)
    print(f"Removed {GLOBAL_SKILL_DIR}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="show status without changing anything")
    parser.add_argument("--remove", action="store_true", help="remove the global skill copy")
    args = parser.parse_args()

    if args.check:
        status = _status()
        human = {
            "missing-project-copy": "project skill copy is missing (run from the repo root)",
            "invalid-project-copy": "project skill copy has no SKILL.md",
            "installed": "installed globally",
            "not-installed": "not installed globally (project-scoped only)",
        }[status]
        print(f"status: {status} - {human}")
        print(f"project skill dir: {PROJECT_SKILL_DIR}")
        print(f"global skill dir:  {GLOBAL_SKILL_DIR}")
        return 0
    if args.remove:
        return _remove()
    return _install()


if __name__ == "__main__":
    raise SystemExit(main())
