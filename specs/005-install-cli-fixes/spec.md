# Feature Specification: Cross-Platform Install and CLI Robustness Fixes

**Feature Branch**: `005-install-cli-fixes`

**Created**: 2026-07-06

**Status**: Draft

**Input**: Resolve issues #22 (Windows install fails on transitive `pywin32`), #23 (`ingest` crashes with a Unicode encoding error on Windows), and #24 (documented post-subcommand `--db`/`--ollama-host`/`--config` options error with "No such option").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install succeeds on Windows behind endpoint protection (Priority: P1)

An operator on Windows with a real-time endpoint scanner (e.g. Sophos Intercept X, CrowdStrike) installs the tool. The install completes without an "Access is denied" failure, because the tool no longer drags in the heavy native `pywin32` chain it never uses.

**Why this priority**: A hard install failure blocks the tool entirely for an entire class of (common, enterprise) Windows users. Nothing else matters if the tool cannot be installed.

**Independent Test**: On any platform, verify the built/installed distribution's declared dependencies no longer include the `youtrack-cli → docker → pywin32` chain, and that the tool still runs (it invokes the separately-installed `yt` binary). On Windows behind a scanner, `install` completes cleanly.

**Acceptance Scenarios**:

1. **Given** a Windows machine with an active on-access scanner, **When** the operator installs the tool, **Then** installation completes without an `os error 5 / Access is denied` failure on `pywin32`.
2. **Given** the installed tool and a separately-installed, authenticated `yt` CLI on PATH, **When** the operator runs any command, **Then** the tool functions exactly as before (it reads YouTrack through the `yt` subprocess).
3. **Given** the tool's published distribution metadata, **When** its dependency tree is inspected, **Then** `pywin32` (and the `docker` client that pulls it in) is absent from the required dependencies.

---

### User Story 2 - Fetching issues works on a Windows console (Priority: P1)

An operator on Windows runs `ingest` (or any command that shells out to `yt`). The command fetches issues successfully instead of crashing with a Unicode encoding error when the child `yt` process prints a non-ASCII character (e.g. an emoji) to a legacy code-page console.

**Why this priority**: The first real command an operator runs (`ingest`) crashes on Windows, making the tool unusable there even after a successful install.

**Independent Test**: Force the child subprocess into a non-UTF-8 default code page and confirm the tool still captures and parses `yt` output without a `UnicodeEncodeError`. Verify the subprocess is invoked with a UTF-8 I/O environment on all platforms.

**Acceptance Scenarios**:

1. **Given** a Windows console using a legacy code page (e.g. cp1252), **When** the operator runs `ingest --project P` and the `yt` child emits a non-ASCII character, **Then** the command completes and returns issues rather than raising `UnicodeEncodeError`.
2. **Given** any platform, **When** the tool spawns the `yt` subprocess, **Then** the child is instructed to use UTF-8 for its standard I/O and the tool decodes the captured output as UTF-8.

---

### User Story 3 - Documented CLI option placement works (Priority: P2)

An operator follows the README/quickstart and passes `--db`, `--ollama-host`, or `--config` after the subcommand (e.g. `analyze --project P --db ./yir.db --ollama-host URL`, `doctor --ollama-host URL`, `show --db ./yir.db`). The command accepts the options instead of erroring with "No such option".

**Why this priority**: Every post-subcommand example in the current docs is broken, so users copy-pasting documented commands hit an immediate error. It blocks correct usage but has a manual workaround (move the option before the subcommand), so it ranks below the outright failures.

**Independent Test**: Run each documented command form with the option placed after the subcommand and confirm it is accepted and applied. Confirm the docs and the CLI agree on placement.

**Acceptance Scenarios**:

1. **Given** the tool, **When** the operator runs `analyze --project P --db ./yir.db --ollama-host URL`, **Then** the command runs and uses the supplied database path and Ollama host.
2. **Given** the tool, **When** the operator runs `doctor --ollama-host URL` or `show --db ./yir.db`, **Then** the option is accepted rather than rejected as "No such option".
3. **Given** the documentation, **When** a reader copies any command example, **Then** the shown option placement matches what the CLI accepts.

