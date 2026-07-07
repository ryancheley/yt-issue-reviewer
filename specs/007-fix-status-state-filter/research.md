# Research: Respect `Status` custom-field state

No open unknowns — the bug and fix are fully characterized by issue #35's investigation.
Recorded decisions:

## Decision: Recognize `Status` as a state-bearing custom field

- **Decision**: Add `"Status"` to the `_extract_custom_field(custom_fields, "State", "Stage", ...)`
  call in `parse_issue`, appended after the existing names.
- **Rationale**: Some YouTrack projects (e.g. NGDEV) model workflow state entirely in a
  custom field literally named `Status`; the built-in `State` field is `None` for every
  issue. Empirically confirmed in issue #35: all 21 issues had `State = None` and a
  `Status` of `Done`/`In Progress`/`Waiting`.
- **Order matters**: `Status` is appended last so `State`/`Stage` win when present,
  preserving existing behavior (FR-005, edge case: both fields present).
- **Alternatives considered**: A per-project config to name the state field — rejected as
  speculative (YAGNI); the field name is a stable YouTrack convention and the fixed list
  already covers the observed variants.

## Decision: Apply `_matches_state` on the production read path

- **Decision**: In `CliYouTrackSource.fetch_issues`, filter the parsed issues with the
  existing `_matches_state(issue.state, state)` after parsing, before the date-range filter.
- **Rationale**: The server-side `yt --state Open` is a no-op for `Status`-based projects
  (the built-in `State` it filters on is empty), so `Done` issues come back anyway. The
  helper already exists and is already exercised by `FakeYouTrackSource`; production simply
  never called it. Applying it makes the two sources consistent (FR-003) and is idempotent
  when the server-side filter already worked (edge case).
- **Alternatives considered**:
  - Fix only the parser (B) without the client-side filter (C) — rejected: the server-side
    `--state Open` still won't drop `Status=Done` issues, so the leak persists.
  - Drop the server-side `--state Open` entirely and rely only on the client filter —
    rejected: keep the server-side hint (cheaper payload for `State`-based projects); the
    client filter is a safety net, not a replacement.

## Confirmed out of scope

- Issue #34 (JSONDecodeError on multi-line descriptions) is already fixed by the shipped
  #29 work (`strict=False` in `_load_json_issues`) and covered by
  `test_control_chars_in_strings_are_tolerated`. Verified: a raw-newline description parses.
  No change in this feature.
