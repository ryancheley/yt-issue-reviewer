# Research: Fetch every issue in a project

No open unknowns — root cause and fix confirmed against the `yt` CLI's own help and a local run.

## Decision: Pass `--all` to `yt issues list`

- **Decision**: Add `--all` to the command built in `CliYouTrackSource._fetch_project`.
- **Rationale**: `yt issues list --help` shows `--page-size` defaults to **100** and `--all`
  "Fetch all results using pagination". Without a pagination flag, `yt` returns only the first
  page, so projects with >100 issues silently lose the remainder — the reported symptom on a
  large Jira-imported project. `--all` delegates full pagination to `yt` (the sole read seam,
  Constitution III) instead of hand-rolling a page loop in this tool.
- **Verified**: `yt issues list --project-id THD --format json --all` returns correctly (THD:
  2 issues, exit 0) — the flag is accepted and non-breaking for small projects.
- **Alternatives considered**:
  - `--page-size <big-number>` — rejected: a fixed large page still caps silently at that
    number; `--all` is the intended "everything" mode.
  - `--max-results <big-number>` — rejected: same capping concern; still an arbitrary ceiling.
  - Hand-rolled page loop (`--start-page` + `--page-size`) — rejected: reimplements what
    `yt --all` already does; more code, more failure modes (VI. Simplicity).

## Confirmed behavior to preserve

- Client-side state filtering (#35/#39) and date-range filtering already run over the full
  per-project set in `fetch_issues`, so they compose with the larger fetch unchanged.
- JSON parsing (`_load_json_issues`), project scoping, and error handling are untouched.
- The existing 300s subprocess timeout still bounds the (now potentially longer) fetch.
