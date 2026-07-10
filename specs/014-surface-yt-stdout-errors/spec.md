# Feature Specification: Surface `yt`'s stdout in failure messages

**Feature Branch**: `014-surface-yt-stdout-errors`

**Created**: 2026-07-09

**Status**: Draft

**Input**: User description: Implement issue #54 — include `yt`'s stdout in the
`YouTrackUnavailable` error so failures show the real reason (e.g. "Not authenticated").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the real reason a `yt` call failed (Priority: P1)

An operator runs `analyze` and it fails because `yt` returned an error. They expect the error
message to tell them *why* — especially actionable causes like "not authenticated" — so they
know what to do next (e.g. re-run `yt auth login`).

**Why this priority**: Today the tool shows only `yt`'s stderr, but `yt` frequently writes the
actual reason to stdout (e.g. youtrack-cli 0.24.5 prints `❌ Not authenticated` to stdout while
stderr only carries the generic `Error: Failed to list issues`). Operators get a vague message
and misdiagnose an auth problem as a network/permission one.

**Independent Test**: Simulate a `yt` failure where the reason is on stdout and confirm the
raised error message contains that reason.

**Acceptance Scenarios**:

1. **Given** a `yt` invocation that exits non-zero with the reason (e.g. `❌ Not authenticated`)
   on **stdout** and a generic message on stderr, **When** the tool raises its error, **Then** the
   message includes the stdout reason.
2. **Given** a `yt` invocation that exits non-zero with the reason only on **stderr**, **When**
   the tool raises its error, **Then** the message still includes the stderr text (unchanged).
3. **Given** a successful `yt` invocation, **When** the tool runs, **Then** behavior is unchanged
   (no error, output parsed as before).

### Edge Cases

- Both stdout and stderr have content → the message includes both (no duplication of empty parts).
- One stream is empty → only the non-empty stream appears; no stray blank lines.
- The existing operator guidance for the auth-check failure (e.g. "Run `yt auth login`") is
  preserved alongside the newly-included stream text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a `yt` invocation exits non-zero, the raised failure message MUST include the
  reason `yt` wrote to stdout, in addition to stderr.
- **FR-002**: Both `yt` failure points — the availability/auth check and the issue-list fetch —
  MUST include stdout in their failure messages.
- **FR-003**: When a stream (stdout or stderr) is empty, it MUST be omitted from the message with
  no leftover blank lines.
- **FR-004**: The existing operator-facing guidance (e.g. "Run `yt auth login`" on the auth-check
  failure) MUST be preserved.
- **FR-005**: The success path MUST be unchanged — output is still parsed normally and no error is
  raised when `yt` succeeds.

### Key Entities

- **`yt` failure output**: The combination of the subprocess's stdout and stderr, which together
  carry the human-readable reason a command failed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a failure whose reason is on stdout (e.g. "Not authenticated"), the operator-visible
  error message contains that reason (today it does not).
- **SC-002**: For a failure whose reason is only on stderr, the message is unchanged from today.
- **SC-003**: No regression — the full existing test suite passes and successful runs behave as before.

## Assumptions

- Both `yt` streams are worth showing on failure; combining them is safe because on success neither
  is surfaced. The excerpt/length behavior of existing messages is otherwise unchanged.
- This complements the upstream youtrack-cli ticket about 0.24.5 invalidating stored auth on
  upgrade; here we only improve the *diagnosability* of any `yt` failure, not the auth handling.
