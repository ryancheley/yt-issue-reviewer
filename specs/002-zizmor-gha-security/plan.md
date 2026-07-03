# Implementation Plan: zizmor GitHub Actions Security Auditing

**Branch**: `002-zizmor-gha-security` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-zizmor-gha-security/spec.md`

## Summary

Add [zizmor](https://docs.zizmor.sh) — a static analysis tool for GitHub Actions
workflows — as a **dedicated, required CI job** that audits everything under
`.github/workflows/` on every pull request and push to `main`. zizmor runs via
`uvx zizmor@<pinned>` (no new language runtime, no project dependency), in `--offline`
mode with `--persona regular` and `--min-severity medium`, exiting non-zero (codes 11–14)
when findings at/above the threshold exist. The existing `ci.yml` is remediated to a clean
baseline: hash-pinned actions (`unpinned-uses`), explicit least-privilege permissions
(`excessive-permissions`), and `persist-credentials: false` on checkout (`artipacked`).
Branch protection is updated to require the new `zizmor` check alongside `check`, so an
insecure workflow change cannot be merged.

## Technical Context

**Language/Version**: N/A for the audit itself (zizmor is a prebuilt binary run via `uvx`).
Existing CI targets Python 3.14 via uv.

**Primary Dependencies**:
- `zizmor` (run ephemerally via `uvx zizmor@<version>`; NOT added to `pyproject.toml`)
- Existing CI actions: `actions/checkout`, `astral-sh/setup-uv`

**Storage**: N/A. Optional `zizmor.yml` config at repo root only if a real finding needs a
justified suppression.

**Testing**: Validate locally with `uvx zizmor@<version> --offline .github/workflows/`
(expect exit 0 / clean). Negative test documented in quickstart: introduce a deliberate
template-injection and confirm the gate fails.

**Target Platform**: GitHub Actions `ubuntu-latest` runner.

**Project Type**: CI/infrastructure change (no application code touched).

**Performance Goals**: zizmor audit completes in seconds; adds negligible CI time and runs
in parallel with the existing `check` job.

**Constraints**:
- No new language runtime in CI (Constitution VI) — `uvx` reuses the existing uv setup.
- No new Python dependency in `pyproject.toml` — zizmor runs ephemerally.
- Least-privilege: top-level `permissions: {}`, per-job `contents: read`.
- `--offline` so no `GITHUB_TOKEN` is required for the audit; deterministic and
  network-free (aligns with the project's no-external-egress posture).
- The `check` job's status context name MUST stay `check` (branch protection depends on it).

**Scale/Scope**: One repository, currently one workflow file (`ci.yml`); the audit covers
the whole `.github/workflows/` directory so new workflows are picked up automatically.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Relevance to this feature | Status |
|---|-----------|---------------------------|--------|
| I | Privacy & Data Boundaries | zizmor runs `--offline`; no issue content, no external egress, no hosted AI. | ✅ PASS |
| II | Read-Only by Default | Pure CI/audit change; does not touch YouTrack or any write path. | ✅ N/A |
| III | Build on yt-cli | No YouTrack interaction. | ✅ N/A |
| IV | Reproducibility & Transparency | zizmor version pinned; threshold explicit; any suppression carries a written justification. | ✅ PASS |
| V | Local-First Data | No data handling. | ✅ N/A |
| VI | Simplicity | `uvx` reuses existing tooling; no new runtime, no new project dep; one small job. | ✅ PASS |
| VII | Test-First | Not application logic; validation is a local audit run + a documented negative test in quickstart. | ✅ PASS (adapted) |

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-zizmor-gha-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (config/entity shapes)
├── quickstart.md        # Phase 1 output (validation incl. negative test)
├── contracts/           # Phase 1 output
│   └── ci-audit.md      # zizmor job + workflow-hardening contract
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source (repository root) — files changed/added

```text
.github/workflows/ci.yml    # add `zizmor` job; harden existing `check` job
zizmor.yml                  # OPTIONAL — only if a real finding needs a justified suppression
```

**Structure Decision**: This is an infrastructure feature; the only production artifacts
are the CI workflow and an optional zizmor config. No `src/` or `tests/` changes. The audit
is a **separate `zizmor` job** (clearer signal, parallel to `check`) rather than a step
inside `check`; because branch protection currently requires only the `check` context,
implementation MUST add `zizmor` to the required status checks (called out as a task).

## Complexity Tracking

> No Constitution violations — this section intentionally left empty.
