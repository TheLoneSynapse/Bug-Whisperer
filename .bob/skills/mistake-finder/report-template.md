# Report templates

Exact formats for the two modes. Use them verbatim so reports stay comparable
across runs.

---

## Mode 1 — Failure triage report

Title: `## Failure triage report — <date> <suite name>`

Ranked table, then per-row detail:

```
| # | Test | Root cause | Evidence | Confidence | Patch |
|---|------|-----------|----------|------------|-------|
| 1 | ...  | ...       | file:line| high       | ...   |
```

Ranking: correctness/security > data loss > everything else; ties broken by
confidence.

Per row:

```
### #N <test id>
root_cause: <one sentence, what is actually wrong>
evidence: <file:line> — <why this proves it>
confidence: high|medium|low
patch: <the minimal fix applied>
result: green | rolled back (needs human review)
```

Shared root cause: list the fix **once** with all its tests attached:

```
### #N <root cause> — affects: <test A>, <test B>
```

Final summary block (required, exact keys):

```
tests_failing_at_start: <n>
rows_fixed: <n>
rows_rolled_back: <n>
recall: <fixed>/<total>
rework: <rolled-back fixes>
full_suite: green | red (<n> still failing — needs human review)
elapsed: <wall clock>
```

---

## Mode 2 — Mistake review report

Title: `## Mistake review — <date> — scope: <files or "uncommitted changes">`

Ranked findings table:

```
| # | Severity | Class | Finding | Evidence | Confidence | Suggested fix |
|---|----------|-------|---------|----------|------------|---------------|
```

Severity definitions:
- **Critical** — data loss, security hole, or an invariant that breaks under
  normal use.
- **High** — wrong behavior on realistic input; error path leaves state
  corrupted.
- **Medium** — works today, breaks under foreseeable change or load.
- **Low** — style/robustness; flagged for completeness.

Rules:
- Deduplicate: if two classes flagged the same location, merge into one row and
  keep the higher severity, noting both classes.
- `confidence: low` findings are included but must say so in the Confidence
  column.
- Cap the headline list at 10 findings; lower-severity extras go under a
  "Minor notes" section.
- End with one line: `<n> findings — <n> critical/high, <n> medium, <n> low`.
  If nothing was found, say `No mistakes found in the reviewed scope.` — that
  is a valid result.

After the report: ask the user which findings to fix. Do not edit any file
before the user picks.
