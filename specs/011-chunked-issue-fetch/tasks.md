# Tasks: Fetch issues in bounded chunks so slow/gated networks work

**Feature**: 011-chunked-issue-fetch | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #45). Constitution VII (Test-First): write the failing tests
before the implementation. No setup/foundational work — module and the subprocess-stub test
harness already exist.

## Phase 1: User Story 1 — Analyze from behind a slow/gated network (P1)

**Goal**: retrieve every issue in a project via bounded requests, so no single request exceeds
a ~20s per-request gateway limit.

**Independent test**: `uv run pytest tests/unit/test_youtrack_subprocess.py` — the new tests
fail before the fix, pass after.

### Tests first (write, watch fail)

- [X] T001 [US1] In `tests/unit/test_youtrack_subprocess.py`, add a fixture that stubs `subprocess.run` to serve **synthetic ascending-`created` pages** keyed off the `--top` value and the `created: <cursor> ..` clause in the issued `--query` (auth call returns a token). Cover a project of ~3 pages with distinct `created` dates.
- [X] T002 [US1] Add a test asserting `CliYouTrackSource().fetch_issues(["PROJ"], state="all")` returns **all** synthetic issues (multi-page assembly, count = total) and that **each `yt issues list` request used `--top` ≤ PAGE** (no unbounded/`--all` request).
- [X] T003 [US1] Add a test that the **boundary overlap is de-duplicated** — synthetic pages that re-include the last issue of the prior page (because the cursor is date−1day) yield each issue exactly once.
- [X] T004 [US1] Add a test that a **same-date stall** (a full page of PAGE issues all sharing one `created` date, no new ids) raises `YouTrackUnavailable` with actionable text, instead of looping.
- [X] T005 [US1] Add a test that a project **fitting in one page** (first page shorter than PAGE) is returned in a single request (behavior unchanged) and that the issued command contains no `--all`.

### Implementation

- [X] T006 [US1] In `src/yt_issue_reviewer/ingest/youtrack.py`, replace the single `--all` request in `CliYouTrackSource._fetch_project` with the creation-date cursor loop: extract a `_run_issue_page(query)` helper that runs one bounded `yt issues list --format json --top PAGE --query <query>` (reusing the existing UTF-8 env, timeout, returncode + `_load_json_issues` handling), then loop building `project: <P> [created: <cursor> ..] sort by: created asc`, dedup by `issue_id`, advance the cursor to the newest page `created` minus one day, stop on a short page. Add a module constant `_PAGE_SIZE = 200` with a comment naming the ~20s ceiling. Remove `--all`.
- [X] T007 [US1] Add a small helper (e.g. `_cursor_floor(iso_ts)`) that converts an issue's ISO `created` to a `YYYY-MM-DD` **minus one day** lower bound, and raise `YouTrackUnavailable` (guidance: narrow via `--since/--until` or use a faster network) when a full page yields no new ids.

## Phase 2: Polish & verification

- [X] T008 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-005).
- [X] T009 Manual check (local, fast network): `analyze --project NGDEV --state all` still ingests the full local count (e.g. 178) in as many bounded pages as needed (SC-003). Operator to confirm on the gated instance later (SC-001).

## Dependencies

- T001 before T002–T005 (fixture underpins them). T001–T005 (tests) before T006–T007 (impl) — Test-First.
- T006 and T007 touch the same file/function; sequential.
- T008/T009 after implementation.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T008 fully resolves issue #45.
