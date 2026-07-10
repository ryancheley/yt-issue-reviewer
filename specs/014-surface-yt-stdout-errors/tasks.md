# Tasks: Surface `yt`'s stdout in failure messages

**Feature**: 014-surface-yt-stdout-errors | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #54). Constitution VII (Test-First): write the failing tests before
the change. No setup/foundational work — the module and its subprocess-stub test harness exist.

## Phase 1: User Story 1 — See the real reason a `yt` call failed (P1)

**Goal**: a `yt` failure whose reason is on stdout (e.g. `❌ Not authenticated`) surfaces that
reason in the `YouTrackUnavailable` message.

**Independent test**: `uv run pytest tests/unit/test_youtrack_subprocess.py` — the new tests fail
before the change, pass after.

### Tests first (write, watch fail)

- [X] T001 [US1] In `tests/unit/test_youtrack_subprocess.py`, add a test that stubs `subprocess.run` so `yt issues list` returns `returncode=1` with the reason on **stdout** (e.g. `"❌ Not authenticated"`) and empty stderr; assert `fetch_issues(["NGDEV"])` raises `YouTrackUnavailable` whose message **contains the stdout reason**.
- [X] T002 [US1] Add a test that when the failing `yt` call has the reason only on **stderr** (empty stdout), the raised `YouTrackUnavailable` message still contains the stderr text (no regression).
- [X] T003 [US1] Add a test for the `check_available()` path: stub `yt auth token --show` to return `returncode=1` with a reason on stdout; assert `check_available()` raises `YouTrackUnavailable` containing both the existing "Run `yt auth login`" guidance and the stdout reason.

### Implementation

- [X] T004 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py`, add a small module helper `_proc_output(proc)` that returns the non-empty of `proc.stdout.strip()` and `proc.stderr.strip()` joined by a newline (drops empties).
- [X] T005 [US1] Use `_proc_output(proc)` in both non-zero-returncode branches: `check_available()` (append it after the "youtrack-cli is not authenticated. Run `yt auth login`." guidance instead of `proc.stderr.strip()`) and `_fetch_page()` (replace `proc.stderr.strip()` in the `'yt issues list' failed ...` message). Success path unchanged.

## Phase 2: Polish & verification

- [X] T006 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-003).

## Dependencies

- T001–T003 (tests) before T004–T005 (impl) — Test-First.
- T004 before T005 (T005 calls the helper).
- T006 after implementation.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T006 fully resolves issue #54.
