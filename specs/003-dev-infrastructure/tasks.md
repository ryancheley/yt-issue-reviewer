---

description: "Task list for Developer Infrastructure & Release Readiness"
---

# Tasks: Developer Infrastructure & Release Readiness

**Input**: Design documents from `/specs/003-dev-infrastructure/` (issues #3, #5, #6, #7)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Infrastructure feature — "tests" are validation runs (`just check`, `uv build` +
`twine check`, the `zizmor` audit, and the unchanged `pytest` suite). No application-code
tests are added; no `src/` changes.

**Organization**: Sequenced per the requested order — task runner first (it's the
validation harness), then Dependabot, then release + metadata, then docs, then a final
validation phase. Tasks carry `[US#]` labels: US1 docs, US2 task runner, US3 Dependabot,
US4 release.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- Exact file paths in every task.

## Path Conventions

Repo-root artifacts: `.github/dependabot.yml`, `.github/workflows/release.yml`,
`pyproject.toml`, `LICENSE`, `justfile`, `README.md`, `CONTRIBUTING.md`, `docs/*.md`.
No `src/` or `tests/` changes.

---

## Phase 1: Setup

**Purpose**: Confirm the local tooling used to build and validate everything.

- [X] T001 Confirm `just` (`just --version`, 1.42+) and `uv` are available, and record the release-workflow action SHAs from research.md R2 (checkout `93cb6ef…` v5.0.1, setup-uv `d0cc045…` v6.8.0, gh-action-pypi-publish `cef2210…` v1.14.0) for reuse

**Checkpoint**: Tooling confirmed; SHAs on hand.

---

## Phase 2: User Story 2 — Task runner mirrors CI (Priority: P1) 🎯 harness

**Goal**: A `justfile` whose `check` recipe runs exactly the CI gate, so it can validate
every other artifact in this feature.

**Independent Test**: `just --list` shows recipes; `just check` runs
lint+format-check+typecheck+test+security and exits 0 on a clean tree.

- [X] T002 [US2] Create `justfile` at repo root with recipes `default` (`just --list`), `install`, `lint`, `lint-fix`, `format`, `format-check`, `typecheck`, `security` (`uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/`), `test *args`, `run *args`, `doctor`, `clean`, `deps-update`, `fix`, and `check` = `lint format-check typecheck test security`, per contracts/justfile.md
- [X] T003 [US2] Run `just check` and confirm it exits 0 and runs the same checks as `.github/workflows/ci.yml` (ruff, ruff format --check, ty, pytest, zizmor) — local == CI (SC-003)

**Checkpoint**: `just check` is the working validation harness for the rest of the feature.

---

## Phase 3: User Story 3 — Automated dependency updates (Priority: P2)

**Goal**: Dependabot opens monthly, grouped update PRs for the uv and github-actions
ecosystems.

**Independent Test**: `.github/dependabot.yml` is valid YAML with both ecosystems, monthly,
grouped.

- [X] T004 [US3] Create `.github/dependabot.yml` (v2) with `uv` and `github-actions` ecosystems, `directory: "/"`, `schedule.interval: monthly`, and a `groups` block (`patterns: ["*"]`) per ecosystem, per contracts/dependabot.md
- [X] T005 [US3] Validate `.github/dependabot.yml` is well-formed (parses as YAML; `grep` confirms both ecosystems + monthly + groups) and requires no secrets

**Checkpoint**: Dependency-update automation configured (live behavior verified GitHub-side post-merge).

---

## Phase 4: User Story 4 — Release / publish readiness (Priority: P2)

**Goal**: A tag-driven, Trusted-Publishing release workflow that builds and (on publish)
uploads to PyPI, plus complete package metadata — all audit-clean. No real publish/tag here.

**Independent Test**: `uv build` + `uvx twine check dist/*` pass; `zizmor` audit of
`.github/workflows/` (incl. the new `release.yml`) is clean.

- [X] T006 [US4] Add PyPI metadata to `pyproject.toml` `[project]`: `license = "MIT"`, `keywords`, `classifiers` (Dev Status 3 - Alpha, Environment :: Console, Intended Audience :: Developers, License :: OSI Approved :: MIT License, Programming Language :: Python :: 3.14, Topic :: Software Development :: Bug Tracking), and `[project.urls]` (Homepage/Repository/Issues → github.com/ryancheley/yt-issue-reviewer), per contracts/release.md
- [X] T007 [P] [US4] Add a top-level `LICENSE` file with the MIT license text (© Ryan Cheley)
- [X] T008 [US4] Create `.github/workflows/release.yml`: trigger `push.tags: ['v*']`, top-level `permissions: {}`; job `testpypi` (env `testpypi`, `id-token: write`+`contents: read`, checkout pinned + `persist-credentials: false`, setup-uv pinned, `uv build`, `pypa/gh-action-pypi-publish` pinned with TestPyPI `repository-url` + `skip-existing: true`); job `pypi` (`needs: testpypi`, env `pypi`, `id-token: write`+`contents: write`, same build, publish to PyPI, then `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --generate-notes` with `GH_TOKEN`), using the SHAs from T001, per contracts/release.md
- [X] T009 [US4] Validate build + metadata: `uv build` produces a wheel + sdist in `dist/`, and `uvx twine check dist/*` reports PASS (SC-006)
- [X] T010 [US4] Run `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/` and confirm exit 0 — both `ci.yml` and the new `release.yml` are audit-clean (least-privilege, hash-pinned) (SC-007)

**Checkpoint**: Release automation is present, builds valid artifacts, and passes the audit; real publish remains a documented maintainer action.

---

