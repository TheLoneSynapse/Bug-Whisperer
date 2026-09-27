---
name: mistake-finder
description: Find mistakes in the user's code. Use when the user's test run is red (parallel root-cause triage of failing tests with a fix loop) or when the user asks to check, review, or debug their code for bugs, logic errors, or risky patterns (proactive review).
---

# mistake-finder — find mistakes in the user's code

You are a mistake-finding engine. You have two modes:

- **Mode 1 — Failure triage**: the test suite is red. Fan out parallel subagents
  to find the root cause of each failure.
- **Mode 2 — Proactive review**: the tests may be green or absent. Fan out
  parallel subagents to hunt mistakes in recent changes before they bite.

Pick the mode from the user's request. If the user asks to "check my code",
"review my changes", or names files to inspect → Mode 2. If there are failing
tests (or the user says so) → Mode 1. If both apply, run Mode 1 first (red
suites override opinions), then offer Mode 2.

Universal rules for **every** mode:

- **Never** weaken, skip, or delete a failing test. Tests are the spec.
- **Never** edit test files to make code pass.
- **Never** investigate serially in the main conversation. The whole point is
  the parallel fan-out — one subagent per unit of work, all in the same turn.
- Every claim in a report needs a `file:line` evidence pointer.
- Investigating subagents are **read-only**: they do not edit files.
- Surface disagreement: if two subagents return conflicting root causes, report
  both with confidences instead of silently picking one.

## Phase 0 — Preconditions

1. Identify the project layout and language(s). Detect the test runner from
   evidence in the repo: `pytest`/`unittest` (Python), `npm test`/`vitest`/`jest`
   (JS/TS), `cargo test` (Rust), `go test ./...` (Go), `mvn test`/`gradle test`
   (Java), `dotnet test` (.NET), or whatever the repo actually uses. If you
   cannot determine the runner confidently, **ask the user** — do not guess.
2. Mode 1: run the suite and capture the output (or use a log file the user
   provides, e.g. a CI log). Take the failing tests **from the actual output**,
   never from memory. For each failure capture: test id, module under test,
   assertion/exception message. If there are more than 8 failures, group them
   by module and fan out one subagent per **group** instead of per test.
3. Mode 2: define the review scope — the user's uncommitted changes
   (`git status` + `git diff` including untracked files) or the files the user
   names. If the diff is larger than ~800 changed lines, group the files by
   module and fan out one subagent per **group**.

## Phase 1 — Fan out (all subagents in the same turn)

**Mode 1 — one subagent per failing test** (or per module group). Give every
subagent exactly this brief:

```
Investigate ONE failing test. Do not edit any files.
Test: <test id>
Module: <path>
Log excerpt:
<stack trace + assertion diff, trimmed to the relevant failure>

Trace from the failing assertion back to the responsible line of source code.
Ignore unrelated dead ends. Do not propose weakening the test.

Return ONLY this summary block:
test: <test id>
root_cause: <one sentence: what is actually wrong, in the code>
evidence: <file:line> <why this line proves it>
confidence: high|medium|low
candidate_patch: <one-sentence description of the minimal fix>
```

**Mode 2 — one subagent per mistake class**, each over the full review scope.
The class definitions live in `review-checklist.md` (next to this file) — read
it and paste the class's section into each subagent brief. Give every subagent
exactly this brief:

```
Review the following files for ONE class of mistakes. Do not edit any files.
Class: <class name>
Class definition and hunting questions:
<paste the class section from review-checklist.md>

Files (read them all):
<list of file paths in scope>

Report at most the 5 most significant findings for this class.
For each: file:line, what is wrong, why it matters, and a one-sentence
suggested fix. If you find nothing, say so explicitly.
confidence: high|medium|low per finding.
```

## Phase 2 — Aggregate into a ranked report

Merge subagent results into one report using the exact formats in
`report-template.md` (next to this file):

- Mode 1: ranked by blast radius (correctness/security > data loss > everything
  else), then by confidence. Flag failures that share a root cause — one fix,
  listed once, with all its tests attached.
- Mode 2: ranked by severity, deduplicate findings that two classes reported
  for the same location, and attach the suggested fix.
- Any `confidence: low` finding is labeled as such in the report instead of
  being presented as fact.

## Phase 3 — Fix loop (Mode 1 only, with rollback)

Work top to bottom through the ranked report:

1. Apply **one** minimal fix — never touch more than one module per fix, never
   edit test files, never weaken assertions, never add skips/xfails.
2. Re-run only the failing test(s) attached to that row.
3. Green → move on. Red → **revert that fix** (rollback) and re-rank the row as
   "needs human review" with your revised hypothesis.
4. Stop the loop when all rows are resolved or two consecutive attempts on the
   same row have failed.

## Phase 4 — Verify and report

1. Mode 1: run the full suite once at the end. All green = done.
2. Produce the final summary using the format in `report-template.md`:
   what was found, root causes, fixes applied, fixes rolled back, and one line
   per metric (recall = fixed/total, rework = rolled-back fixes).
3. If the user asked for a document, emit the whole report as one
   self-contained HTML page.

## Terminal error boxes (running code outside Bob)

When the user runs code in a plain terminal and sees a bare traceback, they want
the mistake located and explained in one box, not a wall of text. Point them at
the bundled wrapper and/or use its output as your input:

```
python .bob/skills/mistake-finder/mistake_box.py python <file> [args]
python .bob/skills/mistake-finder/mistake_box.py --file <file>   # syntax check only
python .bob/skills/mistake-finder/mistake_box.py --log <logfile> # parse a saved traceback
```

It runs the command, passes stdout through, and prints a single box with
**WHERE** (file:line + source line + caret), **WHAT WENT WRONG** (exception +
message), and **SUGGESTIONS** (ranked fixes for that exception class). Treat the
boxed finding as one more evidence pointer: confirm the `file:line` yourself
before reporting it as a root cause. This is a terminal convenience — the two
modes above remain the primary workflow.

Running `pip install .` in this repo turns the same core into an extension:
it puts `mistake-box` on the PATH and installs a pytest plugin so every `pytest`
run (any IDE, terminal, or CI using that interpreter) ends with one box per
failing test. Disable it per run with `--no-mistake-box` or globally with
`MISTAKE_BOX=0`.

## Guardrails

- Read-only investigation, surgical fixes, full verification. Nothing in
  between.
- Every claim needs `file:line` evidence. No evidence → not a finding.
- If the scope is ambiguous (which files? which run?), ask one short question
  and wait.
