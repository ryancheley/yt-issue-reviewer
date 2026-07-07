# Tasks: Fetch every issue in a project, not just the first page

**Feature**: 010-fetch-all-issues | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #42). Constitution VII (Test-First): write the failing
regression test before the fix. No setup/foundational work — module and the
subprocess-stub harness (captures the issued `yt` command) already exist.

## Phase 1: User Story 1 — Analyze a project with more than 100 issues (P1)

**Goal**: `analyze` must ingest every issue in a project, not just the first page of 100.

**Independent test**: `uv run pytest tests/unit/test_youtrack_subprocess.py`
— the new test fails before the fix, passes after.

### Tests first (write, watch fail)

- [X] T001 [US1] Add a regression test in `tests/unit/test_youtrack_subprocess.py` that stubs `subprocess.run`, calls `CliYouTrackSource().fetch_issues(["PROJ"])`, captures the issued `yt issues list` command, and asserts it contains `--all` (so `yt` paginates the full result set).

### Implementation

- [X] T002 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py` `CliYouTrackSource._fetch_project`, add `--all` to the `yt issues list` command so `yt` pages through every issue (its `--page-size` defaults to 100). Add a short comment noting the default-100 cap this avoids.

## Phase 2: Polish & verification

- [X] T003 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-003).
- [X] T004 Manual live check (optional, operator): against a >100-issue project, confirm `analyze --state all` now ingests the full count (matches `yt ... --all | jq length`), not 100 (SC-001).

## Dependencies

- T001 (test) before T002 (fix) — Test-First.
- T002 is the only impl task; sequential.
- T003/T004 after T002.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T003 fully resolves issue #42.
