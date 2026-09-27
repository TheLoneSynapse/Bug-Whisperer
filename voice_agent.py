#!/usr/bin/env python3
"""voice_agent.py - talk to mistake-finder.

Speak -> Watson Speech to Text -> work out which file you meant -> run it ->
print the same boxed report `mistake-box` prints -> read it back with Watson
Text to Speech.

Zero third-party installs: `requests` (already in .venv), stdlib `winsound`
for playback, and an ffmpeg that supports DirectShow for microphone capture.

Usage (see VOICE.md):
    voice.bat                              # interactive push-to-talk loop
    voice.bat --once                       # one turn, then exit
    voice.bat --text "find demo math"      # no mic: run a spoken-style command
    voice.bat --file demos\\demo_math.py   # analyse one file directly
    voice.bat --pin mycode.py             # pin "the file I am working on"
    voice.bat --set-file mycode.py        # alias for --pin
    voice.bat --list-mics
    voice.bat --no-speak                   # print the box, do not read aloud

Which file does it analyse?
    1. a file you name out loud  ("find the mistake in demo math")
    2. otherwise the pinned file  (.voice_current, set by --pin / --set-file)
    3. otherwise the most recently modified .py file in the workspace

Commands at the > prompt:
    (Enter)                  record from mic
    find / check / mistake   run analysis on the target file
    pin <path>               pin a file, e.g.  pin tests/pandas.test.py
    pin                      show the currently pinned file
    help                     show this command list
    q / quit                 exit
"""

from __future__ import annotations

import argparse
import glob
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from difflib import SequenceMatcher
from pathlib import Path

# --------------------------------------------------------------------------
# Project wiring
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / ".bob" / "skills" / "mistake-finder"
STATE_FILE = ROOT / ".voice_current"

SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", ".pytest_cache",
             "node_modules", ".freebuff", ".bob", "build", "dist",
             ".mypy_cache", ".ruff_cache", "site-packages"}

CODE_EXTS = {".py"}


def load_box():
    """Import the skill's dependency-free `box` module."""
    if str(SKILL_DIR) not in sys.path:
        sys.path.insert(0, str(SKILL_DIR))
    try:
        return importlib.import_module("box")
    except ImportError:
        sys.exit(f"voice-agent: cannot find {SKILL_DIR / 'box.py'}\n"
                 "Run this from the project root.")


# --------------------------------------------------------------------------
# .env loading (no python-dotenv: this stays dependency-free)
# --------------------------------------------------------------------------


def load_env(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines into os.environ without overwriting real env vars."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class Config:
    def __init__(self) -> None:
        self.api_key = os.environ.get("IBM_API_KEY", "").strip()
        self.stt_url = os.environ.get("IBM_STT_URL", "").strip().rstrip("/")
        self.stt_model = os.environ.get("IBM_STT_MODEL", "en-US_BroadbandModel").strip()
        self.tts_url = os.environ.get("IBM_TTS_URL", "").strip().rstrip("/")
        self.tts_voice = os.environ.get("IBM_TTS_VOICE", "en-US_AllisonV3Voice").strip()
        self.watsonx_url = os.environ.get("WATSONX_URL", "").strip().rstrip("/")
        self.watsonx_project = os.environ.get("WATSONX_PROJECT_ID", "").strip()
        self.watsonx_model = os.environ.get("WATSONX_MODEL", "ibm/granite-4-h-small").strip()
        self.mic = os.environ.get("VOICE_MIC", "").strip()
        try:
            self.max_seconds = int(os.environ.get("VOICE_MAX_SECONDS", "15"))
        except ValueError:
            self.max_seconds = 15

    def require_voice(self) -> None:
        missing = [n for n, v in (("IBM_API_KEY", self.api_key),
                                  ("IBM_STT_URL", self.stt_url),
                                  ("IBM_TTS_URL", self.tts_url)) if not v]
        if missing:
            sys.exit("voice-agent: missing from .env -> " + ", ".join(missing) +
                     "\nCopy .env.example to .env and fill it in (see VOICE.md).")


# --------------------------------------------------------------------------
# IAM token (cached, refreshed when close to expiry)
# --------------------------------------------------------------------------

_token = {"value": "", "expires": 0.0}


def iam_token(cfg: Config) -> str:
    if _token["value"] and time.time() < _token["expires"] - 60:
        return _token["value"]
    import requests
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey",
              "apikey": cfg.api_key},
        headers={"Accept": "application/json"}, timeout=30)
    if resp.status_code != 200:
        detail = resp.text[:300]
        sys.exit(f"voice-agent: IBM rejected the API key ({resp.status_code}): {detail}")
    payload = resp.json()
    _token["value"] = payload["access_token"]
    _token["expires"] = time.time() + float(payload.get("expires_in", 3600))
    return _token["value"]


