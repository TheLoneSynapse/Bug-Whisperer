# Voice mode — talk to mistake-finder

Say *"find the mistake in demo math"* and you get the same boxed report
`mistake-box` prints, on the file you meant, read back to you out loud.

```
you (into the mic): find the mistake in demo json
   file: demos\demo_json.py  (you said 'demo json')
   ╔══════════════════════════════════════════════════════════════════╗
   ║ MISTAKE FOUND - JSONDecodeError                                  ║
   ╠══════════════════════════════════════════════════════════════════╣
   ║ WHERE                                                            ║
   ║   demos\demo_json.py:11                                          ║
   ║ >>  11 | data = json.loads("{'name': 'Alice', 'age': 25}")      ║
   ╠══════════════════════════════════════════════════════════════════╣
   ║ WHAT WENT WRONG                                                  ║
   ║   JSONDecodeError: Expecting property name enclosed in ...       ║
   ╚══════════════════════════════════════════════════════════════════╝
speaker: "JSONDecodeError in demo_json.py, line 11. Print the raw payload
          before parsing; it is probably empty or an error page, not JSON."
```

## How to activate it

```bash
voice.bat                 # interactive push-to-talk loop
```

Then, at the `>` prompt:

- **Press Enter with nothing typed** → it starts recording. Speak, then press
  Enter again to stop. (It stops on its own after `VOICE_MAX_SECONDS`.)
- **Or type a command** instead of speaking — same pipeline, no mic:
  `find the mistake in mycode` — handy for testing, and it works over SSH.
- **`q`** to quit.

Ctrl+C cancels a recording in progress.

### One-shot commands

```bash
voice.bat --text "find the mistake in demo math"   # no mic, scriptable
voice.bat --file demos\demo_json.py                # analyse one file now
voice.bat --set-file mycode.py                     # pin "the file I'm working on"
voice.bat --list-mics                              # what microphones exist
voice.bat --once                                   # one turn, then exit
voice.bat --no-speak                               # print the box, stay silent
voice.bat --ascii                                  # plain +-| box
```

## Which file does it check?

Three ways, in order:

1. **A file you name out loud** — resolved against every `.py` file in the
   workspace, ignoring `.venv`, `.bob`, `__pycache__`, etc. It understands
   spoken punctuation, so *"demo underscore math"*, *"demo math"* and
   `"demo_math.py"` all land on `demos/demo_math.py`. It tells you which file
   it chose and why (`you said 'demo math'`), so a wrong guess is obvious.
2. **The pinned file** — `.voice_current`, set by `--set-file`, or automatically
   after every successful lookup. This is the closest thing to "the file I have
   open".
3. **The most recently modified `.py`** in the workspace — the file you were
   just editing. The agent's own source is never picked.

To make "the file I have open" literal in VS Code, run the task
**`voice: pin open file`** (`.vscode/tasks.json`, bound to `${file}`), or bind
it to a key. Then every voice request targets that editor's file until you say
a different name.

> The agent cannot read your editor's active tab directly — that needs an
> extension. The pin task is the honest, portable substitute.

## What happens on each turn

```
mic ──ffmpeg──▶ WAV ──Watson STT──▶ transcript
                                     │
                      file recognition (or pinned / most recent)
                                     │
                        run the file, parse the traceback
                                     │
                   box printed  +  one-line summary spoken by Watson TTS
```

- **A find request** (`find` / `check` / `mistake` / `bug` / `error` …) runs the
  analysis and prints the box.
- **A question** (*"why does a KeyError happen in pandas"*) is sent to
  **Granite** on watsonx.ai and the answer is spoken — so it is a voice agent,
  not just a command runner.

## Setup

`.env` (gitignored) holds the credentials; `.env.example` is the template.

| Variable | What it is |
|---|---|
| `IBM_API_KEY` | IBM Cloud IAM API key — https://cloud.ibm.com/iam/apikeys |
| `IBM_STT_URL` | Watson Speech to Text instance URL |
| `IBM_TTS_URL` | Watson Text to Speech instance URL |
| `IBM_TTS_VOICE` | e.g. `en-US_AllisonV3Voice`, `en-US_EmmaExpressive` |
| `WATSONX_URL` / `WATSONX_PROJECT_ID` / `WATSONX_MODEL` | Granite for free-form questions |
| `VOICE_MIC` | microphone name (`voice.bat --list-mics`); blank = first device |
| `FFMPEG` | path to a DirectShow-capable ffmpeg; blank = auto-discover |

### Dependencies

Only what is already installed: `requests` (in `.venv`), stdlib `winsound` for
playback, and an **ffmpeg with DirectShow support** for the microphone. No pip
installs.

The stock `ffmpeg.exe` bundled with some apps is built `--disable-indevs` and
**cannot record**. This machine has a usable one inside the Wand capture app;
`find_ffmpeg()` discovers it automatically and picks the first build whose
`-devices` output lists `dshow`. If yours ever breaks, drop a full ffmpeg build
somewhere and set `FFMPEG=` in `.env`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no DirectShow-capable ffmpeg found` | Set `FFMPEG=` in `.env` to a normal ffmpeg build. |
| Wrong microphone used | `voice.bat --list-mics`, then copy the exact name into `VOICE_MIC`. |
| `IBM rejected the API key` | Key rotated or wrong — update `IBM_API_KEY` in `.env`. |
| Box says `NO MISTAKE - TIMED OUT` | The file blocks (waits for input / long work); raise `VOICE_RUN_TIMEOUT`. |
| Nothing heard | Speak within ~15 s of the recording start; check `VOICE_MAX_SECONDS`. |
| It picks the wrong file | Say the name more clearly, or `--set-file` to pin it. |

## Security

`.env` is in `.gitignore` — never commit it or paste its key anywhere public.
If a key leaks, disable it on the IAM page and put the new one in `.env`; the
agent reads it fresh on the next run.
