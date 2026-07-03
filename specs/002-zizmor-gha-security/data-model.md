# Phase 1 Data Model: zizmor GitHub Actions Security Auditing

This feature has no application data. The "entities" are configuration/policy artifacts and
the shape of an audit result. Captured here for traceability to the spec's Key Entities.

## Entity: Workflow file

A GitHub Actions workflow definition under `.github/workflows/` (currently `ci.yml`). The
subject of the audit.

- **Location**: `.github/workflows/*.yml`
- **Relevant hardening attributes** (validated by the audit):
  - top-level `permissions` (should be `{}`)
  - per-job `permissions` (least-privilege, e.g. `contents: read`)
  - each `uses:` reference (should be a full commit SHA + version comment)
  - `actions/checkout` `persist-credentials` (should be `false`)
- **Validation rule**: MUST produce no zizmor findings at/above the threshold (FR-006).

## Entity: Audit invocation (policy)

The parameters that define how the audit runs — the explicit, reviewable policy (FR-009).

| Field | Value | Meaning |
|-------|-------|---------|
| `version` | `1.26.1` (pinned) | zizmor version, for reproducibility (FR/Constitution IV) |
| `path` | `.github/workflows/` | audited target (all workflow files → FR-005) |
| `min_severity` | `medium` | inclusive gating threshold (FR-003) |
| `persona` | `regular` | signal level |
| `offline` | `true` | no network / token (R3) |
| `format` | `github` | inline PR annotations |

Encoded in `.github/workflows/ci.yml` (the `zizmor` job) — the single source of truth.

## Entity: Audit finding

A security weakness reported by the audit. Not persisted by us; produced by zizmor and
surfaced in CI logs / PR annotations.

- **Fields**: rule/audit id (e.g. `unpinned-uses`), severity
  (`informational|low|medium|high`), location (`file:line:col`), message.
- **Gating rule**: a finding with `severity >= min_severity` fails CI (exit 11–14).
- **State**: `reported` (visible) → either `remediated` (fixed in the workflow) or
  `suppressed` (see below).

## Entity: Suppression

An explicit, justified exclusion of a specific rule/finding (FR-010, SC-005). Only created
if a real finding cannot be remediated.

- **Form**: an entry in `zizmor.yml` under `rules.<audit-id>.ignore` (`file[:line[:col]]`),
  or an inline `# zizmor: ignore[<rule>]` comment.
- **Required attribute**: a written **justification** adjacent to the suppression.
- **Invariant**: no suppression exists without a justification; unused suppressions are
  removed.

## State transition: a workflow change

```text
workflow edited ──▶ zizmor job runs ──▶ finding >= threshold?
                                           │
                                   yes ────┴──▶ CI fails ──▶ merge blocked (branch protection)
                                    no  ───────▶ CI passes ─▶ mergeable
```
