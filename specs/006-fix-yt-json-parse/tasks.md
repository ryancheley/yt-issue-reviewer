# Tasks: Graceful handling of non-JSON `yt` output

**Feature**: 006-fix-yt-json-parse | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Gate**: `just check` (ruff, ruff format, ty, pytest, zizmor) must pass before push.

**Scope note**: One production function is hardened (`_load_json_issues` in
`src/yt_issue_reviewer/ingest/youtrack.py`). Tests are written first (constitution Principle
VII, Test-First). Both user stories touch the same function and the same test file, so their
tasks are sequential, not parallel.

## Phase 1: Setup

No setup tasks — existing project, existing test suite, no new dependencies.

## Phase 2: Foundational

No foundational/blocking tasks — the change is isolated to one existing function.

## Phase 3: User Story 1 — BOM-prefixed JSON parses successfully (P1)

**Goal**: A UTF-8 BOM at the start of valid `yt` JSON no longer crashes; issues parse normally.

**Independent test**: Call `youtrack._load_json_issues()` with a valid issue-list payload
prefixed with a BOM and assert it returns the same list as the un-prefixed payload.

- [X] T001 [US1] Add failing unit test `test_bom_prefixed_json_parses` in `tests/unit/test_load_json_issues.py`: assert `_load_json_issues("﻿" + '[{"idReadable":"X-1"}]')` returns the same list as without the BOM, and `test_bom_then_whitespace_is_empty` asserting `"﻿  "` returns `[]`.
- [X] T002 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py`, `_load_json_issues`: strip a leading UTF-8 BOM (`stdout.removeprefix("﻿")`) before the existing empty check so BOM-then-empty still returns `[]`.

## Phase 4: User Story 2 — Non-JSON output gives a clear error (P1)

**Goal**: Non-JSON stdout raises the operator-facing `YouTrackUnavailable` with a truncated
excerpt instead of a raw `JSONDecodeError` traceback.

**Independent test**: Call `_load_json_issues()` with a non-JSON string and assert it raises
`YouTrackUnavailable` (not `JSONDecodeError`) with an excerpt of the input in the message.

- [X] T003 [US2] Add failing unit tests in `tests/unit/test_load_json_issues.py`: `test_non_json_raises_youtrack_unavailable` (a banner string raises `YouTrackUnavailable`, message contains an excerpt of the input) and `test_long_non_json_excerpt_truncated` (a very long non-JSON input yields a message shorter than the input). Also `test_empty_and_whitespace_still_return_empty` to lock existing behavior.
- [X] T004 [US2] In `_load_json_issues`, wrap `json.loads` in `try/except json.JSONDecodeError` and re-raise `YouTrackUnavailable(f"'yt' did not return JSON. Got: {excerpt}")` using `from exc`, where `excerpt` is the first ~200 chars of the stripped output. Preserve the dict-unwrap and non-list handling unchanged.

## Phase 5: Polish & Verification

- [X] T005 Run `just check` and confirm ruff, ruff format, ty, pytest (incl. the new tests), and zizmor all pass with no analysis-behavior change.

## Dependencies

- T001 → T002 (test-first for US1).
- T003 → T004 (test-first for US2).
- T002 and T004 edit the same function; do US1 then US2 sequentially.
- T005 last, after all edits.

## Parallel Opportunities

None — single function, single test file. All tasks are sequential.

## Implementation Strategy

- **MVP = User Story 1** (T001–T002): recovers the exact issue #29 crash (BOM). Shippable alone.
- **Full fix** adds User Story 2 (T003–T004): comprehensible failure for any other non-JSON
  output. Both are P1 and small; ship together.
