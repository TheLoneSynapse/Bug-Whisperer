# Review checklist — mistake classes

Each class below is handed to one review subagent in Mode 2. A subagent gets
only its own class section pasted into its brief. Keep the classes independent:
the same code is read by several subagents, each hunting for a different kind
of mistake. When adapting this skill to a team, add or remove classes here —
the SKILL.md workflow does not need to change.

---

## Class: logic-and-boundaries

Hunt for: off-by-one errors (`<` vs `<=`, `>` vs `>=`, wrong loop bounds), wrong
comparison direction, conditions that are always true/false, inverted boolean
logic, incorrect operator precedence, use-after-decrement, wrong variable used
in a condition (copy-paste bugs), boundary values not handled (empty list,
single element, zero, negative, max int, first/last index).

Hunting questions:
- For every `<`/`>`/`<=`/`>=`: which exact boundary value does the spec imply,
  and does the code agree?
- For every loop: what happens on the first iteration? The last? Zero
  iterations?
- What inputs make this branch take the unexpected path?

## Class: error-handling

Hunt for: exceptions swallowed silently (`except: pass`, empty catch), errors
caught too broadly (bare `except Exception` hiding real bugs), missing null/None
checks on values that can be absent, unhandled promise rejections, missing
error propagation (async functions whose failure is dropped), resource cleanup
missing on the error path (file handles, connections, locks not released when an
exception fires mid-operation), misleading error messages.

Hunting questions:
- What happens if every I/O call in this function fails right now?
- Which failure paths leave shared state corrupted or resources leaked?
- Is any error message lying about what actually went wrong?

## Class: concurrency-and-state

Hunt for: shared mutable state mutated from multiple paths without
synchronization, check-then-act races (test-then-set, exists-then-create),
non-atomic read-modify-write on caches/counters, unsafe lazy initialization,
stale reads after await/yield points, deadlock-prone lock ordering, thread/async
unsafe collection use.

Hunting questions:
- If two calls interleave at any await point or any line boundary, can the
  invariant break?
- Which mutable state escapes this module and who else can touch it?

## Class: resource-and-performance

Hunt for: unbounded growth (lists/dicts/maps only ever added to, no eviction),
files/sockets/statements opened without guaranteed close, N+1 query patterns
(query inside a loop), repeated recomputation of a pure value inside a loop,
accidental O(n²) on data that scales, loading entire datasets into memory when
streaming is available.

Hunting questions:
- What grows forever if this code runs 1000 times?
- What is opened here that is not closed on every path?

## Class: security-footguns

Hunt for: injection risks (string-built SQL/commands/paths, `eval`/`exec` on
input), secrets or tokens hardcoded or logged, unvalidated input reaching
file paths (path traversal) or URLs (SSRF), authentication/expiry checks
using inclusive instead of exclusive comparisons, missing authorization checks
on a per-object basis, insecure defaults (verify=False, weak hashing) reachable
from normal code paths.

Hunting questions:
- Where does externally influenced data first enter, and where does it exit
  unsanitized?
- Which comparison decides access or expiry, and is the boundary strict or
  inclusive?

## Class: test-gaps

Hunt for (in the tests, not the source): assertions missing entirely or
asserting on the wrong thing, tests that can never fail (no assertion, try/except
swallowing the assertion), boundary cases untested (zero, one, max, empty,
expired, exact threshold), error paths untested, tests coupled to
implementation details that will break on refactor, duplicated setup hiding
state leaks between tests.

Hunting questions:
- If the implementation silently inverted its condition, which test would catch
  it? If the answer is "none", that is a finding.
- Which untested path is the most likely to be broken by the next change?