## Phase 5: User Story 1 — Documentation (Priority: P1)

**Goal**: A user can install, configure, and run the tool from docs; a contributor knows
the workflow. Docs come after the other artifacts so they can describe them accurately.

**Independent Test**: every CLI command and every config setting is documented; CONTRIBUTING
lists the required checks; docs link to spec artifacts.

- [X] T011 [P] [US1] Write `docs/installation.md` (uv; `youtrack-cli` auth; self-hosted Ollama + models `nomic-embed-text` / optional chat model; `OLLAMA_HOST` / Tailscale)
- [X] T012 [P] [US1] Write `docs/quickstart.md` (doctor → analyze → show), adapting `specs/001-related-issue-finder/quickstart.md`
- [X] T013 [P] [US1] Write `docs/cli-reference.md` documenting all 6 commands (`doctor`, `ingest`, `embed`, `analyze`, `show`, `runs`), flags, and exit codes — source: `specs/001-related-issue-finder/contracts/cli.md`
- [X] T014 [P] [US1] Write `docs/configuration.md` covering every setting in `src/yt_issue_reviewer/config.py` (db_path, ollama_host, embedding_model, label_model, weight_semantic, weight_structural, min_score, temporal_window_days) + env vars (`OLLAMA_HOST`, `YIR_DB`, `YIR_CONFIG`) with defaults
- [X] T015 [P] [US1] Write `docs/architecture.md` (hybrid semantic + structural scoring, evidence, union-find grouping, Datasette-friendly SQLite) linking `specs/001-related-issue-finder/data-model.md`
- [X] T016 [P] [US1] Write `docs/privacy-and-security.md` (read-only YouTrack, self-hosted Ollama only, no third-party hosted AI, degraded-mode) linking `.specify/memory/constitution.md`
- [X] T017 [P] [US1] Write `docs/releasing.md` (version bump + `vX.Y.Z` tag; the one-time PyPI/TestPyPI Trusted Publisher setup: owner/repo `release.yml`, environments `pypi`/`testpypi`)
- [X] T018 [US1] Write `CONTRIBUTING.md` (required checks: `just check` == ruff/ruff format/ty/pytest/zizmor; feature-branch + PR workflow; branch protection; link the constitution) and note that the justfile `check` recipe and `ci.yml` must change together
- [X] T019 [US1] Expand `README.md` (overview, privacy posture, install summary, quickstart pointer, links to `docs/` and to the `just` recipes; note `just` install)

**Checkpoint**: Documentation complete and accurate to the shipped artifacts.

---

## Phase 6: Validation & Polish

**Purpose**: Prove the whole bundle with the harness; confirm no app change; close issues.

- [X] T020 Run `just check` and confirm exit 0 (== CI gate: ruff, ruff format, ty, pytest, zizmor across both workflows)
- [X] T021 Confirm no application change: `git diff --name-only main..HEAD | grep '^src/'` returns nothing, and `uv run pytest -q` passes unchanged (SC-008)
- [X] T022 Run `quickstart.md` validation scenarios (task runner, dependabot shape, release build + twine check + audit, docs coverage) and confirm each
- [X] T023 [P] Open the PR referencing all four issues ("Closes #3", "Closes #5", "Closes #6", "Closes #7") and confirm the required `check` + `zizmor` checks pass on it

---

## Dependencies & Execution Order

### Phase order (per requested sequencing)

- **Phase 1 (Setup)** → no deps.
- **Phase 2 (US2 justfile)** → first, because `just check` is the harness used to validate
  Phases 3–5.
- **Phase 3 (US3 Dependabot)** → small/independent; after the harness exists.
- **Phase 4 (US4 release + metadata)** → after Phase 3; must pass `just security`/zizmor.
- **Phase 5 (US1 docs)** → after 2–4 so docs describe the real artifacts.
- **Phase 6 (Validation)** → last.

### Story independence

- US2, US3, US4, US1 each touch distinct files and are independently testable; the ordering
  is for validation convenience (US2's harness) and doc accuracy (US1 last), not hard code
  dependencies.

### Within phases

- T001 SHAs precede T008 (release workflow).
- T006/T007 (metadata + LICENSE) precede T009 (build + twine check).
- T008 precedes T010 (audit must include the new workflow).

---

## Parallel Opportunities

- **Docs (Phase 5)**: T011–T017 are separate files → parallel; T018/T019 follow.
- **T007** (LICENSE) is independent of T006/T008.
- Dependabot (Phase 3) is independent of the release work (Phase 4) and could be done in
  parallel once the harness exists.

### Parallel example: Phase 5 docs

```bash
Task: "Write docs/installation.md"
Task: "Write docs/cli-reference.md"
Task: "Write docs/configuration.md"
Task: "Write docs/architecture.md"
```

---

## Implementation Strategy

### MVP / increments

Each user story is a shippable increment:
1. **US2 justfile** — instant contributor value; also the validation harness.
2. **US3 Dependabot** — set-and-forget maintenance.
3. **US4 release + metadata** — makes the project publishable (real publish = maintainer).
4. **US1 docs** — adoption; written last for accuracy.

### Notes

- No `src/`/analysis changes (FR-025). zizmor runs via `uvx` only — no `pyproject.toml`
  dependency (FR-012).
- New workflows stay least-privilege + hash-pinned so the required `zizmor` check stays
  green (FR-024).
- Do **not** publish to PyPI or push a `vX.Y.Z` tag — those are maintainer actions gated on
  the one-time Trusted Publisher setup (documented in `docs/releasing.md`).
- Already on branch `003-dev-infrastructure`; PR will close #3/#5/#6/#7.
