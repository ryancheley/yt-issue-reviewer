# Phase 0 Research: Developer Infrastructure & Release Readiness

Resolves the technical unknowns for the four bundled items. Grounded in the yt-cli
reference (`ryancheley/yt-cli`), current tool docs, and the repo's own #2 hardening.

## R1. Dependabot for uv + GitHub Actions

**Decision**: `.github/dependabot.yml` v2 with two ecosystems — `package-ecosystem: "uv"`
and `package-ecosystem: "github-actions"`, both `directory: "/"`, `schedule.interval:
monthly`, each with a `groups:` block (`patterns: ["*"]`) to produce one grouped PR per
ecosystem.

**Rationale**: Dependabot's native `uv` support (GA 2025-03) reads `pyproject.toml` +
`uv.lock` directly. Grouping minimizes PR noise. Crucially, Dependabot updates
hash-pinned `uses:` to the new SHA **and rewrites the `# vX.Y.Z` comment**, so the
supply-chain-safe pinning added in #2 stays current without manual work. No secret is
required.

**Alternatives considered**: `package-ecosystem: "pip"` — wrong for a uv-lockfile project;
`uv` is the correct native ecosystem. Weekly/daily cadence — noisier than the agreed
monthly default.

## R2. Release workflow — build & publish

**Decision**: `on: push: tags: ['v*']`. Two jobs, each `checkout` (pinned,
`persist-credentials: false`) + `astral-sh/setup-uv` (pinned) + `uv build`, then publish
with `pypa/gh-action-pypi-publish` (pinned):
- `testpypi`: `environment: testpypi`, `permissions: { id-token: write, contents: read }`,
  publish with `repository-url: https://test.pypi.org/legacy/` and `skip-existing: true`.
- `pypi`: `needs: testpypi`, `environment: pypi`,
  `permissions: { id-token: write, contents: write }`, publish to PyPI, then
  `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --generate-notes`
  (`env: GH_TOKEN: ${{ github.token }}`).

**Rationale**: Mirrors yt-cli's proven pattern. `uv build` produces sdist+wheel; the PyPA
action is the battle-tested uploader and supports OIDC. Building in each job avoids
artifact-passing actions (fewer pins). `contents: write` on the `pypi` job is only for
creating the GitHub Release. TestPyPI first catches metadata/upload problems before the
irreversible real publish; `skip-existing` tolerates a re-run where the TestPyPI version
already exists.

**Pinned actions** (SHAs resolved at plan time):
- `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5.0.1`
- `astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e # v6.8.0`
- `pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b # v1.14.0`

**Alternatives considered**:
- `uv publish --trusted-publishing always` — works, but the PyPA action is more widely
  used and documented for OIDC; either is fine, chose the action to match yt-cli.
- Build-once + upload/download-artifact — cleaner but needs two more pinned actions;
  rejected for simplicity (Constitution VI), building twice is cheap.

## R3. Trusted Publishing (OIDC) — no stored token

**Decision**: Use PyPI/TestPyPI **Trusted Publishing** via GitHub Environments (`pypi`,
`testpypi`) and `id-token: write`. No `PYPI_API_TOKEN` secret.

**Rationale**: No long-lived credential to store or leak — aligns with the project's
least-privilege / no-standing-credentials posture. The GitHub Environment also provides an
optional approval gate for the real publish.

**Manual prerequisite (documented, not automated)**: On PyPI and TestPyPI, add a *pending*
Trusted Publisher pointing at owner `ryancheley`, repo `yt-issue-reviewer`, workflow file
`release.yml`, and environment name (`pypi` / `testpypi`). This one-time account setup and
the actual `v*` tag push are **maintainer actions** — out of scope for automated execution
(publishing is outward-facing and irreversible). `docs/releasing.md` documents the steps.

## R4. pyproject metadata for a clean PyPI page

**Decision**: Add to `[project]`: `license = "MIT"` (SPDX expression) + a `LICENSE` file;
`keywords`; `classifiers` (Development Status :: 3 - Alpha, Environment :: Console,
Intended Audience :: Developers, License :: OSI Approved :: MIT License, Programming
Language :: Python :: 3.14, Topic :: Software Development :: Bug Tracking); and
`[project.urls]` (Homepage, Repository, Issues → the GitHub repo).

