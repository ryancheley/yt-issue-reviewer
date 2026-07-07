# Feature Specification: Respect `Status` custom-field state when filtering open issues

**Feature Branch**: `007-fix-status-state-filter`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: Fix issue #35 — `analyze --state open` leaks resolved (Done) issues for YouTrack projects that model workflow state in a custom field named `Status` instead of the built-in `State` field.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Exclude resolved issues in Status-based projects (Priority: P1)

An operator runs `analyze --state open` against a YouTrack project whose workflow
state lives in a custom field named `Status` (values like `Done`, `In Progress`,
`Waiting`) rather than the built-in `State` field. They expect only unresolved
issues to be analyzed.

**Why this priority**: This is the entire bug. Today every `Done` issue leaks into
the analysis, silently corrupting results for an entire class of projects. Without
this fix the `--state open` flag is meaningless for those projects.

**Independent Test**: Feed the ingest layer a project whose issues carry a `Status`
custom field of `Done` and request `state=open`; confirm the `Done` issues are
excluded from the returned set.

**Acceptance Scenarios**:

1. **Given** a project with 21 issues (15 `Done`, 3 `In Progress`, 3 `Waiting`) whose
   state lives in a `Status` custom field, **When** the operator requests `--state open`,
   **Then** only the 6 unresolved issues are returned.
2. **Given** the same project, **When** the operator requests `--state all`,
   **Then** all 21 issues are returned.
3. **Given** a project whose state lives in the built-in `State` field (existing behavior),
   **When** the operator requests `--state open`, **Then** results are unchanged from today.

### Edge Cases

- An issue has neither a `State` nor a `Status` custom field → its state is empty; an
  empty state is treated as open (not resolved), matching today's behavior for the
  built-in field.
- A project has both a `State` and a `Status` custom field → the built-in `State` wins
  (checked first), preserving existing behavior.
- The `yt` server-side `--state Open` filter already excludes an issue → the client-side
  filter is a no-op for that issue (idempotent).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The ingest layer MUST recognize a custom field named `Status` as a source
  of an issue's workflow state, in addition to the already-recognized `State` and `Stage`.
- **FR-002**: When `--state open` is requested, the system MUST exclude issues whose
  resolved workflow state (from any recognized field) matches a closed marker
  (`closed`, `resolved`, `done`, `fixed`, `verified`), regardless of whether the server-side
  `yt` filter excluded them.
- **FR-003**: The client-side state filter MUST be applied on the production (`yt` CLI)
  read path, not only in the test fake, so behavior is consistent across sources.
- **FR-004**: `--state all` MUST continue to return every issue with no state filtering.
- **FR-005**: Existing behavior for projects using the built-in `State`/`Stage` field
  MUST be unchanged.

### Key Entities

- **Issue state**: The workflow position of an issue (open vs. resolved), sourced from
  the built-in `State` field or a `Status`/`Stage` custom field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a Status-based project, `--state open` returns zero issues whose
  `Status` is a closed marker (`Done`/`Resolved`/etc.).
- **SC-002**: For the repro project (15 `Done`, 3 `In Progress`, 3 `Waiting`),
  `--state open` returns exactly 6 issues.
- **SC-003**: No regression: every existing test in the suite continues to pass.

## Assumptions

- Sibling issue #34 (JSONDecodeError on multi-line descriptions) is already resolved by
  the shipped #29 work (`strict=False`) and a regression test exists; it needs no change
  in this feature.
- The set of closed-state markers is the existing `_matches_state` set and does not need
  to expand for this fix.
- `Status` is checked after `State`/`Stage`, so the built-in field takes precedence when
  both are present.
