# Feature Specification: Repair a backslash immediately before a newline in `yt` JSON

**Feature Branch**: `015-fix-backslash-newline-escape`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: Fix issue #57 — `analyze` still crashes with `Invalid \escape`
when a `yt` issue description ends a line with a literal backslash followed by a raw newline;
the #48 backslash-repair misses this case.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze issues whose text has a backslash at a line end (Priority: P1)

An operator runs `analyze` against a project whose issue text contains a literal backslash at
the end of a line (followed by a real line break) — `yt` emits that as a backslash directly
before a raw newline, which is invalid JSON. They expect the analysis to complete over all
issues, not crash.

**Why this priority**: This is the entire bug. The #48 repair fixed most unescaped-backslash
cases, but a backslash right before a newline slips through, so a single such issue still aborts
the whole run with a raw `Invalid \escape` error and no analysis is produced.

**Independent Test**: Feed the JSON-loading step a payload with a backslash immediately before a
raw newline inside a string value and confirm it returns the parsed issues instead of raising.

**Acceptance Scenarios**:

1. **Given** `yt` output whose issue description ends a line with a literal backslash directly
   before a raw newline, **When** the operator runs `analyze`, **Then** all issues are parsed and
   the analysis completes.
2. **Given** `yt` output containing already-valid escapes (`\n`, `\t`, `\"`, `\\`, `\/`,
   `\uXXXX`), **When** it is loaded, **Then** it parses to the same values as before (no
   corruption).
3. **Given** the earlier #48 cases (Windows path `C:\Users`, regex `\d+`), **When** they are
   loaded, **Then** they still parse (no regression).
4. **Given** `yt` output that is genuinely not JSON, **When** it is loaded, **Then** the operator
   still gets the existing clear "did not return valid JSON" error, not a raw traceback.

### Edge Cases

- A backslash before a newline vs. before any other character — both must be repaired.
- Valid escapes and already-escaped backslashes must remain intact.
- Empty / whitespace / BOM-prefixed / control-character output continues to behave as today.
- Output still unparseable after repair yields the existing operator-facing error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST parse `yt` JSON in which a backslash is immediately followed by a
  raw newline inside a string value (a literal backslash at a line end).
- **FR-002**: The repair MUST also continue to handle a backslash followed by any other invalid
  escape character (the #48 cases), and MUST NOT alter valid escape sequences.
- **FR-003**: Well-formed JSON MUST continue to parse unchanged; the repair applies only as a
  fallback after a normal parse fails.
- **FR-004**: Output that cannot be parsed even after repair MUST surface the existing
  operator-facing "did not return valid JSON" error, never a raw stack trace.
- **FR-005**: Existing handling of empty, whitespace, BOM-prefixed, and control-character output
  MUST be unchanged, and the full existing test suite MUST continue to pass.

### Key Entities

- **Issue payload**: The raw text `yt` prints, expected to be JSON but occasionally malformed —
  here, an unescaped backslash directly before a newline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A project whose issue text has a backslash at a line end is analyzed successfully
  (currently crashes with `Invalid \escape`).
- **SC-002**: For well-formed JSON, the parsed result is identical to before the change.
- **SC-003**: The #48 cases (Windows paths, regexes) and valid escapes still parse correctly.
- **SC-004**: No regression — the full existing test suite continues to pass.

## Assumptions

- The goal is a parseable, analyzable result, not byte-perfect reconstruction: turning an
  invalid backslash-before-newline into an escaped backslash plus a (tolerated) raw newline is
  sufficient for relatedness analysis.
- This is a narrow sub-case of #48 (same `Invalid \escape` error class, different trigger) and is
  fixed in the same shared repair path, so all callers/subcommands benefit.
- Reported live on 0.3.9 against a real NGDEV project (error at line 5439 column 79).
