# Tasks: Respect `Status` custom-field state when filtering open issues

**Feature**: 007-fix-status-state-filter | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #35). Constitution VII (Test-First) applies: write the failing
regression tests before the fix. No setup or foundational work needed — the module,
helper (`_matches_state`), and test harness already exist.

## Phase 1: User Story 1 — Exclude resolved issues in Status-based projects (P1)

**Goal**: `--state open` must not return issues whose state lives in a `Status` custom
field set to a closed marker (`Done`, etc.).

**Independent test**: `uv run pytest tests/unit/test_ingest_filters.py tests/unit/test_youtrack_source.py`
— both new tests fail before the fix, pass after.

### Tests first (write, watch fail)

- [X] T001 [P] [US1] Add a regression test in `tests/unit/test_ingest_filters.py` asserting `parse_issue` reads state from a `Status` custom field (value `Done`) into `Issue.state`, and that a built-in `State` field still wins when both are present.
- [X] T002 [US1] Add a regression test in `tests/unit/test_youtrack_source.py` where `CliYouTrackSource` (stub `subprocess.run` + `shutil.which`) returns issues whose `Status` custom field is `Done`; assert `fetch_issues([...], state="open")` excludes the `Done` issues and `state="all"` returns them all.

### Implementation

- [X] T003 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py` `parse_issue`, add `"Status"` (after `"Stage"`) to the `_extract_custom_field(custom_fields, "State", "Stage", "Status")` call so `Status`-based projects populate `Issue.state`.
- [X] T004 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py` `CliYouTrackSource.fetch_issues`, apply `_matches_state(i.state, state)` to the parsed issues before the date-range filter, so the client-side state filter runs on the production path regardless of what `yt --state Open` returned.

## Phase 2: Polish & verification

- [X] T005 Run `just check` (ruff + ty + full pytest) and confirm the CI gate is green with no regressions (SC-003).

## Dependencies

- T001, T002 (tests) before T003, T004 (fix) — Test-First.
- T001 ∥ T002 are parallelizable (different files).
- T003 and T004 are in the same file; do T003 then T004 (no [P]).
- T005 after all.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T005 fully resolves issue #35.
