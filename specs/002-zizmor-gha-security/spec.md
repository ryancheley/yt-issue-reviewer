# Feature Specification: zizmor GitHub Actions Security Auditing

**Feature Branch**: `002-zizmor-gha-security`

**Created**: 2026-07-03

**Status**: Draft

**Input**: Issue #2 — "Add zizmor GitHub Actions security auditing to CI". Add zizmor, a
static analysis tool that audits GitHub Actions workflow files for security weaknesses, to
CI so every change to a workflow is automatically checked before it can be merged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Insecure workflow changes are blocked automatically (Priority: P1)

As the maintainer, when someone opens a pull request that modifies a GitHub Actions
workflow, the CI automatically audits all workflow files for security weaknesses and fails
the check when a finding at or above the configured severity threshold is present — so an
insecure workflow change cannot be merged (branch protection already blocks merge on a
failing check).

**Why this priority**: This is the entire point of the feature — it turns "workflow
security" from a manual, easy-to-forget review step into an automated gate. Without it,
nothing else in this feature delivers value.

**Independent Test**: On a branch, introduce a deliberate workflow weakness (e.g., an
unsanitized `${{ github.event.* }}` expression interpolated into a shell `run:` step) and
open a PR; confirm the audit check fails and reports the finding. Revert it and confirm the
check passes.

**Acceptance Scenarios**:

1. **Given** a pull request that changes a workflow file to include a weakness at/above the
   threshold, **When** CI runs, **Then** the audit step fails and the finding is visible in
   the check output.
2. **Given** a pull request whose workflow files contain no findings at/above the
   threshold, **When** CI runs, **Then** the audit step passes.
3. **Given** a push to the default branch, **When** CI runs, **Then** the audit runs
   automatically with no manual step.
4. **Given** the audit fails, **When** the maintainer views the pull request, **Then** the
   merge is blocked until the check passes (via existing branch protection).

---

### User Story 2 - Existing workflows pass the audit cleanly (Priority: P1)

As the maintainer, I want the project's current workflow(s) to pass the audit with no
findings at/above the threshold, including having explicit least-privilege permissions, so
that the new gate starts green and the baseline is secure.

**Why this priority**: A gate that is red on day one is untrustworthy and gets disabled.
The existing CI must be remediated to a clean baseline as part of introducing the audit.

**Independent Test**: Run the audit against the repository's current workflow files on the
feature branch; confirm zero findings at/above the threshold, and confirm each workflow job
declares explicit permissions.

**Acceptance Scenarios**:

1. **Given** the existing workflow files, **When** the audit runs, **Then** there are no
   findings at/above the threshold.
2. **Given** the existing CI job(s), **When** inspected, **Then** each declares explicit,
   least-privilege permissions rather than inheriting broad defaults.
3. **Given** any finding that is intentionally not fixed, **When** it is suppressed,
   **Then** the suppression is recorded with a written justification.

---

### User Story 3 - Transparent, tunable audit configuration (Priority: P3)

As the maintainer, I want the audit's severity threshold and any rule suppressions to be
explicit and reviewable, so that the policy is understandable and can be tightened over
time.

**Why this priority**: Useful for long-term maintainability and trust, but the audit
delivers its core value (US1/US2) even with only default settings. This is a refinement.

**Independent Test**: Change the configured threshold and confirm the set of findings that
fail CI changes accordingly; confirm any suppression entry carries a justification.

**Acceptance Scenarios**:

1. **Given** a configured severity threshold, **When** a finding below it exists, **Then**
   CI does not fail on that finding.
2. **Given** a configured severity threshold, **When** a finding at/above it exists,
   **Then** CI fails.
3. **Given** a suppressed rule, **When** the configuration is reviewed, **Then** a
   justification for the suppression is present.

---

### Edge Cases

- **No workflow files present**: the audit completes successfully (nothing to flag) rather
  than erroring.