---

### Edge Cases

- **`yt` not installed / not authenticated**: Because `youtrack-cli` is no longer a bundled dependency, the tool must still fail with the existing clear, actionable message ("the 'yt' CLI was not found on PATH. Install youtrack-cli and run `yt auth login`.") rather than an opaque error.
- **Option provided both before and after the subcommand**: The behavior must be deterministic and documented (later/more-specific placement wins, or an equivalent well-defined rule).
- **Non-UTF-8 bytes in `yt` output**: Decoding should not hard-crash on stray undecodable bytes; the tool should degrade gracefully rather than raise.
- **Existing config precedence unchanged**: Adding option placement must not alter the documented precedence (explicit CLI value > env var > TOML file > default).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool's required runtime dependencies MUST NOT include `youtrack-cli` (nor the transitive `docker`/`pywin32` chain it introduces). `youtrack-cli` remains a documented external prerequisite that the operator installs and authenticates separately.
- **FR-002**: Removing `youtrack-cli` as a bundled dependency MUST NOT change how the tool reads YouTrack: all reads continue to go through the `yt` CLI subprocess (Constitution Principle III), and the read-only guarantee is preserved.
- **FR-003**: The tool MUST spawn the `yt` subprocess with an environment that forces UTF-8 standard I/O in the child process, and MUST decode the captured subprocess output as UTF-8, so that non-ASCII output does not cause an encoding crash on any platform.
- **FR-004**: The UTF-8 subprocess behavior MUST apply to every place the tool invokes `yt` (both the availability/auth check and the issue-list fetch).
- **FR-005**: The `--db`, `--ollama-host`, and `--config` options MUST be accepted when placed after the subcommand for every command the documentation shows them with, matching the documented usage.
- **FR-006**: Option resolution MUST preserve the existing configuration precedence (explicit CLI value > environment variable > TOML file > built-in default) and MUST NOT change the resolved value for any currently-working invocation.
- **FR-007**: All documentation (README and docs site) MUST show option placements that the CLI actually accepts; docs and CLI MUST agree.
- **FR-008**: The install/prerequisite documentation MUST continue to clearly state that `youtrack-cli` must be installed and authenticated separately.
- **FR-009**: The dependency lock file MUST be regenerated to reflect the removed dependency, and the project's quality gate (lint, type-check, tests) MUST pass.
- **FR-010**: No change to analysis behavior — scoring, embeddings, evidence, and output MUST be unchanged by this feature.

### Key Entities

*Not applicable — this feature changes packaging, subprocess invocation, and CLI wiring; it introduces no new domain data.*

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Inspecting the installed distribution's dependency tree shows zero occurrences of `pywin32` and `docker` among required dependencies.
- **SC-002**: On a Windows console using a legacy (non-UTF-8) code page, `ingest` completes without a `UnicodeEncodeError` in 100% of runs where `yt` emits non-ASCII output.
- **SC-003**: 100% of the option-placement examples shown in the README and docs execute without a "No such option" error.
- **SC-004**: The full project quality gate (lint, type-check, tests) passes, and analysis output for an equivalent run is byte-for-byte identical to output produced before this change.

## Assumptions

- `youtrack-cli` is expected to be installed separately by the operator (already stated as a prerequisite in the installation docs, and matching how real users install it — e.g. via pipx). The tool has never imported the `youtrack_cli` Python package; it only invokes the `yt` binary on PATH.
- Forcing UTF-8 in the child subprocess environment is safe on all supported platforms (Python 3.11+) and does not affect the parsed JSON payload, which is already UTF-8/ASCII.
- Making the three options accept post-subcommand placement is preferred over rewriting all docs to put them before the subcommand, because post-subcommand placement is the more natural CLI ergonomics and matches every existing example.
- The change targets the currently-supported interpreter range (Python 3.11–3.14) and introduces no new third-party dependency.
