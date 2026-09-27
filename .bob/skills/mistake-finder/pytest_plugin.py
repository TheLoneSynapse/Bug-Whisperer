"""mistake-finder pytest plugin - box every failing test automatically.

Once this package is installed, pytest discovers the plugin through the
``pytest11`` entry point, so **any** test run - in any IDE, terminal, or CI that
uses the same Python environment - ends with a boxed report for each failing
test: WHERE (file:line + source), WHAT WENT WRONG (exception + message), and
SUGGESTIONS (concrete fixes for that exception).

Turn it off for one run with ``--no-mistake-box``, or globally with the
environment variable ``MISTAKE_BOX=0``.
"""

from __future__ import annotations

import os

try:  # installed as a package
    from . import box
except ImportError:  # loaded by path (e.g. PYTEST_PLUGINS)
    import box  # type: ignore[no-redef]

_ENV = "MISTAKE_BOX"
_OFF = {"0", "false", "no", "off"}


def pytest_addoption(parser) -> None:
    group = parser.getgroup("mistake-finder")
    group.addoption(
        "--mistake-box",
        action="store_true",
        dest="mistake_box",
        default=None,
        help="print failing tests as boxed mistake reports (default: on)",
    )
    group.addoption(
        "--no-mistake-box",
        action="store_false",
        dest="mistake_box",
        default=None,
        help="disable mistake-finder boxed failure reports",
    )


def pytest_configure(config) -> None:
    # Ask for UTF-8 so the pretty box survives a cp1252 Windows console.
    box.prepare_stdout()


def _enabled(config) -> bool:
    try:
        value = config.getoption("mistake_box")
    except (ValueError, AttributeError):
        value = None
    if value is not None:
        return bool(value)
    return os.environ.get(_ENV, "1").strip().lower() not in _OFF


def _box_width(terminalreporter) -> int:
    tw = getattr(terminalreporter, "_tw", None)
    full = getattr(tw, "fullwidth", 90)
    try:
        full = int(full)
    except (TypeError, ValueError):
        full = 90
    return max(60, min(100, full - 2))


def _finding_from_report(report) -> "box.Finding":
    text = ""
    longrepr = getattr(report, "longrepr", None)
    if longrepr is not None:
        try:
            text = str(longrepr)
        except Exception:  # never let a weird repr break the run
            text = ""

    finding = (
        box.parse_pytest_repr(text)
        or box.parse_python_error(box.strip_pytest_prefixes(text))
        or box.parse_python_error(text)
    )
    if finding is None:
        finding = box.Finding(kind="Error", message=_last_meaningful_line(text))
    finding.test_id = getattr(report, "nodeid", "") or ""
    when = getattr(report, "when", "call")
    if when != "call" and not finding.message:
        finding.message = f"{when} phase failed"
    if not finding.kind:
        finding.kind = "Error"
    finding.suggestions = box.suggestions_for(finding)
    return finding


def _last_meaningful_line(text: str) -> str:
    for line in reversed(text.splitlines()):
        if line.strip():
            return line.strip()
    return "test failed"


def _collect(terminalreporter) -> list:
    stats = getattr(terminalreporter, "stats", {}) or {}
    reports = []
    for key in ("failed", "error"):
        reports.extend(stats.get(key, []) or [])

    # One box per test: prefer the call-phase report when a test failed in both.
    chosen, order = {}, []
    for rep in reports:
        nid = getattr(rep, "nodeid", "?")
        prev = chosen.get(nid)
        if prev is None:
            chosen[nid] = rep
            order.append(nid)
        elif getattr(rep, "when", "") == "call" and getattr(prev, "when", "") != "call":
            chosen[nid] = rep
    return [chosen[nid] for nid in order]


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    if not _enabled(config):
        return
    try:
        findings = [_finding_from_report(r) for r in _collect(terminalreporter)]
    except Exception as exc:  # pragma: no cover - defensive
        terminalreporter.write_line(f"mistake-finder: {exc}", red=True)
        return
    if not findings:
        return

    width = _box_width(terminalreporter)
    terminalreporter.write_sep(
        "=", f"mistake-finder: {len(findings)} failure(s) as boxes")
    for finding in findings:
        print("")
        box.emit(box.box_title(finding), box.build_body(finding), width)
