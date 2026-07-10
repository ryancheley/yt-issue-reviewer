# Feature Specification: `--version` flag for the CLI

**Feature Branch**: `013-add-version-flag`

**Created**: 2026-07-09

**Status**: Draft

**Input**: User description: Implement issue #51 — add a `--version` flag so
`yt-issue-reviewer --version` prints the installed version instead of erroring.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check the installed version (Priority: P1)

A user (or someone triaging a bug report) wants to know which version of the tool is installed.
They run `yt-issue-reviewer --version` and expect it to print the version and exit cleanly.

**Why this priority**: `--version` is a near-universal CLI convention and the first thing people
reach for. It's also directly valuable for support here: several recent issues turned out to be
from users on old builds, so a quick version check makes triage far easier. Today the command
errors, which is confusing and looks broken.

**Independent Test**: Invoke the CLI with `--version` and confirm it prints the version string
and exits successfully.

**Acceptance Scenarios**:

1. **Given** the tool is installed, **When** the user runs `yt-issue-reviewer --version`,
   **Then** it prints `yt-issue-reviewer, version <X.Y.Z>` and exits with status 0.
2. **Given** the tool is installed, **When** the user runs the short form `-V`, **Then** it
   prints the same version and exits with status 0.
3. **Given** a released build, **When** the version is printed, **Then** it matches the version
   declared for the package (the single source of truth), with no separately hardcoded value.

### Edge Cases

- `--version` short-circuits before any subcommand runs — it needs no YouTrack/Ollama/network
  access and never touches the database.
- The existing `--verbose` option and all subcommands continue to work unchanged (the new flag
  must not collide with or shadow them).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Running the CLI with `--version` MUST print the installed version and exit with
  status 0, without running any subcommand.
- **FR-002**: `-V` MUST be accepted as a short alias for `--version`.
- **FR-003**: The printed version MUST match the package's single source of truth (installed
  distribution metadata); no second, separately maintained copy may be introduced.
- **FR-004**: The output MUST identify the program (e.g. `yt-issue-reviewer, version X.Y.Z`).
- **FR-005**: Existing options (including `--verbose`) and all subcommands MUST continue to work
  unchanged.

### Key Entities

- **Tool version**: The package's declared version, already exposed in the codebase as a single
  source of truth read from installed distribution metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `yt-issue-reviewer --version` exits 0 and prints the version (today it exits with an
  error).
- **SC-002**: The printed version equals the package's declared version — verifiable by comparing
  the output to the source-of-truth version value.
- **SC-003**: `-V` produces the same result as `--version`.
- **SC-004**: No regression — the full existing test suite continues to pass and all subcommands
  behave as before.

## Assumptions

- The version is already available in code as a single source of truth
  (`yt_issue_reviewer.__version__`, read from installed metadata), so this feature only exposes
  it on the command line — it does not introduce or duplicate a version value.
- The conventional output format (`<prog>, version <X.Y.Z>`) is acceptable; exact wording is a
  detail, not a requirement beyond identifying the program and version.
