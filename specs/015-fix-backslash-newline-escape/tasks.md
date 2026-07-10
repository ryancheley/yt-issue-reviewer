# Tasks: Repair a backslash immediately before a newline in `yt` JSON

**Feature**: 015-fix-backslash-newline-escape | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #57). Constitution VII (Test-First): write the failing test before
the change. No setup/foundational work — `_escape_stray_backslashes` and its test file exist.

## Phase 1: User Story 1 — Analyze issues whose text has a backslash at a line end (P1)

**Goal**: `analyze` parses `yt` JSON where a description ends a line with a literal backslash
before a raw newline, instead of crashing with `Invalid \escape`.

**Independent test**: `uv run pytest tests/unit/test_load_json_issues.py` — the new test fails
before the change, passes after.

### Tests first (write, watch fail)

- [X] T001 [US1] In `tests/unit/test_load_json_issues.py`, add a test that `_load_json_issues` parses a payload with a backslash **immediately before a raw newline** inside a `description` (e.g. `'[{"idReadable": "NG-1", "description": "ends with backslash\\\n next line"}]'`) and returns the issue list instead of raising.

### Implementation

- [X] T002 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py`, add `flags=re.DOTALL` to the `re.sub(...)` in `_escape_stray_backslashes` so the `\\(.)` branch also matches a backslash before a newline. Update the docstring to note the newline case (issue #57).

## Phase 2: Polish & verification

- [X] T003 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions — including the existing #48 / valid-escape / control-char / non-JSON tests (SC-002/003/004).

## Dependencies

- T001 (test) before T002 (fix) — Test-First.
- T003 after implementation.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T003 fully resolves issue #57.
