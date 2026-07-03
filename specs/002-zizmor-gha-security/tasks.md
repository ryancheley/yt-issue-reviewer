---

description: "Task list for zizmor GHA Security Auditing implementation"
---

# Tasks: zizmor GitHub Actions Security Auditing

**Input**: Design documents from `/specs/002-zizmor-gha-security/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This is a CI/infrastructure feature. "Tests" are audit runs and a negative test
(deliberate finding proves the gate fails) rather than unit tests — included as validation
tasks per the spec's success criteria. No application code or `pyproject.toml` changes.

**Organization**: Sequenced so the workflow is hardened and proven clean **before** the gate
is enforced, then the dedicated `zizmor` job is added and made a required check. Tasks carry
`[US#]` labels: US1 (gate blocks insecure changes), US2 (existing workflows clean +
least-privilege), US3 (transparent, tunable policy).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- Exact file paths included in every task.

## Path Conventions

Infrastructure feature. Files touched: `.github/workflows/ci.yml`, optionally `zizmor.yml`
(repo root). No `src/` or `tests/` changes.

---

## Phase 1: Setup

**Purpose**: Establish the audit tool and pinned version before touching the workflow.

- [X] T001 Verify the audit runs via `uvx zizmor@1.26.1 --version` (confirms no new runtime / no project dependency needed); record the pinned version to use in CI
- [X] T002 Capture the current baseline by running `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/` and noting the findings (expect `unpinned-uses`, `excessive-permissions`, `artipacked`) to confirm the remediation targets

**Checkpoint**: zizmor runs locally; the pre-remediation findings are known.

---

## Phase 2: Foundational

**Purpose**: Gather the concrete data the hardening needs. Blocks the hardening tasks.

- [X] T003 Resolve the current full commit SHA for each action tag used in `.github/workflows/ci.yml` — `actions/checkout` (currently `@v5`) and `astral-sh/setup-uv` (currently `@v6`) — via `gh api repos/<owner>/<repo>/commits/<tag> --jq .sha` (e.g. `gh api repos/actions/checkout/commits/v5 --jq .sha`); record each `sha # vTag` pair for pinning

**Checkpoint**: Exact SHAs in hand for hash-pinning.

---

## Phase 3: User Story 2 — Existing workflows pass cleanly (Priority: P1) 🎯 MVP

**Goal**: Harden `ci.yml` so the audit baseline is clean at `--min-severity medium` with no
suppressions, and every job declares least-privilege permissions.

**Independent Test**: `uvx zizmor@1.26.1 --offline --min-severity medium .github/workflows/`
exits 0; each job in `ci.yml` has an explicit `permissions` block.

### Implementation for User Story 2

- [X] T004 [US2] Add top-level `permissions: {}` to `.github/workflows/ci.yml` (deny-all default)
- [X] T005 [US2] Add explicit `permissions: { contents: read }` to the existing `check` job in `.github/workflows/ci.yml` (keep the job name/context `check` — branch protection depends on it)
- [X] T006 [US2] Pin `actions/checkout` and `astral-sh/setup-uv` to their full commit SHAs (from T003) with trailing `# vX` version comments in `.github/workflows/ci.yml` (satisfies `unpinned-uses`)
- [X] T007 [US2] Add `with: { persist-credentials: false }` to the `actions/checkout` step in `.github/workflows/ci.yml` (satisfies `artipacked`)
- [X] T008 [US2] Re-run `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/` and confirm exit 0 (clean baseline). If any finding remains, remediate at the root cause; only if truly unavoidable add a justified suppression to a new `zizmor.yml` (or inline `# zizmor: ignore[<rule>] <justification>`) per contracts/ci-audit.md
- [X] T009 [US2] Confirm no application code and no `pyproject.toml` dependency changed (git diff scope is limited to `.github/` and, if created, `zizmor.yml`)

**Checkpoint**: Existing workflow is clean and least-privilege — the gate can now be enforced safely.

---

## Phase 4: User Story 1 — Insecure workflow changes are blocked (Priority: P1)

**Goal**: Add the dedicated `zizmor` CI job that audits `.github/workflows/` on every PR and
push to `main`, and make it a required status check so failures block merge.

**Independent Test**: The `zizmor` job appears on PRs and pushes; a medium+ finding makes it
exit non-zero; branch protection lists `zizmor` as required.

### Implementation for User Story 1

