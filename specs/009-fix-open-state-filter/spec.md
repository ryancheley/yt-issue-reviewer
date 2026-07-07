# Feature Specification: `--state open` must return all genuinely-open issues

**Feature Branch**: `009-fix-open-state-filter`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: Fix issue #39 — `analyze --state open` drops legitimately-open
issues because the server-side `yt --state Open` filter is unreliable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze open issues in a project whose issues are `New` (Priority: P1)

An operator runs `analyze --state open` against a project whose issues are genuinely open
(for example, all in state `New`). They expect every open issue to be analyzed.

**Why this priority**: This is the whole bug. Today the operator gets *zero* issues even
though open issues exist, so `--state open` is silently useless for these projects — the
opposite failure from #35 (which leaked resolved issues in). Both stem from trusting the
unreliable server-side `--state Open`.

**Independent Test**: Point the ingest layer at a source that only returns issues when no
server-side state argument is applied (mimicking the observed `yt --state Open` → empty
behavior) and request `state=open`; confirm the `New` issues are returned.

**Acceptance Scenarios**:

1. **Given** a project with 2 issues both in state `New`, **When** the operator requests
   `--state open`, **Then** both issues are returned.
2. **Given** the same project, **When** the operator requests `--state all`, **Then** both
   issues are returned (unchanged).
3. **Given** a project mixing `New`/`In Progress` and `Done`/`Closed` issues, **When** the
   operator requests `--state open`, **Then** only the non-resolved issues are returned and
   the resolved ones are excluded (the #35 behavior is preserved).

### Edge Cases

- An issue has an empty/unknown state → treated as open (not resolved), matching existing
  `_matches_state` behavior.
- A project genuinely has zero open issues → `--state open` returns zero (correctly empty,
  not a false empty caused by the server-side filter).
- Resolved issues (`Done`/`Closed`/`Resolved`/`Fixed`/`Verified`) → excluded under
  `--state open`, whether their state comes from the built-in `State` field or a `Status`
  custom field (from #35).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `--state open` MUST return every issue whose workflow state is not a resolved
  marker, regardless of how the upstream issue source responds to a server-side state hint.
- **FR-002**: The system MUST NOT rely on the upstream `yt` server-side `--state Open`
  filter to determine which issues are open; open/closed determination MUST be made from the
  issue's own state after fetching.
- **FR-003**: `--state all` MUST continue to return every issue (unchanged).
- **FR-004**: Resolved issues MUST remain excluded under `--state open` (no regression of the
  #35 fix), for both built-in `State` and `Status`-custom-field projects.
- **FR-005**: The change MUST NOT alter the `yt` command used for `--state all`, nor any
  non-state behavior (project scoping, date-range filtering, JSON parsing).

### Key Entities

- **Issue workflow state**: Open vs. resolved, derived from the issue's `State`/`Stage`/`Status`
  field; the sole authority for open/closed filtering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a project whose issues are all `New`, `--state open` returns 100% of those
  issues (currently returns 0%).
- **SC-002**: For the live repro project (THD, 2 `New` issues), `--state open` returns 2.
- **SC-003**: For a mixed project, the count returned by `--state open` equals the number of
  non-resolved issues (resolved excluded).
- **SC-004**: No regression — the full existing test suite continues to pass.

## Assumptions

- The client-side `_matches_state` filter added in #35 already runs unconditionally in
  `fetch_issues`, so removing the server-side hint leaves correct filtering in place.
- Fetching all issues per project (instead of a server-narrowed subset) is acceptable for
  the tool's scale; the tool already fetches and filters client-side for date ranges.
- The set of resolved-state markers (`closed`/`resolved`/`done`/`fixed`/`verified`) is
  unchanged.
