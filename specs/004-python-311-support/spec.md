# Feature Specification: Support Python 3.11+

**Feature Branch**: `004-python-311-support`

**Created**: 2026-07-06

**Status**: Draft

**Input**: User description: "Support Python 3.11+ instead of requiring 3.14. Loosen the project's Python version floor from >=3.14 to >=3.11 so most users can install and run the tool. Update requires-python in pyproject.toml, add trove classifiers for 3.11/3.12/3.13, set the ty type-checker python-version target to the new minimum, and expand the CI workflow to test across Python 3.11-3.14. Audit src/ for any 3.12+/3.14-only syntax or stdlib usage and backport or guard as needed. CI must run the existing just check gate on each supported Python version. Tracked in GitHub issue #19."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Install and run on an older-but-supported Python (Priority: P1)

A user whose environment provides Python 3.11 (or 3.12/3.13) installs the tool and runs an analysis. Today the install is refused because the project demands Python 3.14; after this change the install succeeds and the tool works identically.

**Why this priority**: This is the entire point of the feature — the current 3.14 floor excludes the overwhelming majority of real-world Python environments. Without this, nobody but the maintainer can install the tool.

**Independent Test**: On a machine with only Python 3.11 available, install the package and run a representative command (e.g. the CLI's `--help` and one analysis path). Both succeed with no version-related error.

**Acceptance Scenarios**:

1. **Given** an environment with Python 3.11 as the only interpreter, **When** the user installs the package, **Then** the install succeeds without a "requires Python >=3.14" resolution error.
2. **Given** the tool installed on Python 3.11, **When** the user runs the CLI, **Then** it behaves identically to running on Python 3.14 (no runtime `SyntaxError`, `ImportError`, or missing-stdlib-attribute failure).
3. **Given** the published package metadata, **When** a user or tool inspects supported versions, **Then** Python 3.11, 3.12, 3.13, and 3.14 are all advertised as supported.

---

### User Story 2 - Every supported version is verified in CI (Priority: P1)

A maintainer merges a change and trusts that the project genuinely works on all advertised Python versions, not just the newest one, because the CI gate exercises each version.

**Why this priority**: Advertising 3.11+ without testing it is a promise the project can't keep — a version-specific regression would ship silently. The CI matrix is what makes the compatibility claim trustworthy and keeps it true over time.

**Independent Test**: Open a pull request; observe that the CI check runs the full quality gate once per supported Python version and all runs must pass before merge.

**Acceptance Scenarios**:

1. **Given** a pull request, **When** CI runs, **Then** the project's standard quality gate (lint, type check, tests) executes on Python 3.11, 3.12, 3.13, and 3.14.
2. **Given** a change that breaks on one specific version, **When** CI runs, **Then** the run for that version fails and blocks merge, while other versions may still pass.
3. **Given** all supported versions pass, **When** the maintainer merges, **Then** no version-specific quality gate was skipped or bypassed.

---

### Edge Cases

- A source file uses syntax or a stdlib feature available only in 3.12+/3.14 → the audit must find it and either backport it or guard it so 3.11 does not fail at import/runtime.
- A runtime dependency itself requires Python newer than 3.11 → the effective floor cannot be lowered below what dependencies allow; this must be detected (resolution/CI failure) and surfaced, not silently ignored.
- The type checker and CI use different notions of "minimum version" → the type-checker target and the CI matrix floor must agree on 3.11 so type errors that only appear on the minimum version are caught.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project's declared minimum Python version MUST be 3.11 (installation permitted on 3.11, 3.12, 3.13, and 3.14).
- **FR-002**: The published package metadata MUST advertise support for Python 3.11, 3.12, 3.13, and 3.14.
- **FR-003**: The type checker's target Python version MUST be set to the new minimum (3.11) so it validates against the oldest supported interpreter.
- **FR-004**: The continuous integration quality gate MUST run against each supported Python version (3.11 through 3.14), and all MUST pass for a change to be mergeable.
- **FR-005**: The source code MUST be free of syntax and standard-library usage that is unavailable on Python 3.11; any such usage found MUST be replaced with a 3.11-compatible equivalent or guarded by a version check.
- **FR-006**: The change MUST NOT alter the tool's runtime behavior or output on any currently working version (3.14); lowering the floor is additive compatibility only.
- **FR-007**: If any runtime dependency cannot be satisfied on Python 3.11, that conflict MUST surface as a failed resolution/CI run rather than a silently broken install.

### Key Entities

- **Supported Python version set**: The versions the project promises to install and run on — 3.11, 3.12, 3.13, 3.14. This set is the single source of truth reflected consistently in the version floor, the advertised classifiers, the type-checker target (its minimum), and the CI matrix (its full range).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The tool installs successfully on Python 3.11, 3.12, 3.13, and 3.14 (4 of 4 supported versions), versus 1 of 4 today.
- **SC-002**: The full quality gate passes on 100% of supported Python versions in CI.
- **SC-003**: Package metadata lists exactly the four supported versions with no gaps or unsupported versions advertised.
- **SC-004**: Zero behavioral differences in tool output between the previously-supported version (3.14) and the newly-supported versions for the same input.

## Assumptions

- The existing source already avoids 3.12+/3.14-only language features (a preliminary audit found `from __future__ import annotations` throughout, `tomllib` which is stdlib since 3.11, and no PEP 695 aliases, generic syntax, `match`, or `itertools.batched`), so the audit is expected to confirm compatibility rather than require large backports. The audit is still mandatory to guarantee this.
- All current runtime dependencies support Python 3.11 or newer; this is verified by successful resolution/CI on 3.11. If a dependency turns out to require a higher floor, that constraint wins (see FR-007) and is reported rather than worked around.
- 3.11 is an acceptable floor (rather than 3.10 or 3.9); it aligns with `tomllib` being stdlib and with the range named in issue #19.
- The existing "just check" recipe already defines the canonical quality gate (lint, type check, tests); this feature reuses it unchanged and only multiplies it across versions.
- No `src/` functional changes are expected beyond any compatibility fixes the audit turns up; this is packaging/CI/metadata work.
