"""Core of mistake-finder: turn an error into a boxed, explained report.

This module holds the logic shared by every front end:

  * ``mistake_box.py``    - the command-line wrapper (run code, box the error);
  * ``pytest_plugin.py``  - the pytest plugin (box every failing test).

It has no third-party dependencies. Public surface:

    Finding                  one located mistake
    parse_python_error(str)  -> Finding | None   (parse a traceback/syntax block)
    suggestions_for(Finding) -> list[str]        (ranked, concrete fixes)
    render_box(title, body, width) -> str        (the boxed text)
    build_box(Finding, width) -> str             (a full report box)
"""

from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Box drawing
# --------------------------------------------------------------------------

UNICODE_BOX = {
    "tl": "\u2554", "tr": "\u2557", "bl": "\u255a", "br": "\u255d",
    "h": "\u2550", "v": "\u2551", "sep_l": "\u2560", "sep_r": "\u2563",
}
ASCII_BOX = {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|",
             "sep_l": "+", "sep_r": "+"}

_DIVIDER = object()  # body marker: draw a horizontal rule here


def _wrap(text: str, width: int, subsequent_indent: str = "") -> list:
    """Wrap one logical line, preserving its leading indentation."""
    if text == "":
        return [""]
    if len(text) <= width:
        return [text]
    indent = text[: len(text) - len(text.lstrip(" "))]
    body = text[len(indent):]
    wrapped = textwrap.wrap(
        body,
        width=max(10, width),
        subsequent_indent=indent + subsequent_indent,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=False,
        drop_whitespace=False,
    )
    if not wrapped:
        return [text[:width]]
    wrapped[0] = indent + wrapped[0]
    return wrapped


def render_box(title: str, body: list, width: int, ascii_only: bool = False) -> str:
    g = ASCII_BOX if ascii_only else UNICODE_BOX
    inner = max(20, width - 2)
    out = [g["tl"] + g["h"] * inner + g["tr"]]
    for t in _wrap(title, inner - 2):
        out.append(g["v"] + (" " + t).ljust(inner) + g["v"])
    if body:
        out.append(g["sep_l"] + g["h"] * inner + g["sep_r"])
        for row in body:
            if row is _DIVIDER:
                out.append(g["sep_l"] + g["h"] * inner + g["sep_r"])
                continue
            for w in _wrap(row, inner - 2):
                out.append(g["v"] + (" " + w).ljust(inner) + g["v"])
    out.append(g["bl"] + g["h"] * inner + g["br"])
    return "\n".join(out)


def emit(title: str, body: list, width: int, ascii_only: bool = False) -> None:
    """Print a box, degrading to ASCII if the stream cannot encode box chars."""
    text = render_box(title, body, width, ascii_only)
    try:
        print(text)
    except UnicodeEncodeError:
        print(render_box(title, body, width, True))