- **Audit tool unavailable / fails to run**: the CI check fails visibly (treated as a gate
  failure, not silently skipped) so a broken audit can't masquerade as a pass.
- **Finding exactly at the threshold**: treated as at/above the threshold and fails CI
  (threshold is inclusive).
- **Findings below the threshold**: reported for visibility where practical but do not fail
  CI.
- **A new workflow file is added**: it is audited automatically without any change to the
  audit setup (the audit covers all workflow files, not a hardcoded list).
- **Suppressed finding later becomes irrelevant**: stale suppressions should be removable
  without affecting the gate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI MUST audit all GitHub Actions workflow files in the repository for
  security weaknesses on every pull request and on every push to the default branch.
- **FR-002**: The audit MUST run automatically as part of CI with no manual trigger or
  local step required.
- **FR-003**: CI MUST fail when the audit reports one or more findings at or above a
  configured severity threshold (threshold inclusive).
- **FR-004**: Findings below the configured threshold MUST NOT fail CI, but SHOULD remain
  visible in the audit output where practical.
- **FR-005**: The audit MUST cover all workflow files automatically, including newly added
  ones, without requiring the audit configuration to enumerate files.
- **FR-006**: The existing workflow file(s) MUST pass the audit with no findings at/above
  the threshold at the time this feature is completed.
- **FR-007**: Every CI job MUST declare explicit, least-privilege permissions rather than
  relying on broad default permissions.
- **FR-008**: If the audit tool cannot run or errors, the CI check MUST fail (it MUST NOT
  be silently skipped or reported as passing).
- **FR-009**: The configured severity threshold MUST be explicit and reviewable.
- **FR-010**: Any suppression of a specific audit rule or finding MUST be accompanied by a
  written justification retained in the repository.
- **FR-011**: The audit MUST be scoped to GitHub Actions workflow files only; it MUST NOT
  be relied upon to scan application source code.
- **FR-012**: Introducing the audit MUST NOT add a new language runtime to CI beyond what
  the existing pipeline already provides.

### Key Entities *(include if feature involves data)*

- **Workflow file**: A GitHub Actions workflow definition under the repository's workflows
  directory; the subject of the audit.
- **Audit finding**: A reported security weakness with an associated severity, used to
  decide pass/fail against the threshold.
- **Severity threshold**: The configured, inclusive cutoff at/above which findings fail CI.
- **Suppression**: An explicit, justified decision to exclude a specific rule or finding
  from failing the audit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A pull request that introduces a workflow security weakness at/above the
  threshold causes CI to fail 100% of the time.
- **SC-002**: The repository's existing workflow file(s) produce zero findings at/above the
  threshold once the feature is complete.
- **SC-003**: The audit runs automatically on every pull request and every push to the
  default branch, with no manual step (0 manual actions required).
- **SC-004**: 100% of CI jobs declare explicit least-privilege permissions.
- **SC-005**: 100% of active rule/finding suppressions have a recorded written
  justification.
- **SC-006**: A broken or unavailable audit tool results in a failed CI check (never a
  false "pass").

## Assumptions

- **Existing CI**: The project already has a CI pipeline that runs on pull requests and
  pushes to the default branch; the audit is added to that pipeline rather than a new
  system.
- **Branch protection**: Merge-blocking on failing checks is already enforced by branch
  protection, so making the audit a required check is sufficient to block insecure merges.
- **Severity threshold default**: A moderate default threshold is acceptable to start
  (fail on medium-and-above), tightening later; the exact value is a tunable policy detail
  recorded in configuration, not a scope decision.
- **Reuse of existing runtime**: The audit tool integrates with the existing package/runner
  tooling already used by CI, so no additional language runtime is introduced.
- **Single maintainer workflow**: A single maintainer reviews and merges; requiring the
  audit as a status check (not human review) is the enforcement mechanism.
- **Scope**: Only GitHub Actions workflow files are in scope; broader supply-chain or
  application-code scanning is out of scope for this feature.