# --------------------------------------------------------------------------
# ffmpeg discovery - we need a build with DirectShow (--enable-indevs)
# --------------------------------------------------------------------------


def _ffmpeg_candidates() -> list:
    out = []
    if os.environ.get("FFMPEG"):
        out.append(os.environ["FFMPEG"])
    found = shutil.which("ffmpeg")
    if found:
        out.append(found)
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        out += sorted(glob.glob(os.path.join(local, "Wand", "app-*", "resources",
                                             "app.asar.unpacked", "static",
                                             "unpacked", "capture", "release",
                                             "bin", "64bit", "ffmpeg.exe")),
                      reverse=True)
        out.append(os.path.join(local, "DigitalWave", "DW Free Video Downloader",
                                "ffmpeg.exe"))
    out += ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]
    return [p for p in out if p and Path(p).is_file()]


def find_ffmpeg() -> str:
    for path in _ffmpeg_candidates():
        try:
            out = subprocess.run([path, "-hide_banner", "-devices"],
                                 capture_output=True, text=True, timeout=20)
        except Exception:
            continue
        if "dshow" in (out.stdout + out.stderr):
            return path
    sys.exit("voice-agent: no DirectShow-capable ffmpeg found.\n"
             "Set FFMPEG=/path/to/ffmpeg.exe in .env (a normal full build), "
             "or install one.")


def list_mics(ffmpeg: str) -> list:
    """Return (display_name, dshow_id) pairs for every audio input device.

    Uses raw bytes so the device name is never mangled by console encoding.
    Falls back to the display name as the dshow_id when no alternative line follows.
    """
    proc = subprocess.run([ffmpeg, "-hide_banner", "-list_devices", "true",
                           "-f", "dshow", "-i", "dummy"],
                          capture_output=True)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    mics = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.search(r'"([^"]+)"\s*\(audio\)', lines[i])
        if m:
            display = m.group(1)
            # look ahead for the "Alternative name" line
            alt_id = display          # default: use display name
            if i + 1 < len(lines):
                alt_m = re.search(r'Alternative name\s+"([^"]+)"', lines[i + 1])
                if alt_m:
                    alt_id = alt_m.group(1)
                    i += 1            # skip the alt line
            mics.append((display, alt_id))
        i += 1
    return mics


def _mic_key(name: str) -> str:
    """Compare device names ignoring punctuation and console-encoding damage."""
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def pick_mic(ffmpeg: str, wanted: str) -> tuple:
    """Return (display_name, dshow_id) for the best-matching mic."""
    mics = list_mics(ffmpeg)
    if not mics:
        sys.exit("voice-agent: no microphone found (is one plugged in and allowed?)")
    if wanted:
        # exact display-name match
        for display, alt_id in mics:
            if wanted == display:
                return display, alt_id
        key = _mic_key(wanted)
        # fuzzy display-name match
        for display, alt_id in mics:
            other = _mic_key(display)
            if key and (key in other or other in key):
                return display, alt_id
        scored = sorted(mics,
                        key=lambda t: SequenceMatcher(None, key, _mic_key(t[0])).ratio(),
                        reverse=True)
        if scored and SequenceMatcher(None, key, _mic_key(scored[0][0])).ratio() >= 0.8:
            return scored[0]
        print(f"voice-agent: mic '{wanted}' not found. Available:")
        for display, _ in mics:
            print(f"   - {display}")
        print(f"  using '{mics[0][0]}'.")
    return mics[0]


# --------------------------------------------------------------------------
# Record -> transcribe
# --------------------------------------------------------------------------


