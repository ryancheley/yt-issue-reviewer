# Phase 1 Data Model: Developer Infrastructure & Release Readiness

No application data. The "entities" are configuration/metadata artifacts and the doc set.
Captured for traceability to the spec's Key Entities.

## Entity: Update configuration (`.github/dependabot.yml`)

| Field | Value |
|-------|-------|
| `version` | `2` |
| update[0].`package-ecosystem` | `"uv"` |
| update[1].`package-ecosystem` | `"github-actions"` |
| each `.directory` | `"/"` |
| each `.schedule.interval` | `"monthly"` |
| each `.groups.<name>.patterns` | `["*"]` (one grouped PR per ecosystem) |

**Validation**: valid YAML; both ecosystems present; monthly; grouped; no secrets
referenced (FR-013–FR-017).

## Entity: Release automation (`.github/workflows/release.yml`)

| Field | Value |
|-------|-------|
| trigger | `push.tags: ['v*']` |
| top-level `permissions` | `{}` |
| job `testpypi` | env `testpypi`; perms `{id-token: write, contents: read}`; publish to `https://test.pypi.org/legacy/`, `skip-existing: true` |
| job `pypi` | `needs: testpypi`; env `pypi`; perms `{id-token: write, contents: write}`; publish to PyPI; then `gh release create` with `--generate-notes` |
| build | `uv build` (sdist + wheel) in each job |
| checkout | pinned SHA + `persist-credentials: false` |
| publish action | `pypa/gh-action-pypi-publish` pinned SHA |

**Validation**: valid YAML; passes `zizmor` (least-privilege, pinned); no stored token
(OIDC only) (FR-018–FR-023).

## Entity: Package metadata (`pyproject.toml` `[project]`) + `LICENSE`

| Field | Value |
|-------|-------|
| `license` | `"MIT"` (SPDX) + top-level `LICENSE` file (MIT text) |
| `keywords` | e.g. `["youtrack","issues","embeddings","cli","ollama"]` |
| `classifiers` | Dev Status 3 - Alpha; Environment :: Console; Intended Audience :: Developers; License :: OSI Approved :: MIT License; Programming Language :: Python :: 3.14; Topic :: Software Development :: Bug Tracking |
| `[project.urls]` | Homepage / Repository / Issues → `github.com/ryancheley/yt-issue-reviewer` |
| `version` | static `"0.1.0"` (manual bump + tag) |

**Validation**: `uv build` + `uvx twine check dist/*` pass; metadata complete (FR-022).

## Entity: Task runner recipe set (`justfile`)

| Recipe | Command |
|--------|---------|
| `default` | `just --list` |
| `install` | `uv sync --dev` |
| `lint` / `lint-fix` | `uv run ruff check .` / `--fix` |
| `format` / `format-check` | `uv run ruff format .` / `--check` |
| `typecheck` | `uv run ty check` |
| `security` | `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/` |
| `test *args` | `uv run pytest {{args}}` |
| `run *args` / `doctor` | `uv run yt-issue-reviewer …` |
| `clean` | remove build/cache artifacts (leave `*.db`) |
| `deps-update` | `uv sync --upgrade` |
| **`check`** | `lint format-check typecheck test security` — **== CI gate** |
| `fix` | `lint-fix format` |

**Validation**: `just check` passes on a clean tree and equals the CI gate (FR-008–FR-012,
SC-003).

## Entity: Documentation set

| Doc | Covers |
|-----|--------|
| `README.md` | overview, install summary, quickstart pointer, links |
| `docs/installation.md` | uv, youtrack-cli auth, self-hosted Ollama + models, OLLAMA_HOST/Tailscale |
| `docs/quickstart.md` | doctor → analyze → show |
| `docs/cli-reference.md` | all 6 commands, flags, exit codes |
| `docs/configuration.md` | env vars + `config.toml` with defaults |
| `docs/architecture.md` | hybrid scoring, evidence, grouping, SQLite schema |
| `docs/privacy-and-security.md` | read-only, self-hosted-only, degraded mode |
| `docs/releasing.md` | version bump + tag; one-time Trusted-Publisher setup |
| `CONTRIBUTING.md` | required checks (ruff/ty/pytest/zizmor), branch/PR workflow, constitution |

**Validation**: every command + every config setting documented; deep detail links to spec
artifacts, not duplicated (FR-001–FR-007, SC-001, SC-002).

## Cross-cutting invariant

All new automation files use `permissions: {}` + least-privilege jobs + hash-pinned
actions so the `zizmor` audit reports 0 findings ≥ threshold (FR-024, SC-007). No `src/`
change; existing tests pass unchanged (FR-025, SC-008).