def prepare_stdout() -> None:
    """Ask for UTF-8 output so the pretty box survives on Windows consoles."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


@dataclass
class Finding:
    kind: str = "Error"
    message: str = ""
    path: str = ""
    line: int = 0
    func: str = ""
    source: str = ""          # offending source line (from error output)
    col: int = 0              # 0-based caret column in `source`
    suggestions: list = field(default_factory=list)
    static: bool = False      # came from a static syntax check, not a run
    test_id: str = ""         # set by the pytest plugin


# --------------------------------------------------------------------------
# Parsing Python error output
# --------------------------------------------------------------------------

_FILE_RE = re.compile(r'^\s*File "([^"]+)", line (\d+)(?:, in (.+))?\s*$')
_EXC_RE = re.compile(
    r"^([A-Za-z_][\w.]*(?:Error|Exception|Interrupt|Exit|Warning|Iteration))"
    r"(?::\s?(.*))?$"
)


def _looks_like_stdlib(path: str) -> bool:
    norm = path.replace("\\", "/")
    if "site-packages" in norm or "dist-packages" in norm:
        return True
    if norm.startswith("lib/python") or "/lib/python" in norm:
        return True
    if norm.startswith("<") and norm.endswith(">"):
        return True
    return False


def parse_python_error(text: str) -> "Finding | None":
    """Parse a traceback or syntax-error block into a Finding."""
    lines = text.splitlines()
    frames = []
    for i, ln in enumerate(lines):
        m = _FILE_RE.match(ln)
        if m:
            path, lineno, func = m.group(1), int(m.group(2)), m.group(3) or ""
            frames.append((i, path, lineno, func))

    # Find the exception summary line: prefer the last non-indented Error-ish
    # line, and fall back to an indented one (pytest indents its E-block).
    exc_idx = None
    for i in range(len(lines) - 1, -1, -1):
        ln = lines[i]
        if ln and not ln[0].isspace() and _EXC_RE.match(ln):
            exc_idx = i
            break
    if exc_idx is None:
        for i in range(len(lines) - 1, -1, -1):
            s = lines[i].strip()
            if s and _EXC_RE.match(s):
                exc_idx = i
                break

    if exc_idx is None and not frames:
        return None

    f = Finding()
    if exc_idx is not None:
        m = _EXC_RE.match(lines[exc_idx].strip())
        if m:
            f.kind = m.group(1)
            f.message = (m.group(2) or "").strip()
        else:
            f.kind = lines[exc_idx].strip()
    elif frames:
        f.kind, f.message = "Error", ""

    # Syntax-family errors: a frame without ", in" plus a source/caret block.
    syntax_families = ("SyntaxError", "IndentationError", "TabError")
    no_func = [fr for fr in frames if not fr[3]]
    if f.kind in syntax_families or (no_func and not any(fr[3] for fr in frames)):
        header = no_func[-1] if no_func else frames[-1]
        _, f.path, f.line, _ = header
        f.func = ""
        src_i = header[0] + 1
        if src_i < len(lines):
            # Keep the line's own indentation so a caret column lines up with it.
            f.source = lines[src_i]
            caret_i = src_i + 1
            if caret_i < len(lines) and "^" in lines[caret_i]:
                f.col = lines[caret_i].index("^")
        return f

    # Runtime errors: pick the innermost frame that lives in user code.
    user = [fr for fr in frames if not _looks_like_stdlib(fr[1])]
    chosen = user[-1] if user else (frames[-1] if frames else None)
    if chosen is not None:
        _, f.path, f.line, f.func = chosen
    return f


# --------------------------------------------------------------------------
# Suggestions
# --------------------------------------------------------------------------

_GENERIC = [
    "Re-run with the raw traceback visible (mistake-box --raw, or pytest -x) to "
    "see the full context.",
]

_BY_KIND = {
    "SyntaxError": [
        "Check the flagged line and the line just above it -- Python often reports "
        "the mistake one token after the real problem.",
        "Balance brackets/quotes on this line and any f-string it contains.",
    ],
    "IndentationError": [
        "Indent with a consistent number of spaces (4 is standard); the caret marks "
        "the block whose indentation is wrong.",
        "A blank line inside an indented block is fine -- a stray space is not.",
    ],
    "TabError": [
        "Tabs and spaces are mixed. Re-indent the file with a single style "
        "(all spaces is safest).",
    ],
    "NameError": [
        "Check the spelling and capitalization of the name; Python is case-sensitive.",
        "Make sure it is defined before first use (above this line, or imported).",
        "Inside a class/method, did you forget `self.` before the attribute?",
    ],
    "UnboundLocalError": [
        "The name is assigned somewhere later in this function, which makes it "
        "local everywhere -- use it as a parameter or initialize it before use.",
    ],
    "AttributeError": [
        "Confirm the object's type (`print(type(obj))` just above) and that the "
        "attribute/method exists on it.",
        "If the message says 'NoneType', a previous call returned None -- check "
        "that value before using it.",
    ],
    "TypeError": [
        "One operand/argument has a different type than expected -- print the "
        "types of the values involved.",
        "For argument-count errors, match the call site to the function signature.",
        "Convert explicitly (e.g. `int(x)`, `str(x)`) rather than relying on "
        "implicit coercion.",
    ],
    "ValueError": [
        "The type is right but the value is not acceptable (bad literal, wrong "
        "shape, out of range) -- validate/guard it before use.",
    ],
    "IndexError": [
        "The index is past the end of the sequence. Guard with `if i < len(seq)` "
        "and check the loop bounds (`range(len(seq))`, not `range(len(seq)+1)`).",
    ],
    "KeyError": [
        "The key is missing. Use `d.get(key, default)` or check `if key in d` "
        "before indexing.",
    ],
    "ZeroDivisionError": [
        "Guard the divisor: `if denom == 0: ...` -- and check whether an empty "
        "collection is being averaged.",
    ],
    "FileNotFoundError": [
        "Verify the path and the working directory (`os.getcwd()`); prefer "
        "absolute paths or `pathlib.Path(__file__).parent`.",
    ],
    "ModuleNotFoundError": [
        "Install the package or fix the import path. To see where Python is "
        'looking: `python -c "import sys; print(sys.path)"`.',
    ],
    "ImportError": [
        "Check the module's public names and for circular imports between modules.",
    ],
    "RecursionError": [
        "Find the base case that is never reached, or convert the recursion to a "
        "loop / add memoization.",
    ],
    "StopIteration": [
        "Use `next(it, default)` instead of bare `next(it)` so exhaustion is handled.",
    ],
    "AssertionError": [
        "Read the assertion: what value did the code actually produce, and what did "
        "the test expect? Trace backwards to the first line where they diverge.",
    ],
}


def suggestions_for(f: Finding) -> list:
    tips = []
    msg = f.message or ""
    low = msg.lower()

    if "not defined" in low and "name" in low:
        tips += [
            "Search where the name is defined: it may be a typo or not yet run.",
            "If it is an attribute, add `self.`; if it is a module, add the import.",
        ]
    if "unsupported operand type" in low:
        tips.append("Mix of types in an operator -- cast with int()/float()/str() "
                    "before combining.")
    if "not subscriptable" in low:
        tips.append("You indexed a value that is not a sequence -- check it is a "
                    "list/dict/str, not an int or None.")
    if "not callable" in low:
        tips.append("You called something that is not a function -- you may have "
                    "used a variable name that shadows a method.")
    if "positional argument" in low or "requires" in low or "takes" in low:
        tips.append("Compare the number of arguments at the call with the `def` "
                    "signature, including any `self`.")
    if "list index out of range" in low or "index out of range" in low:
        tips.append("Off-by-one likely: confirm the last valid index is len()-1.")
    if "division by zero" in low:
        tips.append("The divisor evaluated to 0 -- print it just before the "
                    "division to find which path produced it.")
    if "is not valid json" in low or "expecting value" in low:
        tips.append("Print the raw payload before parsing; it is probably empty "
                    "or an error page, not JSON.")
    if f.kind == "SyntaxError" and f.source:
        if re.search(r"[^=!<>]=[^=]", f.source) and "==" not in f.source:
            tips.append("A single `=` assigns; use `==` to compare.")
        if f.source.rstrip().endswith(")") and f.source.count("(") != f.source.count(")"):
            tips.append("Unbalanced parentheses on this logical line.")
        if f.source.count("'") % 2 or f.source.count('"') % 2:
            tips.append("A quote is unclosed -- check for a missing closing quote.")

    for t in _BY_KIND.get(f.kind, []):
        if t not in tips:
            tips.append(t)
    if not tips:
        tips += _GENERIC
    # de-dup, keep order
    seen, out = set(), []
    for t in tips:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out[:5]


# --------------------------------------------------------------------------
# Rendering a finding as a box
# --------------------------------------------------------------------------


def _excerpt(path: str, line: int, context: int = 1):
    """Return [(lineno, text)] around `line`, or None if file unreadable."""
    if not path or path.startswith("<"):
        return None
    p = Path(path)
    if not p.is_file():
        return None
    try:
        src = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if line < 1 or line > len(src):
        return None
    lo = max(1, line - context)
    hi = min(len(src), line + context)
    return [(n, src[n - 1]) for n in range(lo, hi + 1)]


def build_body(f: Finding) -> list:
    body = []
    if f.test_id:
        body.append("TEST")
        body.append(f"  {f.test_id}")
        body.append(_DIVIDER)
    loc = f"{f.path or '<unknown>'}:{f.line}" if f.line else (f.path or "<unknown>")
    if f.func:
        loc += f"   (in {f.func})"
    body.append("WHERE")
    body.append(f"  {loc}")

    width = max(3, len(str(f.line or 1)))
    excerpt = _excerpt(f.path, f.line, context=1)
    if excerpt:
        for n, text in excerpt:
            mark = ">>" if n == f.line else "  "
            body.append(f"{mark} {n:>{width}} | {text}")
            if n == f.line and f.col:
                col = min(f.col, len(text))
                body.append(" " * (len(mark) + 1 + width + 3 + col) + "^")
    elif f.source:
        body.append(f"  {f.line:>{width}} | {f.source}")
        if f.col:
            body.append(" " * (2 + width + 3 + f.col) + "^")

    body.append(_DIVIDER)
    body.append("WHAT WENT WRONG")
    body.append(f"  {f.kind}: {f.message}".rstrip(": "))
    body.append(_DIVIDER)
    body.append("SUGGESTIONS")
    for i, tip in enumerate(f.suggestions, 1):
        body.append(f"  {i}. {tip}")
    return body


def box_title(f: Finding, static: bool = False) -> str:
    label = "STATIC CHECK" if (f.static or static) else "MISTAKE FOUND"
    return f"{label} - {f.kind}"


def build_box(f: Finding, width: int = 88, ascii_only: bool = False) -> str:
    if not f.suggestions:
        f.suggestions = suggestions_for(f)
    return render_box(box_title(f), build_body(f), width, ascii_only)


# --------------------------------------------------------------------------
# Parsing pytest's rendered failure output
# --------------------------------------------------------------------------

_PYTEST_E_RE = re.compile(r"^(\s*)E(?=\s)\s?(.*)$")


def strip_pytest_prefixes(text: str) -> str:
    """Undo pytest's rendering so a normal traceback parser can read it.

    pytest prefixes the detail of every failure line with ``E`` (``E     File
    "x.py", line 1``) and indents the block. Removing the marker and the common
    indent recovers something close to a plain traceback.
    """
    rows = []
    for ln in text.split("\n"):
        m = _PYTEST_E_RE.match(ln)
        rows.append(m.group(1) + m.group(2) if m else ln)
    nonempty = [r for r in rows if r.strip()]
    if not nonempty:
        return "\n".join(rows)
    indent = min(len(r) - len(r.lstrip(" ")) for r in nonempty)
    if indent:
        rows = [r[indent:] if r.strip() else r for r in rows]
    return "\n".join(rows)


_PYTEST_CRASH_RE = re.compile(
    r"^(?P<path>(?:[A-Za-z]:)?[^:\n]+?):(?P<line>\d+): "
    r"(?P<exc>[A-Za-z_][\w.]*(?:Error|Exception|Interrupt|Exit|Iteration))"
    r"(?:: (?P<msg>.*))?$"
)


def parse_pytest_repr(text: str) -> "Finding | None":
    """Parse pytest's rendered longrepr (the block shown for a failed test).

    pytest ends that block with a ``path:line: ExceptionType`` crash line and
    prefixes the detail lines with ``E   ``. It is not a normal traceback, so
    ``parse_python_error`` cannot read it.
    """
    crash = None
    for ln in text.splitlines():
        m = _PYTEST_CRASH_RE.match(ln.strip())
        if m:
            crash = m
    if crash is None:
        return None

    detail = []
    for ln in text.splitlines():
        s = ln.rstrip()
        stripped = s.lstrip()
        if stripped.startswith("E ") or stripped == "E":
            detail.append(stripped[1:].strip())

    f = Finding()
    f.kind = crash.group("exc")
    f.path = crash.group("path")
    f.line = int(crash.group("line"))
    msg = (crash.group("msg") or "").strip()
    if not msg and detail:
        msg = " | ".join(dict.fromkeys(detail))
    # The crash line sometimes carries no message; the E-lines then repeat the
    # type ("ZeroDivisionError: division by zero"). Drop the redundant prefix.
    if msg.startswith(f.kind + ":"):
        msg = msg[len(f.kind) + 1:].strip()
    f.message = msg
    return f


# --------------------------------------------------------------------------
# Static syntax checking
# --------------------------------------------------------------------------


def finding_from_syntaxerror(exc: SyntaxError) -> Finding:
    f = Finding(kind=type(exc).__name__, message=(exc.msg or "").strip(),
                static=True)
    f.path = exc.filename or ""
    f.line = exc.lineno or 0
    f.source = (exc.text or "").rstrip("\n")
    if exc.offset:
        f.col = max(0, int(exc.offset) - 1)
    f.suggestions = suggestions_for(f)
    return f


def check_file(path: str) -> "Finding | None":
    """Compile `path`; return a Finding for the first syntax error, else None."""
    p = Path(path)
    if not p.is_file():
        return None
    try:
        source = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        compile(source, str(p), "exec")
    except SyntaxError as e:
        return finding_from_syntaxerror(e)
    return None