def record(ffmpeg: str, mic: tuple, max_seconds: int, stop_on_enter: bool = True) -> Path:
    """Record from the microphone until Enter (or max_seconds) and return a WAV.

    mic is a (display_name, dshow_id) tuple returned by pick_mic().
    The dshow_id is the alternative @device_cm_ path which survives encoding
    issues that corrupt the display name.
    """
    display, dshow_id = mic
    wav = Path(tempfile.gettempdir()) / f"mf_voice_{os.getpid()}.wav"
    dshow_arg = f"audio={dshow_id}"
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-f", "dshow", "-i", dshow_arg,
           "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    stop = threading.Event()
    if stop_on_enter:
        def wait_enter():
            try:
                input()
            except EOFError:
                pass
            stop.set()
        threading.Thread(target=wait_enter, daemon=True).start()

    print("   recording... ", end="", flush=True)
    deadline = time.time() + max_seconds
    if stop_on_enter:
        print("(press Enter to stop)", flush=True)
    while time.time() < deadline and not stop.is_set():
        if proc.poll() is not None:          # ffmpeg died early
            break
        time.sleep(0.05)
    print("   done.", flush=True)

    if proc.poll() is None:
        try:                                  # 'q' makes ffmpeg finalise the WAV
            proc.stdin.write(b"q")
            proc.stdin.flush()
            proc.wait(timeout=10)
        except Exception:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
    if proc.poll() not in (0, None) and not wav.is_file():
        err = (proc.stderr.read() or b"").decode("utf-8", "replace")[:300]
        sys.exit(f"voice-agent: recording failed.\n{err}")
    return wav


def transcribe(cfg: Config, wav: Path) -> str:
    import requests
    data = wav.read_bytes()
    resp = requests.post(
        f"{cfg.stt_url}/v1/recognize",
        headers={"Authorization": "Bearer " + iam_token(cfg),
                 "Content-Type": "audio/wav"},
        params={"model": cfg.stt_model},
        data=data, timeout=120)
    if resp.status_code != 200:
        sys.exit(f"voice-agent: STT failed ({resp.status_code}): {resp.text[:300]}")
    results = resp.json().get("results", [])
    if not results:
        return ""
    return results[0]["alternatives"][0]["transcript"].strip()


def speak(cfg: Config, text: str) -> None:
    """Read `text` aloud. Silently does nothing if audio playback is unavailable."""
    if not text.strip():
        return
    try:
        import requests
        resp = requests.post(
            f"{cfg.tts_url}/v1/synthesize",
            headers={"Authorization": "Bearer " + iam_token(cfg),
                     "Content-Type": "application/json",
                     "Accept": "audio/wav"},
            params={"voice": cfg.tts_voice},
            json={"text": text[:1400]}, timeout=120)
        if resp.status_code != 200:
            print(f"voice-agent: TTS failed ({resp.status_code})", file=sys.stderr)
            return
        wav = Path(tempfile.gettempdir()) / f"mf_say_{os.getpid()}.wav"
        wav.write_bytes(resp.content)
        try:
            import winsound
            winsound.PlaySound(str(wav), winsound.SND_FILENAME)
        except ImportError:
            print(f"voice-agent: (audio written to {wav}; no winsound on this OS)",
                  file=sys.stderr)
    except Exception as exc:                    # speech is a nicety, never fatal
        print(f"voice-agent: could not speak: {exc}", file=sys.stderr)


def ask_granite(cfg: Config, question: str) -> str:
    """Free-form question -> Granite answer (used when it is not a find request)."""
    if not (cfg.watsonx_url and cfg.watsonx_project):
        return ("I did not catch a file name. Say something like "
                "'find the mistake in demo math'.")
    import requests
    body = {
        "model_id": cfg.watsonx_model,
        "project_id": cfg.watsonx_project,
        "messages": [
            {"role": "system", "content":
                "You are mistake-finder, a terse Python debugging assistant. "
                "Answer in at most three sentences, plain prose, no markdown."},
            {"role": "user", "content": question},
        ],
        "parameters": {"max_tokens": 220, "temperature": 0.2},
    }
    resp = requests.post(f"{cfg.watsonx_url}/ml/v1/text/chat",
                         headers={"Authorization": "Bearer " + iam_token(cfg),
                                  "Content-Type": "application/json",
                                  "Accept": "application/json"},
                         params={"version": "2024-10-08"},
                         json=body, timeout=120)
    if resp.status_code != 200:
        return f"Granite returned {resp.status_code}."
    return resp.json()["choices"][0]["message"]["content"].strip()


# --------------------------------------------------------------------------
# Which file did they mean?
# --------------------------------------------------------------------------

