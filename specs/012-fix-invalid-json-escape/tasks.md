# Tasks: Tolerate invalid backslash escapes in `yt` JSON output

**Feature**: 012-fix-invalid-json-escape | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #48). Constitution VII (Test-First): write the failing tests
before the fix. No setup/foundational work — `_load_json_issues` and its test file already exist.

## Phase 1: User Story 1 — Analyze issues whose text contains backslashes (P1)

**Goal**: `analyze` completes over issues whose text contains unescaped backslashes (Windows
paths, regexes), instead of crashing.

**Independent test**: `uv run pytest tests/unit/test_load_json_issues.py` — the new tests fail
before the fix, pass after.

### Tests first (write, watch fail)

- [X] T001 [P] [US1] In `tests/unit/test_load_json_issues.py`, add a test that `_load_json_issues` parses a payload with an **unescaped backslash inside a `description`** (e.g. `[{"idReadable":"NG-1","description":"path C:\\Users and regex \\d+"}]` written with real single backslashes) and returns the issue list instead of raising.
- [X] T002 [P] [US1] Add a test that a payload using **valid escapes** (`\n`, `\t`, `\"`, `\\`, `\/`, `\uXXXX`) parses to the **same** values through `_load_json_issues` as plain `json.loads` — the repair must not corrupt valid escapes.
- [X] T003 [P] [US1] Add/confirm a test that a genuinely **non-JSON banner** still raises `YouTrackUnavailable` (the repair must not mask real "yt didn't return JSON" errors).

### Implementation

- [X] T004 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py`, add a module helper `_escape_stray_backslashes(text)` — `re.sub(r'\\(["\\/bfnrtu])|\\(.)', lambda m: m.group(0) if m.group(1) else "\\\\" + m.group(2), text)` — that doubles any backslash not part of a valid JSON escape while preserving valid escapes. Add `import re` at the top if not present.
- [X] T005 [US1] In `_load_json_issues`, wrap the `json.loads(stdout, strict=False)` call: on `JSONDecodeError`, retry once with `json.loads(_escape_stray_backslashes(stdout), strict=False)`; only if that retry also raises `JSONDecodeError`, re-raise the existing operator-facing `YouTrackUnavailable` (truncated excerpt) as today. Add a comment referencing issue #48.

## Phase 2: Polish & verification

- [X] T006 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-004).

## Dependencies

- T001–T003 (tests) before T004–T005 (impl) — Test-First. T001/T002/T003 are independent [P].
- T004 before T005 (T005 calls the helper).
- T006 after implementation.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T006 fully resolves issue #48.
