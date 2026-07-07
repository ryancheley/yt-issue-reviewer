# Tasks: `--state open` must return all genuinely-open issues

**Feature**: 009-fix-open-state-filter | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #39). Constitution VII (Test-First) applies: write the failing
regression test before the fix. No setup/foundational work — module, helper
(`_matches_state`), and the subprocess-stub test harness already exist.

## Phase 1: User Story 1 — Analyze open issues in a `New`-state project (P1)

**Goal**: `--state open` must return genuinely-open issues even when `yt`'s server-side
`--state Open` would return nothing for them.

**Independent test**: `uv run pytest tests/unit/test_youtrack_subprocess.py`
— the new test fails before the fix, passes after.

### Tests first (write, watch fail)

- [X] T001 [US1] Add a regression test in `tests/unit/test_youtrack_subprocess.py` where a stubbed `subprocess.run` returns a `State=New` issue only when the command has **no** `--state` argument (and `[]` when `--state Open` is present, mimicking live `yt`); assert `CliYouTrackSource().fetch_issues(["THD"], state="open")` includes the `New` issue, and assert the issued command for the `open` case omits `--state Open`.

### Implementation

- [X] T002 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py` `CliYouTrackSource._fetch_project`, remove the `if state == "open": cmd += ["--state", "Open"]` branch so `yt issues list` returns all issues; the client-side `_matches_state` filter in `fetch_issues` (from #35) does the open/closed selection.

## Phase 2: Polish & verification

- [X] T003 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-004).
- [X] T004 Manual live check (optional): `analyze --project THD --state open` now reports 2 issues (SC-002); `--state all` still reports 2.

## Dependencies

- T001 (test) before T002 (fix) — Test-First.
- T002 in the same file as no other impl task; sequential.
- T003/T004 after T002.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T003 fully resolves issue #39.