# Words that carry no file information.
STOPWORDS = {
    "find", "found", "check", "checks", "search", "look", "please", "the", "a",
    "an", "in", "on", "at", "for", "of", "to", "my", "me", "this", "that",
    "mistake", "mistakes", "error", "errors", "bug", "bugs", "problem",
    "problems", "issue", "issues", "wrong", "review", "debug", "code", "file",
    "files", "open", "opened", "currently", "and", "it", "is", "are", "what",
    "show", "give", "tell", "run", "analyse", "analyze", "detect", "scan",
    "hey", "ok", "okay", "now", "up", "with",
}

FIND_WORDS = {"find", "check", "mistake", "mistakes", "error", "errors", "bug",
              "bugs", "review", "debug", "wrong", "problem", "problems",
              "issue", "issues", "detect", "scan", "analyse", "analyze"}

QUESTION_WORDS = {"what", "why", "how", "when", "which", "explain", "mean",
                  "means", "difference", "should", "can", "does", "do"}


def normalise(text: str) -> str:
    """Turn spoken punctuation into the characters it stands for."""
    out = text.lower()
    for spoken, symbol in (("underscore", "_"), ("dot py", ".py"),
                           ("dot p y", ".py"), ("dot", "."),
                           ("slash", "/"), ("backslash", "/"),
                           ("dash", "-"), ("hyphen", "-")):
        out = out.replace(spoken, symbol)
    out = re.sub(r"[^\w./\\-]+", " ", out)
    return re.sub(r"\s+", " ", out).strip()


def index_code_files(root: Path = ROOT) -> list:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix in CODE_EXTS:
                files.append(Path(dirpath) / name)
    return sorted(files)


def _aliases(path: Path) -> set:
    """Every spelling of a file a person might say out loud."""
    stem = path.stem
    names = {
        stem.lower(),
        stem.lower().replace("_", " "),
        stem.lower().replace("_", ""),
        path.name.lower(),
        path.name.lower().replace("_", " "),
    }
    try:
        rel = path.relative_to(ROOT)
        names.add(str(rel).lower())
        names.add(str(rel).lower().replace("_", " ").replace("\\", " ")
                  .replace("/", " "))
    except ValueError:
        pass
    return {n for n in names if n}


def _tokens(text: str) -> set:
    return {t for t in re.split(r"[\s.]+", text) if t}


def resolve_file(transcript: str, files: list):
    """Return (path, why) for the file the utterance names, else (None, "")."""
    clean = normalise(transcript)
    spoken = " ".join(t for t in clean.split() if t not in STOPWORDS)
    if not spoken:
        return None, ""

    spoken_tokens = _tokens(spoken)
    best, best_score, best_reason = None, 0.0, ""

    for path in files:
        for alias in _aliases(path):
            alias_tokens = _tokens(alias)
            if not alias_tokens:
                continue
            # every word of the alias was said -> strong hit
            contained = alias_tokens <= spoken_tokens
            overlap = len(alias_tokens & spoken_tokens) / len(alias_tokens)
            fuzzy = SequenceMatcher(None, spoken, alias).ratio()

            if contained:
                score, reason = 1.0, f"you said '{alias}'"
            elif overlap >= 0.5:
                score, reason = overlap, f"you said '{alias}'"
            elif fuzzy >= 0.75:
                score, reason = fuzzy * 0.8, f"closest match to '{spoken}'"
            else:
                continue

            # prefer matches on longer (more specific) aliases
            score += 0.001 * len(alias_tokens)
            if score > best_score:
                best, best_score, best_reason = path, score, reason

    if best is None or best_score < 0.6:
        return None, ""
    return best, best_reason


def pinned_file():
    if STATE_FILE.is_file():
        try:
            raw = STATE_FILE.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if raw:
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = ROOT / candidate
            if candidate.is_file():
                return candidate
    return None


def set_pinned(path: str) -> Path:
    candidate = Path(path)
    if not candidate.is_file():
        sys.exit(f"voice-agent: no such file: {path}")
    try:
        candidate = candidate.relative_to(ROOT)
    except ValueError:
        pass
    STATE_FILE.write_text(str(candidate), encoding="utf-8")
    return candidate


def most_recent_code_file(files: list):
    """The file you are most likely editing: newest mtime wins.

    The agent's own source is skipped - we have just written it, so it would
    always win and is never what you meant.
    """
    me = Path(__file__).resolve()
    best, best_mtime = None, 0.0
    for path in files:
        if path.resolve() == me:
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > best_mtime:
            best, best_mtime = path, mtime
    return best


