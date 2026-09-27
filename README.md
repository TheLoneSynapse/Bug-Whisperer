# 🐛 Bug Whisperer — Find Mistakes in Your Code Automatically

> **Made for the IBM Bob 2.0 Hackathon (lablab.ai)**
> A skill for IBM Bob that finds your coding mistakes, explains them in plain English, and fixes them — automatically.

---

## 📖 Table of Contents

1. [What is this?](#-what-is-this)
2. [What does it do?](#-what-does-it-do)
3. [What do I need before I start?](#-what-do-i-need-before-i-start)
4. [Step 1 — Download the project](#-step-1--download-the-project)
5. [Step 2 — Install Python](#-step-2--install-python)
6. [Step 3 — Install the tool](#-step-3--install-the-tool)
7. [Step 4 — Use it in IBM Bob IDE](#-step-4--use-it-in-ibm-bob-ide)
8. [Step 5 — Use it in your Terminal](#-step-5--use-it-in-your-terminal)
9. [Step 6 — Use it with your Voice](#-step-6--use-it-with-your-voice)
10. [Example: What the output looks like](#-example-what-the-output-looks-like)
11. [Troubleshooting](#-troubleshooting)
12. [Project File Map](#-project-file-map)

---

## 🤔 What is this?

**Bug Whisperer** is a tool that reads your Python code and tells you exactly **what went wrong**, **where it went wrong**, and **how to fix it** — in simple, friendly language.

Think of it like a helpful teacher looking over your shoulder while you code. When something breaks, instead of seeing a scary red error message, you see a neat box that says:

- 📍 **WHERE** the mistake is (exact file and line number)
- ❌ **WHAT WENT WRONG** (explained in plain English)
- 💡 **SUGGESTIONS** (step-by-step tips to fix it)

---

## ✨ What does it do?

It has **two main modes**:

### Mode 1 — Fix Failing Tests 🔴→🟢
When your tests are failing (showing red errors), Bug Whisperer:
1. Looks at every failing test at the same time (in parallel)
2. Figures out the root cause of each failure
3. Applies the smallest possible fix
4. Checks if the fix worked — if not, it undoes it and tries again

### Mode 2 — Review Your Code 🔍
When you just wrote some code and want a second opinion, Bug Whisperer:
1. Checks for logic errors and edge cases
2. Checks for security issues
3. Checks for missing error handling
4. Gives you a ranked list of findings with evidence

---

## 📋 What do I need before I start?

You need **3 things** installed on your computer:

| Thing | What it is | Where to get it |
|-------|-----------|-----------------|
| **Python 3.8 or newer** | The programming language this tool uses | [python.org/downloads](https://python.org/downloads) |
| **Git** | A tool to download code from GitHub | [git-scm.com](https://git-scm.com/downloads) |
| **IBM Bob IDE** | The AI coding assistant this skill runs inside | [IBM Bob](https://www.ibm.com/products/bob) |

> 💡 **Not sure if you have Python?** Open a terminal (Command Prompt on Windows) and type:
> ```
> python --version
> ```
> If you see something like `Python 3.11.0` — you're good! If you see an error, follow Step 2 below.

---

## 📥 Step 1 — Download the project

Open your **Terminal** (on Windows: press `Windows key + R`, type `cmd`, press Enter).

Copy and paste this command, then press **Enter**:

```bash
git clone https://github.com/TheLoneSynapse/Bug-Whisperer.git
```

Then move into the downloaded folder:

```bash
cd Bug-Whisperer
```

> ✅ You should now see a folder called `Bug-Whisperer` on your computer.

---

## 🐍 Step 2 — Install Python

> **Skip this step if you already have Python 3.8 or newer.**

### On Windows:
1. Go to [https://python.org/downloads](https://python.org/downloads)
2. Click the big yellow **"Download Python"** button
3. Run the installer
4. ⚠️ **IMPORTANT:** On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install
5. Click **"Install Now"**
6. When it's done, close and reopen your terminal, then type `python --version` to confirm

### On Mac:
1. Go to [https://python.org/downloads](https://python.org/downloads)
2. Download the macOS installer and run it
3. Follow the on-screen steps

### On Linux:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

## ⚙️ Step 3 — Install the tool

Make sure you are inside the `Bug-Whisperer` folder in your terminal. Then run:

```bash
pip install .
```

> This command reads the project and installs everything automatically. It takes about 10–30 seconds.

**What this does:**
- Installs a command called `mistake-box` that you can use anywhere
- Installs a pytest plugin that automatically shows errors in a friendly box every time you run tests

> ✅ If you see no red errors, installation was successful!

### Install the skill into IBM Bob (global — works in every project)

```bash
python install_skill.py
```

> This copies the skill into IBM Bob so it's available in every project you open.

To check if it worked:
```bash
python install_skill.py --check
```

To uninstall it later:
```bash
python install_skill.py --remove
```

---

## 🤖 Step 4 — Use it in IBM Bob IDE

### First time setup (do this once):
1. Open **IBM Bob IDE**
2. Open this project folder (`Bug-Whisperer`) in Bob
3. Go to **Settings → Skills**
4. Confirm you can see `mistake-finder` in the list
5. *(Optional)* Go to **Settings → Auto-Approve → Skills** and turn it **ON** — this means Bob won't ask for permission every time

### Using it day-to-day:

Open a **conversation** in Bob (make sure you're in **Agent mode**), then just type naturally:

---

**If your tests are failing:**
```
Run mistake-finder on the failing tests.
```

**If you just wrote some code and want it reviewed:**
```
Check my code for mistakes.
```

**To review a specific file:**
```
Check src/myfile.py for mistakes.
```

**If you have a log file from a CI/CD pipeline:**
```
Run mistake-finder on artifacts/ci.log.
```

---

Bob will:
1. Activate the skill automatically
2. Spawn parallel mini-agents (you'll see them in the **Tasks panel**)
3. Show you a ranked report of all findings
4. In triage mode: apply one fix at a time, re-run the test, undo if it doesn't work

---

## 💻 Step 5 — Use it in your Terminal

You don't need IBM Bob to use this tool! You can also use it directly in any terminal.

### Run your code and see errors in a friendly box:

```bash
mistake-box python mycode.py
```

Instead of a raw Python traceback, you'll see a neat box like this:

```
╔══════════════════════════════════════════════════════════════╗
║ MISTAKE FOUND - SyntaxError                                  ║
╠══════════════════════════════════════════════════════════════╣
║ WHERE                                                        ║
║   mycode.py:12                                               ║
║ >>  12 |     if x = 5:                                       ║
║               ^                                              ║
╠══════════════════════════════════════════════════════════════╣
║ WHAT WENT WRONG                                              ║
║   SyntaxError: invalid syntax. Maybe you meant '==' or ':='? ║
╠══════════════════════════════════════════════════════════════╣
║ SUGGESTIONS                                                  ║
║   1. A single `=` assigns; use `==` to compare.              ║
╚══════════════════════════════════════════════════════════════╝
```

### Other ways to use it:

| What you want to do | Command |
|---------------------|---------|
| Run a Python file and catch errors | `mistake-box python mycode.py` |
| Check a file for syntax errors only | `mistake-box --file mycode.py` |
| Parse an existing log/error file | `mistake-box --log ci.log` |
| Run tests (errors shown in boxes automatically) | `pytest` |
| Run tests WITHOUT the boxes | `pytest --no-mistake-box` |

### On Windows — One-click launcher:

Just double-click **`find-mistakes.bat`** or run it in your terminal:

```
find-mistakes.bat
```

### Turn off the box globally (advanced):

```bash
set MISTAKE_BOX=0      # Windows
export MISTAKE_BOX=0   # Mac/Linux
```

---

## 🎙️ Step 6 — Use it with your Voice

You can speak to find mistakes! Say things like *"find the mistake in demo math"* and it will find and explain the error out loud.

```bash
voice.bat
```

Press **Enter** to start speaking, speak your command, press **Enter** again.

### Other voice commands:

| Command | What it does |
|---------|-------------|
| `voice.bat` | Start push-to-talk loop |
| `voice.bat --text "find the mistake in demo json"` | Type instead of speaking |
| `voice.bat --file mycode.py` | Analyse one file directly |
| `voice.bat --list-mics` | Show available microphones |

> 📖 For full setup instructions (microphone setup, credentials, troubleshooting), read [`VOICE.md`](VOICE.md).

---

## 🖼️ Example: What the output looks like

Here's a real example. Imagine your test file has this failing test:

```python
def test_add():
    assert add(2, 3) == 5   # but add() returns -1 by mistake
```

Running `pytest` will now show:

```
╔════════════════════════════════════════════════════════════════╗
║ MISTAKE FOUND - AssertionError                                 ║
╠════════════════════════════════════════════════════════════════╣
║ TEST                                                           ║
║   tests/test_calc.py::test_add                                 ║
╠════════════════════════════════════════════════════════════════╣
║ WHERE                                                          ║
║   tests/test_calc.py:5                                         ║
║      4 | def test_add():                                       ║
║ >>   5 |     assert add(2, 3) == 5                             ║
╠════════════════════════════════════════════════════════════════╣
║ WHAT WENT WRONG                                                ║
║   AssertionError: assert -1 == 5  (where -1 = add(2, 3))      ║
╠════════════════════════════════════════════════════════════════╣
║ SUGGESTIONS                                                    ║
║   1. Read the assertion: what value did the code actually      ║
║      produce, and what did the test expect?                    ║
║   2. The function returned -1 but 5 was expected. Check        ║
║      the logic inside add().                                   ║
╚════════════════════════════════════════════════════════════════╝
```

Much friendlier than a raw Python traceback!

---

## 🆘 Troubleshooting

### ❓ "python is not recognized as a command"
**Fix:** Python is not installed or not added to PATH.
- Reinstall Python from [python.org](https://python.org/downloads) and make sure to check **"Add Python to PATH"** during installation.
- Restart your terminal after installing.

---

### ❓ "pip is not recognized as a command"
**Fix:** Try using `pip3` instead of `pip`:
```bash
pip3 install .
```
Or try:
```bash
python -m pip install .
```

---

### ❓ "mistake-box is not recognized as a command"
**Fix:** Run `pip install .` again from inside the `Bug-Whisperer` folder. Make sure you see "Successfully installed" at the end.

---

### ❓ The skill doesn't appear in Bob's Settings → Skills
**Fix:**
1. Run `python install_skill.py` again
2. Restart IBM Bob completely (close and reopen)
3. Check that the file `.bob/skills/mistake-finder/SKILL.md` exists in your project folder

---

### ❓ "git is not recognized as a command"
**Fix:** Git is not installed.
- Download and install from [git-scm.com](https://git-scm.com/downloads)
- Restart your terminal after installing

---

### ❓ Tests are not showing the friendly box
**Fix:** Make sure you installed the tool first with `pip install .` in the `Bug-Whisperer` folder. Also check that you're using the same Python/pip that runs your tests.

---

## 🗂️ Project File Map

Here's what every file and folder in this project does:

```
Bug-Whisperer/
│
├── .bob/skills/mistake-finder/
│   ├── SKILL.md               ← The brain of the skill (instructions for Bob)
│   ├── review-checklist.md    ← List of mistake types to check for
│   ├── report-template.md     ← How reports are formatted
│   ├── box.py                 ← Core engine: parses errors and draws the box
│   ├── mistake_box.py         ← The `mistake-box` command you run in terminal
│   ├── pytest_plugin.py       ← Auto-shows boxes when pytest tests fail
│   └── __init__.py            ← Makes the folder work as a Python package
│
├── tests/                     ← 15 example test files (one per Python library)
├── demos/                     ← 14 demo files showing intentional bugs to find
├── bob_sessions/              ← Screenshots proving the skill works (hackathon submission)
│
├── find_mistakes.py           ← Smart runner — detects which file to analyse
├── find-mistakes.bat          ← One-click Windows launcher
├── smart_run.py               ← Auto-detects which library a demo needs
├── voice_agent.py             ← Voice mode engine
├── voice.bat                  ← One-click voice launcher (Windows)
├── menu.py                    ← Interactive menu to pick what to run
├── install_skill.py           ← Installs the skill into IBM Bob globally
├── pyproject.toml             ← Package config (used by pip install)
├── README.md                  ← This file!
├── VOICE.md                   ← Full voice setup guide
└── .env.example               ← Template for API keys (copy to .env and fill in)
```

---

## 🔒 Is it safe to use on my real code?

Yes! Safety guardrails are built in:

- 🔍 **Investigating agents are read-only** — they never change your files while looking for bugs
- ✅ **Tests are sacred** — it never weakens, skips, or deletes your tests
- 📍 **Every finding needs proof** — no `file:line` evidence = not reported
- 🔧 **One fix at a time** — applies one small fix, runs the test, rolls back if it fails
- 👀 **You approve changes** — in review mode, nothing is changed until you choose which findings to fix

---

## 🙏 Credits

Built for the **IBM Bob 2.0 Hackathon** on [lablab.ai](https://lablab.ai).
Powered by **IBM Bob** — the AI coding assistant.

---

*Happy coding — and may your bugs be few! 🐞*
