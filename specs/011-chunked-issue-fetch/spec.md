# Feature Specification: Fetch issues in bounded chunks so slow/gated networks work

**Feature Branch**: `011-chunked-issue-fetch`

**Created**: 2026-07-07

**Status**: Draft

**Input**: User description: Fix issue #45 — `analyze` returns 0 issues on networks that
kill any single `yt` request running longer than ~20s, because the tool fetches the whole
project in one long request.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze a project from behind a slow/gated network (Priority: P1)

An operator runs `analyze` against a YouTrack instance reached over a remote or corporate
network whose gateway kills any request that runs longer than ~20 seconds. Fetching the
whole project at once exceeds that limit, so today they get **zero issues** with no error.
They expect the analysis to complete with all the project's issues.

**Why this priority**: This is the entire bug — the tool is unusable against any instance
behind such a gateway, silently returning nothing. Every downstream feature depends on
issues being fetched.

**Independent Test**: Drive the ingest layer with an issue source that only returns small
bounded batches per request (and refuses large ones), and confirm the tool still assembles
the complete set of issues by requesting multiple batches.

**Acceptance Scenarios**:

1. **Given** a project with more issues than fit in one bounded request, **When** the operator
   runs `analyze`, **Then** every issue is retrieved by fetching several bounded batches, and
   the ingested count equals the project's total.
2. **Given** a project small enough to fit in one bounded request, **When** the operator runs
   `analyze`, **Then** all issues are retrieved in a single batch (behavior unchanged).
3. **Given** batches that overlap at their boundaries, **When** they are combined, **Then**
   each issue appears exactly once (no duplicates).
4. **Given** an instance behind a ~20s request-time gateway, **When** the operator runs
   `analyze`, **Then** no individual request exceeds the gateway limit, so none are killed.

### Edge Cases

- **Boundary overlap**: consecutive batches may re-include issues at the shared boundary;
  the combined result must de-duplicate them.
- **Timezone skew**: the batch boundary is a date; the instance's date interpretation may
  differ from the tool's. The boundary must be chosen so no issue is skipped (overlap-and-dedup,
  never a gap).
- **Dense boundary**: if more issues than one bounded batch share a single boundary date, the
  cursor cannot advance. The tool must fail with a clear, actionable operator message
  (e.g., narrow the range or use a faster connection) rather than loop forever or silently drop.
- **Empty project**: returns zero issues with no error.
- **Existing filters**: state and date-range filtering continue to apply to the fully
  assembled set (unchanged).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST retrieve every issue in a project without issuing any single
  request large enough to exceed a slow/gated network's per-request time limit.
- **FR-002**: The system MUST retrieve issues in multiple bounded batches when a project is
  larger than one batch, and assemble them into the complete set.
- **FR-003**: The assembled set MUST contain each issue exactly once, even when batches overlap.
- **FR-004**: Batch boundaries MUST be chosen so that no issue is skipped, including under
  timezone differences between the tool and the instance.
- **FR-005**: If the project cannot be paged (more issues than one batch share a single
  boundary value), the system MUST stop and surface a clear operator-facing error with
  remediation guidance, rather than loop indefinitely or silently truncate.
- **FR-006**: A project that fits within a single bounded batch MUST behave exactly as before.
- **FR-007**: Existing state and date-range filtering MUST continue to operate on the fully
  assembled set, unchanged.

### Key Entities

- **Issue batch**: A bounded subset of a project's issues returned by one request, ordered so
  successive batches can continue from where the previous ended.
- **Batch cursor**: The position (a date derived from the last batch) from which the next
  batch resumes, chosen to overlap rather than gap.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On an instance behind a ~20s per-request gateway, `analyze` retrieves 100% of a
  project's issues (today it retrieves 0).
- **SC-002**: No single request during a full fetch exceeds the bounded batch size (kept small
  enough to complete well under the ~20s limit).
- **SC-003**: For a project that fits in one batch, the ingested issue count is unchanged from
  before.
- **SC-004**: Combining overlapping batches yields zero duplicate issues.
- **SC-005**: No regression — the full existing test suite continues to pass.

## Assumptions

- The upstream issue source can return issues ordered by creation time, bounded to a maximum
  count per request, and filtered to those created on/after a given date — the building blocks
  needed to page by a creation-date cursor (verified against a live instance).
- A batch size around 200 issues completes well under the ~20s gateway limit (measured:
  ~250 issues ≈ 8s, ~500 issues ≈ 22s and killed).
- The pathological case (more than one batch's worth of issues sharing a single creation date
  on a gated connection) is rare in practice; a clear error is acceptable there.
- This is independent of the earlier pagination work (#42): #42 fetched all issues in one
  request; this change fetches them in bounded batches so that request can never be too large.