- [X] T010 [US1] Add a `zizmor` job to `.github/workflows/ci.yml` with `permissions: { contents: read }`, checkout pinned + `persist-credentials: false`, and a gating step `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium --format github .github/workflows/` (do NOT use `--format sarif` for the gating step — SARIF always exits 0, per research R2)
- [X] T011 [US1] Verify the `zizmor` job triggers on both `pull_request` and `push` to `main` (matches the existing `check` triggers) so the audit runs automatically with no manual step
- [X] T012 [US1] Push the branch, open the PR, and confirm both `check` and `zizmor` checks run and pass green on the hardened baseline
- [X] T013 [US1] Update branch protection on `main` to require both status checks — set required contexts to `["check", "zizmor"]` via `gh api -X PUT repos/ryancheley/yt-issue-reviewer/branches/main/protection` (strict). **Implication**: until this lands, a failing audit would not block merge; after it, every PR must pass `zizmor`. Keep `enforce_admins` and existing PR settings unchanged

**Checkpoint**: The audit is a required, automatic gate on all workflow changes.

---

## Phase 5: User Story 3 — Transparent, tunable policy (Priority: P3)

**Goal**: Make the severity threshold and any suppressions explicit and reviewable.

**Independent Test**: The threshold is visible in `ci.yml`; any suppression carries a written
justification.

### Implementation for User Story 3

- [X] T014 [US3] Ensure the threshold and persona are explicit and commented in the `zizmor` job in `.github/workflows/ci.yml` (`--min-severity medium`, `--persona regular`), with a short note that the threshold can be tightened later
- [X] T015 [US3] If a `zizmor.yml` was created in T008, confirm every `ignore`/suppression entry has an adjacent written justification; if none was needed, confirm no `zizmor.yml` exists (no empty/unjustified config)

**Checkpoint**: Policy is explicit and auditable.

---

## Phase 6: Validation & Polish

**Purpose**: Prove the gate actually fails on an insecure change, and finish the paperwork.

- [X] T016 [US1] Negative test: on a scratch commit, add an unsafe step to a workflow (e.g. `run: echo "${{ github.event.pull_request.title }}"`), run `uvx zizmor@1.26.1 --offline --min-severity medium .github/workflows/`, and confirm a `template-injection` finding with a non-zero exit; then **revert** the change and confirm exit 0 (SC-001)
- [X] T017 Run through `quickstart.md` validation scenarios (clean baseline, automatic triggers, required-check presence, tool-failure-is-not-a-silent-pass) and confirm each
- [X] T018 [P] Close issue #2 by referencing it in the PR description (e.g. "Closes #2") and confirm the proposed-approach checkboxes there are satisfied

---

## Dependencies & Execution Order

### Phase dependencies (strict, per requested sequencing)

- **Phase 1 (Setup)** → no deps.
- **Phase 2 (Foundational: resolve SHAs)** → after Phase 1; blocks hardening.
- **Phase 3 (US2: harden + clean baseline)** → after Phase 2. MUST be clean before the gate.
- **Phase 4 (US1: add job + require check)** → after Phase 3 (never enforce a red gate).
- **Phase 5 (US3: policy transparency)** → after Phase 4.
- **Phase 6 (Validation)** → last.

### User-story traceability

- **US2** (P1, MVP): T004–T009 — hardening + clean baseline.
- **US1** (P1): T010–T013, T016 — the automatic, required gate.
- **US3** (P3): T014–T015 — explicit, tunable policy.

### Within phases

- T003 (SHAs) precedes T006 (pinning).
- T008 (clean baseline) gates entry to Phase 4.
- T012 (checks green) precedes T013 (make `zizmor` required) — don't require a check that
  hasn't proven green.

---

## Parallel Opportunities

Limited — most tasks edit the single file `.github/workflows/ci.yml` and are sequential.
Independent:

- T003 (SHA lookups for the two actions) can be done together.
- T018 (issue paperwork) is independent of the workflow edits.

---

## Implementation Strategy

### MVP scope

**US2 (Phase 3)** is the MVP foundation — a hardened, least-privilege, audit-clean workflow.
**US1 (Phase 4)** then makes the audit an automatic required gate (the feature's core value).
US3 is a small transparency refinement.

### Incremental delivery

1. Phases 1–2 → tool confirmed, SHAs resolved.
2. Phase 3 → `ci.yml` hardened, local audit clean (MVP baseline).
3. Phase 4 → `zizmor` job added, checks green, made a required check.
4. Phase 5 → policy explicit.
5. Phase 6 → negative test + quickstart validation, close #2.

---

## Notes

- zizmor runs via `uvx zizmor@1.26.1` — no new runtime, no `pyproject.toml` dependency
  (Constitution VI).
- The gating step must not use `--format sarif` (it exits 0 even with findings).
- Keep the `check` job's context name unchanged (branch-protection dependency).
- Do not suppress findings unless a real one is unavoidable, and always with a written
  justification (Constitution IV / FR-010).
- This repo requires a feature branch + green CI before merge — already on
  `002-zizmor-gha-security`.
