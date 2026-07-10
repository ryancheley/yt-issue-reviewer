# Feature Specification: Tolerate invalid backslash escapes in `yt` JSON output

**Feature Branch**: `012-fix-invalid-json-escape`

**Created**: 2026-07-09

**Status**: Draft

**Input**: User description: Fix issue #48 — `analyze` crashes with `JSONDecodeError: Invalid
\escape` when `yt`'s JSON contains an unescaped backslash (e.g. a Windows path or regex in
issue text).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze issues whose text contains backslashes (Priority: P1)

An operator runs `analyze` against a project whose issue descriptions contain literal
backslashes — a Windows file path like `C:\Users\...`, a regular expression like `\d+`, or an
escape sequence in a code snippet — which `yt` emits as JSON without properly escaping the
backslash. They expect the analysis to complete over all issues, not crash.

**Why this priority**: This is the entire bug. Today a single issue with an unescaped backslash
aborts the whole run with a raw stack trace, so the operator gets no analysis at all and no
usable explanation.

**Independent Test**: Feed the JSON-loading step a payload containing an unescaped backslash
inside a string value and confirm it returns the parsed issues instead of raising.

**Acceptance Scenarios**:

1. **Given** `yt` output containing an issue description with an unescaped backslash (e.g.
   `C:\Users` or `\d+`), **When** the operator runs `analyze`, **Then** all issues are parsed
   and the analysis completes.
2. **Given** `yt` output that is well-formed JSON, **When** it is loaded, **Then** it parses
   exactly as before (no change to the normal path).
3. **Given** `yt` output that is not JSON at all (a banner/warning/error text), **When** it is
   loaded, **Then** the operator still gets the existing clear, non-crash error explaining that
   `yt` did not return JSON.

### Edge Cases

- **Valid escapes preserved**: strings already containing valid JSON escapes (`\n`, `\t`,
  `\"`, `\\`, `\/`, `\uXXXX`) must parse to the same values as before — the repair must not
  corrupt them.
- **Control characters** (the earlier #29/#34 case) continue to be tolerated.
- **Empty / whitespace / BOM-prefixed** output continues to behave as today (empty list, no
  error).
- **Still-unparseable** output (malformed beyond stray backslashes) yields the existing
  operator-facing error, not a raw traceback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST successfully parse `yt` JSON output that contains backslashes not
  forming a valid JSON escape sequence (e.g. inside Windows paths or regular expressions).
- **FR-002**: The repair MUST NOT alter strings that already contain valid escape sequences —
  their parsed values must be identical to the pre-fix behavior.
- **FR-003**: Well-formed JSON MUST continue to parse unchanged; the repair applies only as a
  fallback after a normal parse fails.
- **FR-004**: Output that cannot be parsed even after repair MUST surface the existing
  operator-facing "did not return valid JSON" error with a truncated excerpt — never a raw
  stack trace.
- **FR-005**: Existing handling of empty, whitespace-only, BOM-prefixed, and control-character
  output MUST be unchanged.

### Key Entities

- **Issue payload**: The raw text `yt` prints to stdout, expected to be JSON but occasionally
  malformed (control characters #29/#34, or invalid backslash escapes here).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project whose issues contain unescaped backslashes is analyzed successfully
  (currently: crashes with a traceback on the first such issue).
- **SC-002**: For well-formed JSON, the parsed result is identical to before the change.
- **SC-003**: Genuinely non-JSON output raises the existing clear error, not a raw traceback.
- **SC-004**: No regression — the full existing test suite continues to pass.

## Assumptions

- The goal is a parseable, analyzable result, not byte-perfect reconstruction of the operator's
  intended text: repairing a stray backslash makes the surrounding text parse, which is
  sufficient for relatedness analysis.
- The reporter's stack trace is from a pre-0.3.4 build; they should also upgrade. Newer
  `youtrack-cli` (0.24.4) parses API responses leniently, which may avoid this upstream — but
  hardening our shared JSON loader is the durable fix regardless of the operator's `yt` version.
- This is the same failure class as #29/#34 (`yt` emitting malformed JSON) and is fixed in the
  same shared function, so all subcommands/callers benefit.
