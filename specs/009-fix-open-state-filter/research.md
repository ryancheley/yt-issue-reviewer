# Research: `--state open` must return all genuinely-open issues

No open unknowns — the bug was reproduced against a live, authenticated YouTrack.

## Decision: Drop the server-side `--state Open` hint; rely on the client-side filter

- **Decision**: Remove the `if state == "open": cmd += ["--state", "Open"]` branch from
  `CliYouTrackSource._fetch_project`. `yt issues list` then returns all issues for the
  project, and the existing `_matches_state(i.state, state)` filter in `fetch_issues`
  (added by #35) decides open vs. resolved.
- **Rationale**: The server-side `yt --state Open` is empirically unreliable in *both*
  directions:
  - #35: it let resolved (`Done`) issues leak through for `Status`-custom-field projects.
  - #39 (this): it returned zero for project THD whose two issues are both `State=New`
    (genuinely open) — dropping open issues entirely.
  Confirmed live: `yt issues list --project-id THD --state Open` → `[]`, while
  `yt issues list --project-id THD` → the 2 `New` issues. Since the client-side filter is
  already the source of truth (it runs unconditionally post-#35), the server-side hint adds
  nothing and can only subtract correct results. The lazy, correct fix is deletion.
- **Alternatives considered**:
  - Keep `--state Open` and add issues the server dropped — impossible; issues the server
    omits never reach the client to be recovered.
  - Translate `open` into an explicit `State: {New, In Progress, ...}` yt query — rejected:
    couples the tool to each project's state vocabulary (the exact fragility #35 exposed);
    the client-side marker set already handles this generically.
  - Keep `--state Open` only for `State`-based projects — rejected: THD *is* a `State`-based
    project (`State=New`) and still broke; there is no reliable predicate for "when the
    server-side filter works."

## Confirmed behavior to preserve

- `--state all` already passes no `--state` argument, so it is unaffected.
- Date-range filtering, project scoping, and JSON parsing are untouched.
- Resolved-issue exclusion (#35) still holds because `_matches_state` is unchanged.
