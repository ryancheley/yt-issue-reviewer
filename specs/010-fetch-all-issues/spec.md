# Feature Specification: Fetch every issue in a project, not just the first page

**Feature Branch**: `010-fetch-all-issues`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: Fix issue #42 — `analyze` silently returns only the first 100
issues per project because the underlying `yt` fetch is not paginated.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze a project with more than 100 issues (Priority: P1)

An operator runs `analyze` against a large project (for example, one imported from Jira
with several hundred issues) and expects every matching issue to be considered in the
analysis.

**Why this priority**: This is the whole bug. Today issues beyond the first 100 are
silently dropped, so the analysis is incomplete and misleading for any non-trivial project
— with no warning that results are truncated.

**Independent Test**: Point the ingest layer at a source returning more than one page of
issues and confirm the returned set includes issues beyond the first page.

**Acceptance Scenarios**:

1. **Given** a project with 250 issues, **When** the operator runs `analyze --state all`,
   **Then** all 250 issues are ingested (not 100).
2. **Given** a project with fewer than 100 issues, **When** the operator runs `analyze`,
   **Then** all of them are ingested (unchanged behavior).
3. **Given** a project with more than 100 open issues, **When** the operator runs
   `analyze --state open`, **Then** every open issue is considered (state filtering and
   pagination compose correctly).

### Edge Cases

- A project with exactly 100 issues → all 100 returned (no off-by-one at the page boundary).
- A project with 0 issues → empty result, no error.
- Pagination and the existing client-side state/date filters compose: filtering happens
  after the full set is fetched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST retrieve every issue in each requested project, regardless of
  how many pages the upstream issue source returns them in.
- **FR-002**: The number of issues ingested MUST NOT be capped by a default page size.
- **FR-003**: Existing client-side filtering (state, date range) MUST continue to operate on
  the complete fetched set, unchanged.
- **FR-004**: Behavior for projects with fewer issues than one page MUST be unchanged.
- **FR-005**: If the full fetch cannot be completed, the operator MUST get a clear failure
  rather than a silently truncated result set (no regression of existing error handling).

### Key Entities

- **Issue page**: A subset of a project's issues returned by one upstream request; the full
  project is the union of all pages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a project with N issues (N > 100), `analyze --state all` ingests exactly N
  issues (currently ingests 100).
- **SC-002**: For a project with ≤ 100 issues, the ingested count is unchanged from today.
- **SC-003**: No regression — the full existing test suite continues to pass.

## Assumptions

- The upstream `yt` CLI provides a pagination mode that returns the complete result set;
  enabling it is sufficient (no manual page-looping needed in this tool).
- Fetching all issues per project is acceptable for the tool's scale and existing timeout;
  the tool already holds the full per-project set in memory for client-side filtering.
- This is independent of the state/stage field investigation — issues past the first page
  are lost for any state.
