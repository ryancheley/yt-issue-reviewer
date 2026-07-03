# Implementation Plan: Developer Infrastructure & Release Readiness

**Branch**: `003-dev-infrastructure` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-dev-infrastructure/spec.md` (bundles
issues #3 Dependabot, #5 release workflow, #6 docs, #7 justfile).

## Summary

Four cohesive infrastructure/DX additions, no application-code changes:

1. **Dependabot** (`.github/dependabot.yml`) — monthly, grouped update PRs for the `uv`
   Python ecosystem and `github-actions`; keeps hash-pinned action SHAs fresh.
2. **Release workflow** (`.github/workflows/release.yml`) — on a `v*` tag, `uv build` then
   publish via `pypa/gh-action-pypi-publish` using **PyPI Trusted Publishing (OIDC, no
   stored token)**, TestPyPI dry-run → PyPI, then a generated GitHub Release. Plus PyPI
   metadata in `pyproject.toml` and a `LICENSE` file.
3. **Docs** — `README.md` expansion + `docs/*.md` + `CONTRIBUTING.md`: install, quickstart,
   CLI reference, configuration, architecture, privacy/security, Datasette, contributing.
4. **`justfile`** — developer recipes whose `check` recipe reproduces the exact CI gate
   (ruff, ruff format, ty, pytest, zizmor) so local == CI.

Every new workflow is least-privilege and hash-pinned so the required `zizmor` audit stays
green. No real PyPI publish and no tag push are performed here — those are maintainer
actions gated on one-time Trusted-Publisher setup.

## Technical Context

**Language/Version**: Python 3.14 (unchanged). New artifacts are YAML, Markdown, TOML, and
a justfile — no application code.

**Primary Dependencies**:
- Existing: uv, ruff, ty, pytest, `zizmor` (via `uvx`), `just` (dev tool, 1.42 present).
- Release actions (hash-pinned): `actions/checkout@…v5.0.1`,
  `astral-sh/setup-uv@…v6.8.0`, `pypa/gh-action-pypi-publish@…v1.14.0`.
- No new entries in `pyproject.toml` `dependencies`/`dev` (zizmor stays `uvx`-only).

**Storage**: N/A.

**Testing**: `just check` (== CI gate) green locally; `uv build` produces sdist+wheel;
`uvx twine check dist/*` passes; `zizmor` audit of `release.yml` clean; `dependabot.yml` /
`release.yml` valid YAML; existing `pytest` suite unchanged and green.

**Target Platform**: GitHub Actions `ubuntu-latest`; local dev on macOS/Linux.

**Project Type**: Infrastructure / tooling / docs (single project).

**Performance Goals**: N/A (CI-time only; release build is seconds).

**Constraints**:
- No application/runtime/behavior changes (FR-025).
- New workflows: top-level `permissions: {}`, least-privilege per-job perms, actions
  hash-pinned with `# vX.Y.Z`, checkout `persist-credentials: false` (FR-024, zizmor).
- Release auth is credential-less (OIDC Trusted Publishing); no stored token (FR-020).
- `just check` must equal the CI gate exactly (FR-009, SC-003).
- Real publish/tag out of scope; requires maintainer Trusted-Publisher setup.

**Scale/Scope**: One repo; 2 workflow files total after this (ci.yml + release.yml); a
handful of docs pages.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Relevance | Status |
|---|-----------|-----------|--------|
| I | Privacy & Data Boundaries | No issue data touched; zizmor `--offline`; release publishes our own package metadata only. Docs reinforce the privacy posture. | ✅ PASS |
| II | Read-Only by Default | No YouTrack interaction; no app behavior change. | ✅ N/A |
| III | Build on yt-cli | No YouTrack access. (Docs reference `youtrack_cli` correctly.) | ✅ N/A |
| IV | Reproducibility & Transparency | Actions + zizmor pinned to exact versions; Dependabot keeps them current transparently; release notes auto-generated. | ✅ PASS |
| V | Local-First Data | N/A. | ✅ N/A |
| VI | Simplicity | Markdown docs (no site); 2-job release mirroring yt-cli (fewest pinned actions); justfile wraps existing commands; no new deps. | ✅ PASS |
| VII | Test-First | Not app logic; validation is `just check` + `uv build`/`twine check` + zizmor audit + unchanged pytest suite. | ✅ PASS (adapted) |

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-dev-infrastructure/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (config/metadata shapes)
├── quickstart.md        # Phase 1 output (validation steps)
├── contracts/           # Phase 1 output
│   ├── dependabot.md    # update-config contract
│   ├── release.md       # release-workflow + metadata contract
│   └── justfile.md      # recipe contract (check == CI)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source (repository root) — files changed/added

```text
.github/dependabot.yml          # NEW — uv + github-actions, monthly, grouped
.github/workflows/release.yml   # NEW — tag-driven build + Trusted Publishing + release
pyproject.toml                  # EDIT — license, classifiers, urls, keywords
LICENSE                         # NEW — MIT
justfile                        # NEW — dev recipes; `check` == CI gate
README.md                       # EDIT — expand (overview, install, quickstart, links)
CONTRIBUTING.md                 # NEW — required checks + branch/PR workflow
docs/                           # NEW — Markdown docs set
├── installation.md
├── quickstart.md
├── cli-reference.md
├── configuration.md
├── architecture.md
├── privacy-and-security.md
└── releasing.md                # incl. one-time Trusted-Publisher setup steps
```

(Existing `docs/yt-cli-upstream-candidates.md` stays.)

**Structure Decision**: Infrastructure feature — no `src/`/`tests/` changes. The release
workflow uses **two jobs** (`testpypi` → `pypi`), each building with `uv build`, mirroring
yt-cli; this minimizes the number of pinned actions (no artifact-passing actions) at the
cost of building twice (cheap). Trusted Publishing uses GitHub Environments (`testpypi`,
`pypi`) so publishing is gated without any stored secret. The justfile's `check` recipe is
the single source that must stay identical to `ci.yml`'s gate.

## Complexity Tracking

> No Constitution violations — intentionally empty.
