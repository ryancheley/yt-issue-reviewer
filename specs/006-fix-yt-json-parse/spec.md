# Feature Specification: Graceful handling of non-JSON `yt` output

**Feature Branch**: `006-fix-yt-json-parse`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "Fix issue #29: the `analyze` command crashes with an uncaught `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` when the `yt` CLI subprocess returns output that is not valid JSON. Common triggers (Windows especially): a leading UTF-8 BOM that `.strip()` does not remove, or the yt CLI printing a human-readable banner/table/warning to stdout instead of JSON. The user should get a clear, actionable error instead of a raw Python traceback. Related to #24. No change to analysis behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - BOM-prefixed JSON is parsed successfully (Priority: P1)

An operator on Windows runs `analyze` against a real YouTrack project. The `yt` CLI
emits valid JSON but prepends a UTF-8 byte-order mark (BOM). Today the run crashes with a
raw traceback even though the payload is perfectly good JSON.

**Why this priority**: This is the most likely real-world cause of issue #29 — the reported
error (`Expecting value: line 1 column 1 (char 0)`) is the exact signature of a leading BOM,
and it makes the tool completely unusable for the affected operators. Recovering here means
the command *succeeds* rather than merely failing more nicely.

**Independent Test**: Feed the JSON loader a valid issue-list payload prefixed with a BOM and
confirm the issues parse identically to the un-prefixed payload.

**Acceptance Scenarios**:

1. **Given** the `yt` CLI returns valid issue JSON prefixed with a UTF-8 BOM, **When** the
   operator runs `analyze`, **Then** the issues are parsed normally and analysis proceeds
   with no error.
2. **Given** the `yt` CLI returns valid issue JSON with no BOM, **When** the operator runs
   `analyze`, **Then** behavior is unchanged from today.

---

### User Story 2 - Non-JSON output produces a clear, actionable error (Priority: P1)

An operator runs `analyze` and the `yt` CLI writes something that is not JSON to stdout — a
human-readable banner, a table, a warning, or a partial/garbled response — while still exiting
0. Today this surfaces as a raw `json.decoder.JSONDecodeError` traceback that names Python
internals and gives the operator no idea what went wrong or what to do.

**Why this priority**: Even after the BOM case is handled, any other non-JSON stdout must fail
comprehensibly. A traceback is a dead end for a non-developer operator; a clear message that
shows what `yt` actually returned lets them diagnose (wrong `yt` version, `--format json`
unsupported, auth banner, etc.).

**Independent Test**: Feed the JSON loader a non-JSON string and confirm it raises the
project's operator-facing "YouTrack unavailable" error (not `JSONDecodeError`), and that the
message includes a snippet of the offending output.

**Acceptance Scenarios**:

1. **Given** the `yt` CLI exits 0 but prints non-JSON text to stdout, **When** the operator
   runs `analyze`, **Then** the command stops with a clear operator-facing error identifying
   that `yt` did not return JSON, including a short excerpt of the actual output, and does
   **not** print a Python traceback.
2. **Given** the offending output is very long, **When** the error is shown, **Then** the
   excerpt is truncated to a readable length rather than dumping the entire payload.

---

### Edge Cases

- **Empty stdout**: already handled today (returns no issues); behavior MUST be preserved.
- **Whitespace-only stdout**: treated the same as empty (no issues).
- **BOM followed by empty/whitespace**: treated as empty (no issues), not an error.
- **Valid JSON that is not a list/wrapper** (e.g. a bare string or number): treated as "no
  issues" exactly as today — this change does not tighten payload-shape validation.
- **Very long non-JSON output**: excerpt truncated in the error message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST strip a leading UTF-8 byte-order mark from `yt` stdout before
  attempting to parse it as JSON.
- **FR-002**: The system MUST parse BOM-prefixed valid JSON identically to the same payload
  without a BOM.
- **FR-003**: When `yt` stdout is neither empty nor valid JSON, the system MUST raise the
  project's existing operator-facing "YouTrack unavailable" error instead of allowing a raw
  `JSONDecodeError` (or any raw Python exception) to propagate.
- **FR-004**: The operator-facing error MUST include a short, truncated excerpt of the actual
  offending output to aid diagnosis.
- **FR-005**: The system MUST preserve existing behavior for empty and whitespace-only output
  (no issues, no error).
- **FR-006**: The change MUST NOT alter analysis behavior, scoring, or the shape of parsed
  issues for any input that already parses successfully today.

### Key Entities

- **`yt` stdout**: the raw text captured from the `yt issues list --format json` subprocess;
  the sole input to the JSON-loading step being hardened.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A valid issue payload prefixed with a UTF-8 BOM parses to the same issues as the
  un-prefixed payload (100% equivalence).
- **SC-002**: Non-JSON stdout never produces a `json.decoder.JSONDecodeError` traceback to the
  operator; it produces the operator-facing "YouTrack unavailable" error every time.
- **SC-003**: The reproduction from issue #29 (BOM-prefixed output) no longer crashes.
- **SC-004**: The existing test suite continues to pass with no analysis-behavior changes.

## Assumptions

- The most probable cause of the reported error is a leading UTF-8 BOM; a table/banner/warning
  is the secondary case. Both are covered.
- The project already exposes an operator-facing "YouTrack unavailable" error used elsewhere in
  the ingest path; reusing it keeps error presentation consistent (no new error type needed).
- Fixing the shared JSON-loading step covers every caller (all projects, all subcommands that
  ingest), not just the single path named in the traceback.
- "Truncated excerpt" means a small, fixed number of leading characters — enough to recognize
  the output, not the whole payload.
