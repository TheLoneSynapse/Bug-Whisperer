#!/usr/bin/env python3
"""mistake_box.py - run code and print its mistakes as a boxed terminal report.

The stock Python CLI prints a bare traceback: a wall of text where the two lines
that matter - where the mistake is, and what to do about it - are buried. This
wrapper runs your command, lets its normal output through, then parses the error
and prints one box containing WHERE / WHAT WENT WRONG / SUGGESTIONS.

Usage:
    python mistake_box.py python mycode.py
    python mistake_box.py -- python mycode.py arg1 arg2
    python mistake_box.py --file mycode.py          # static check, no run
    python mistake_box.py --log ci.log              # parse an existing log
    python mistake_box.py --ascii python mycode.py  # plain +-| box
    python mistake_box.py --raw python mycode.py    # also show original stderr

Installable form: `pip install .` also provides the `mistake-box` command and a
pytest plugin that boxes every failing test automatically.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:  # installed as a package: mistake_finder.mistake_box
    from . import box
except ImportError:  # run as a plain script next to box.py
    import box  # type: ignore[no-redef]


def _report(finding: "box.Finding", width: int, ascii_only: bool) -> None:
    box.emit(box.box_title(finding), box.build_body(finding), width, ascii_only)


def _success(width: int, ascii_only: bool, note: str = "") -> None:
    body = [f"  {note}"] if note else []
    box.emit("NO MISTAKES DETECTED", body, width, ascii_only)


def _raw_box(text: str, width: int, ascii_only: bool) -> None:
    body = ["  " + ln for ln in text.rstrip().splitlines()]
    box.emit("UNRECOGNIZED OUTPUT (showing raw)", body, width, ascii_only)


def run_command(cmd: list, width: int, ascii_only: bool, raw: bool) -> int:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"mistake-box: command not found: {cmd[0]}", file=sys.stderr)
        return 127

    if proc.stdout:
        sys.stdout.write(proc.stdout)
        sys.stdout.flush()

    if raw and proc.stderr:
        sys.stderr.write(proc.stderr)

    finding = box.parse_python_error(proc.stderr or "")
    if finding is not None:
        finding.suggestions = box.suggestions_for(finding)
        _report(finding, width, ascii_only)
    elif proc.stderr and proc.stderr.strip():
        if not raw:
            _raw_box(proc.stderr, width, ascii_only)
    elif proc.returncode == 0:
        _success(width, ascii_only, "Command exited 0 with no error output.")
    return proc.returncode


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mistake-box",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", nargs=argparse.REMAINDER,
                        help="command to run (everything after --)")
    parser.add_argument("--file", help="statically syntax-check a file, no run")
    parser.add_argument("--log", help="parse a saved log/traceback file instead of running")
    parser.add_argument("--ascii", action="store_true", help="use a plain +-| box")
    parser.add_argument("--width", type=int, default=0, help="box width (default: 88)")
    parser.add_argument("--raw", action="store_true", help="also print the original stderr")
    args = parser.parse_args(argv)

    box.prepare_stdout()
    width = args.width or 88
    ascii_only = args.ascii

    if args.file:
        finding = box.check_file(args.file)
        if finding is None:
            if not Path(args.file).is_file():
                print(f"mistake-box: no such file: {args.file}", file=sys.stderr)
                return 2
            _success(width, ascii_only, f"{args.file}: no syntax errors.")
            return 0
        _report(finding, width, ascii_only)
        return 1

    if args.log:
        try:
            text = Path(args.log).read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"mistake-box: cannot read {args.log}: {e}", file=sys.stderr)
            return 2
        finding = box.parse_python_error(text)
        if finding is None:
            _success(width, ascii_only, f"No parseable error in {args.log}.")
            return 0
        finding.suggestions = box.suggestions_for(finding)
        _report(finding, width, ascii_only)
        return 1

    cmd = list(args.cmd)
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        parser.print_help()
        return 2
    return run_command(cmd, width, ascii_only, args.raw)


if __name__ == "__main__":
    raise SystemExit(main())