def current_file(files: list):
    """The file to analyse when nothing was named out loud."""
    pinned = pinned_file()
    if pinned is not None:
        return pinned, "the pinned file"
    recent = most_recent_code_file(files)
    if recent is not None:
        return recent, "most recently modified"
    return None, ""


# --------------------------------------------------------------------------
# Run the file and box the mistake
# --------------------------------------------------------------------------


def _passthrough(text: str) -> None:
    """Write a child process's output without dying on console-encoding gaps."""
    try:
        sys.stdout.write(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        sys.stdout.write(text.encode(encoding, "replace").decode(encoding, "replace"))
    sys.stdout.flush()


def run_timeout() -> int:
    try:
        return int(os.environ.get("VOICE_RUN_TIMEOUT", "30"))
    except ValueError:
        return 30


def analyze(box, target: Path, width: int = 88, ascii_only: bool = False):
    """Return (box_text, spoken_summary, finding_or_None)."""
    finding = box.check_file(str(target))
    if finding is not None:
        text = box.build_box(finding, width, ascii_only)
        return text, _summary(finding, target), finding

    # stdin is /dev/null so a file that waits for input (or the agent itself)
    # gets EOF instead of hanging us; the timeout is the backstop for anything
    # that blocks without reading stdin.
    try:
        proc = subprocess.run([sys.executable, str(target)],
                              stdin=subprocess.DEVNULL,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              cwd=str(ROOT), timeout=run_timeout())
    except subprocess.TimeoutExpired:
        text = box.render_box(
            "NO MISTAKE - TIMED OUT",
            [f"  {target.name} was still running after {run_timeout()}s.",
             "  It may be waiting for input or doing long work; not analysed."],
            width, ascii_only)
        return text, f"{target.name} timed out, so I did not analyse it.", None

    if proc.stdout:
        _passthrough(proc.stdout)

    finding = box.parse_python_error(proc.stderr or "")
    if finding is not None:
        finding.suggestions = box.suggestions_for(finding)
        text = box.build_box(finding, width, ascii_only)
        return text, _summary(finding, target), finding

    if proc.stderr and proc.stderr.strip():
        body = ["  " + ln for ln in proc.stderr.rstrip().splitlines()][:20]
        return box.render_box("UNRECOGNIZED OUTPUT", body, width, ascii_only), \
            f"I could not classify the failure in {target.name}.", None

    text = box.render_box("NO MISTAKES DETECTED",
                          [f"  {target.name} ran clean."], width, ascii_only)
    return text, f"No mistakes detected in {target.name}.", None


def _summary(finding, target: Path) -> str:
    """A short sentence to read aloud - the box has the detail."""
    where = f"{target.name}"
    if finding.line:
        where += f", line {finding.line}"
    what = f"{finding.kind}"
    if finding.message:
        what += f": {finding.message}"
    spoken = f"{what} in {where}."
    if finding.suggestions:
        spoken += " " + finding.suggestions[0]
    return spoken


def emit_box(box, text: str) -> None:
    box.prepare_stdout()
    print()
    print(text)
    print()


# --------------------------------------------------------------------------
# Turn handling
# --------------------------------------------------------------------------


def handle_text(box, cfg: Config, utterance: str, files: list,
                speak_reply: bool, ascii_only: bool) -> None:
    """One turn: decide whether it is a find request or a question."""
    utterance = utterance.strip()
    if not utterance:
        print("   (nothing heard)")
        return

    # built-in prompt commands
    low_raw = utterance.lower().strip()

    if low_raw in {"help", "?", "h"}:
        print("  Commands:")
        print("    (Enter)               record from mic")
        print("    find / check          run analysis on the target file")
        print("    pin <path>            pin a file  e.g. pin tests/pandas.test.py")
        print("    pin                   show currently pinned file")
        print("    q / quit              exit")
        return

    if low_raw == "pin" or low_raw.startswith("pin "):
        path_arg = utterance[3:].strip()
        if path_arg:
            try:
                pinned = set_pinned(path_arg)
                print(f"   pinned: {pinned}")
            except SystemExit as e:
                print(f"   {e}")
        else:
            pinned = pinned_file()
            print(f"   currently pinned: {pinned or '(nothing)'}")
        return

    target, why = resolve_file(utterance, files)
    low = normalise(utterance)
    words = set(low.split())
    is_question = bool(words & QUESTION_WORDS) and not (
        words & {"find", "check", "mistake", "mistakes", "bug", "bugs"})
    wants_find = bool(words & FIND_WORDS) or target is not None

    if wants_find and not is_question:
        if target is None:
            target, why = current_file(files)
        if target is None:
            print("   no .py file found to check.")
            print("   tip: type  pin <path>  to set the file, e.g.  pin tests/sklearn.test.py")
            return
        print(f"   file: {target}  ({why})")
        text, summary, _ = analyze(box, target, ascii_only=ascii_only)
        emit_box(box, text)
        if speak_reply:
            speak(cfg, summary)
        set_pinned(str(target))
        return

    # Not a find request: answer it with Granite.
    print("   asking Granite...")
    answer = ask_granite(cfg, utterance)
    print(f"   {answer}\n")
    if speak_reply:
        speak(cfg, answer)


def interactive(box, cfg: Config, once: bool, speak_reply: bool,
                ascii_only: bool) -> int:
    cfg.require_voice()
    ffmpeg = find_ffmpeg()
    mic = pick_mic(ffmpeg, cfg.mic)
    files = index_code_files()

    pinned = pinned_file()
    recent = most_recent_code_file(files) if pinned is None else None
    active = pinned or recent

    print("=" * 62)
    print("  mistake-finder  -  voice mode")
    print("=" * 62)
    print(f"  mic    : {mic[0]}")
    print(f"  files  : {len(files)} .py in this workspace")
    print(f"  speech : {'on' if speak_reply else 'off'}")
    if active:
        src = "pinned" if pinned else "most recent"
        print(f"  target : {active.name}  ({src})")
        print(f"           to change: type  pin <path>  or run the")
        print(f"           'voice: pin open file' task in VS Code.")
    else:
        print(f"  target : (none — say or type a file name)")
    print()
    print("  Press Enter to talk, then Enter again to stop.")
    print("  Type a command instead (e.g. 'find demo math'), or 'q' to quit.")
    print("=" * 62)

    while True:
        try:
            typed = input("\n  > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Bye!")
            return 0

        if typed.lower() in {"q", "quit", "exit"}:
            print("  Bye!")
            return 0

        if typed:
            handle_text(box, cfg, typed, files, speak_reply, ascii_only)
        else:
            try:
                wav = record(ffmpeg, mic, cfg.max_seconds)
            except KeyboardInterrupt:
                print("\n  recording cancelled.")
                continue
            print("   transcribing...", flush=True)
            utterance = transcribe(cfg, wav)
            print(f"   heard: \"{utterance}\"")
            try:
                wav.unlink()
            except OSError:
                pass
            handle_text(box, cfg, utterance, files, speak_reply, ascii_only)

        if once:
            return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="voice-agent", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--once", action="store_true",
                        help="handle a single turn, then exit")
    parser.add_argument("--text", metavar="UTTERANCE",
                        help="run a spoken-style command without the microphone")
    parser.add_argument("--file", metavar="PATH",
                        help="analyse this file now (no speech)")
    parser.add_argument("--pin", "--set-file", dest="set_file", metavar="PATH",
                        help="pin this file as 'the file I am working on'")
    parser.add_argument("--list-mics", action="store_true",
                        help="list microphones and exit")
    parser.add_argument("--no-speak", action="store_true",
                        help="print the box but do not read it aloud")
    parser.add_argument("--ascii", action="store_true",
                        help="use the plain +-| box")
    parser.add_argument("--width", type=int, default=88, help="box width")
    args = parser.parse_args(argv)

    load_env()
    box = load_box()
    box.prepare_stdout()
    cfg = Config()

    if args.list_mics:
        ffmpeg = find_ffmpeg()
        for display, _ in list_mics(ffmpeg):
            print(display)
        return 0

    if args.set_file:
        print(f"pinned: {set_pinned(args.set_file)}")
        return 0

    speak_reply = not args.no_speak

    if args.file:
        if speak_reply:
            cfg.require_voice()
        target = set_pinned(args.file)
        text, summary, _ = analyze(box, target, args.width, args.ascii)
        emit_box(box, text)
        if speak_reply:
            speak(cfg, summary)
        return 0

    if args.text:
        files = index_code_files()
        if speak_reply:
            cfg.require_voice()
        handle_text(box, cfg, args.text, files, speak_reply, args.ascii)
        return 0

    return interactive(box, cfg, args.once, speak_reply, args.ascii)


if __name__ == "__main__":
    raise SystemExit(main())