**Rationale**: Complete metadata yields a professional PyPI page and correct categorization
(FR-022). MIT matches the intended license; a `LICENSE` file is required for a proper
distribution. `description` and `readme` already exist.

**Version handling**: Keep static `version = "0.1.0"`; release by bumping it and pushing a
matching `vX.Y.Z` tag (as yt-cli does). Dynamic-version-from-tag (hatch-vcs / uv dynamic
versioning) is noted as a **future option**, not adopted now (simplicity).

**Note**: Use SPDX string `license = "MIT"` (modern) with hatchling; ensure the installed
hatchling supports PEP 639 SPDX license expressions (it does in current versions). Fallback
if needed: `license = { text = "MIT" }` + a license classifier.

## R5. Documentation set

**Decision**: Markdown only — expand `README.md`, add `CONTRIBUTING.md`, and a `docs/`
folder: `installation.md`, `quickstart.md`, `cli-reference.md`, `configuration.md`,
`architecture.md`, `privacy-and-security.md`, `releasing.md`. Deep detail **links** to the
existing spec artifacts (`specs/001-related-issue-finder/…`, constitution) rather than
duplicating them.

**Rationale**: Markdown-in-repo is sufficient and lowest-maintenance (Constitution VI); a
hosted site is optional/out of scope. Sourcing the CLI reference from
`contracts/cli.md` and config from `src/yt_issue_reviewer/config.py` keeps docs accurate.

**Content sources**:
- Commands/flags/exit codes → `specs/001-related-issue-finder/contracts/cli.md`.
- Config defaults → `src/yt_issue_reviewer/config.py` (`Config`: db_path `yir.db`,
  ollama_host `http://127.0.0.1:11434`, embedding_model `nomic-embed-text`, label_model
  `qwen2.5`, weight_semantic `0.7`, weight_structural `0.3`, min_score `0.6`,
  temporal_window_days `7`) + env vars `OLLAMA_HOST`, `YIR_DB`, `YIR_CONFIG`.
- Architecture → `specs/001-related-issue-finder/{plan,data-model}.md`.
- Privacy/degraded mode → `.specify/memory/constitution.md` + pipeline behavior.

**Alternatives considered**: MkDocs Material site (like yt-cli's Read the Docs) — deferred
as optional; can pair with the release later.

## R6. justfile

**Decision**: A root `justfile` with `default` (`just --list`), `install`, `lint`,
`lint-fix`, `format`, `format-check`, `typecheck`, `security`, `test *args`, `run *args`,
`doctor`, `clean`, `deps-update`, and an aggregate `check` = `lint format-check typecheck
test security`, plus `fix` = `lint-fix format`. `security` runs `uvx zizmor@1.26.1
--offline --persona regular --min-severity medium .github/workflows/` (no project dep).

**Rationale**: `check` reproduces the exact CI gate (the `check` job's ruff/ruff
format/ty/pytest **and** the `zizmor` job) so contributors get local == CI (FR-009,
SC-003). Running zizmor via `uvx` matches #2 and adds no dependency (FR-012). `just` 1.42
is available locally to validate.

**Drift guard**: The `check` recipe and `ci.yml` must stay in lock-step; `docs`/CONTRIBUTING
note that changing one requires changing the other. (A future enhancement could have CI
literally call `just check`, but keeping them parallel avoids requiring `just` on the
runner.)

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Dependabot ecosystems | `uv` + `github-actions`, monthly, grouped |
| Release trigger/build | `v*` tag → `uv build` in each of 2 jobs |
| Publish auth | Trusted Publishing (OIDC), GitHub Environments, no token |
| Publish safety | TestPyPI (`skip-existing`) → PyPI; GitHub Release with `--generate-notes` |
| Pinned actions | checkout v5.0.1, setup-uv v6.8.0, gh-action-pypi-publish v1.14.0 (SHAs above) |
| Metadata | MIT + LICENSE, classifiers, urls, keywords; static version |
| Docs | Markdown (README + CONTRIBUTING + docs/), link specs |
| justfile | recipes incl. `check` == CI gate; zizmor via uvx |
| Out of scope | real publish, tag push, PyPI trusted-publisher account setup (maintainer) |
