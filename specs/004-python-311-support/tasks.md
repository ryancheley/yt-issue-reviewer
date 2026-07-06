# Tasks: Support Python 3.11+

**Feature**: `004-python-311-support` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Input**: plan.md, spec.md, research.md, quickstart.md

**Tests**: No new test tasks — the existing `pytest` suite is the compatibility check; the
feature's job is to run that unchanged suite on every supported version (FR-004/FR-005).

## Format

`- [ ] [ID] [P?] [Story?] Description with file path` — `[P]` = parallelizable (different
file, no incomplete dependency).

---

## Phase 1: Setup

- [X] T001 Confirm the `src/` audit from research R1: run `grep -rnE 'tomllib|from __future__|^\s*type [A-Z]|def [a-zA-Z_]+\[|class [a-zA-Z_]+\[|batched|match ' src/` and verify no Python 3.12+/3.14-only syntax or stdlib usage remains that would break on 3.11. Record the result; expect zero required changes to `src/`.

---

## Phase 2: Foundational (blocks both user stories)

**These establish the new floor; US1 and US2 both depend on them.**

- [X] T002 In `pyproject.toml`: change `requires-python = ">=3.14"` → `">=3.11"` (line ~6).
- [X] T003 In `pyproject.toml`: add trove classifiers `Programming Language :: Python :: 3.11`, `:: 3.12`, `:: 3.13` alongside the existing `:: 3.14` (classifiers list ~line 11-18), keeping them in ascending order.
- [X] T004 In `pyproject.toml`: change `[tool.ty]` `python-version = "3.14"` → `"3.11"` (line ~65) so ty validates against the floor.
- [X] T005 Regenerate the lock: run `uv lock` so `uv.lock` re-solves across 3.11–3.14 (picks a 3.11-compatible numpy per research R2/R3). Verify with `uv lock --check`.
- [X] T006 Amend `.specify/memory/constitution.md`: change "targets Python 3.12+" (Principle VI) and "Python 3.12 or newer" (Technology and Dependency Constraints) → "3.11 or newer"; bump `**Version**: 1.0.0` → `1.1.0`, set `Last Amended` to 2026-07-06, and add a Sync Impact Report note (MINOR: loosened Python floor 3.12→3.11).

**Checkpoint**: Floor is lowered everywhere the project declares it; lock is consistent.

---

## Phase 3: User Story 1 — Install and run on Python 3.11 (Priority: P1) 🎯 MVP

**Goal**: The tool installs and runs identically on Python 3.11 (and 3.12/3.13).

**Independent Test**: On a 3.11 interpreter, install and run the full gate — no version error, no `SyntaxError`/`ImportError`, tests pass (quickstart §3).

- [X] T007 [US1] Install and sync on the floor: `uv python install 3.11 && uv sync --dev --python 3.11`. Confirm install succeeds with no "requires Python >=3.14" resolution error (SC-001, FR-001/FR-007).
- [X] T008 [P] [US1] Type check on the floor: `uv run --python 3.11 ty check` passes (FR-003/FR-005).
- [X] T009 [P] [US1] Lint + format check on the floor: `uv run --python 3.11 ruff check .` and `uv run --python 3.11 ruff format --check .` pass.
- [X] T010 [P] [US1] Tests on the floor: `uv run --python 3.11 pytest` passes with no runtime version failure (FR-005, SC-002).
- [X] T011 [US1] Behavior-unchanged check on the ceiling: `uv run --python 3.14 pytest` still passes identically (FR-006, SC-004).

**Checkpoint**: US1 done — tool verifiably works on 3.11 and is unchanged on 3.14. Shippable MVP.

---

## Phase 4: User Story 2 — Every supported version verified in CI (Priority: P1)

**Goal**: CI runs the full quality gate once per version (3.11–3.14); all must pass to merge.

**Independent Test**: Open the PR; the `check` job fans out over four versions and all pass; `zizmor` stays green (quickstart §5).

- [X] T012 [US2] In `.github/workflows/ci.yml`: add `strategy: { fail-fast: false, matrix: { python-version: ["3.11", "3.12", "3.13", "3.14"] } }` to the `check` job and change the setup step to `uv python install ${{ matrix.python-version }}`. Leave the `zizmor` job single-run. Keep all actions hash-pinned and permissions least-privilege (no new grants) so the zizmor audit stays green.
- [X] T013 [US2] Validate the workflow locally: run `just security` (`uvx zizmor@1.26.1 ... .github/workflows/`) and confirm the edited `ci.yml` produces no new findings (FR-004 stays within the hardened posture).

**Checkpoint**: US2 done — the compatibility promise is enforced on every push/PR.

---

## Phase 5: Polish & Cross-Cutting

- [X] T014 [P] Update user-facing docs that state a Python version: `grep -rn '3\.14\|3\.12+' README.md CONTRIBUTING.md docs/ 2>/dev/null` and change any "requires Python 3.14" language to "Python 3.11+" (FR-002/SC-003). Skip files with no version claim.
- [X] T015 Run the full gate on the active interpreter: `just check` (lint, format-check, typecheck, test, security) — all green before pushing.
- [X] T016 Walk quickstart.md end-to-end (§1–§4) to confirm every requirement→step mapping holds; fix any gap before opening the PR.

---

## Dependencies & Execution Order

- **Phase 1 (T001)** → informs whether any `src/` fix is needed (expected: none).
- **Phase 2 (T002–T006)** → blocks everything; the floor must be lowered first. T002–T004 touch the same file (`pyproject.toml`), so run sequentially; T005 (lock) depends on T002; T006 (constitution) is independent and may run in parallel with T002–T005.
- **Phase 3 (US1)** depends on Phase 2. T008/T009/T010 are `[P]` (independent commands after T007 syncs).
- **Phase 4 (US2)** depends on Phase 2 (floor lowered) but is independent of Phase 3 — the CI edit doesn't need the local validation done first. Can proceed in parallel with Phase 3.
- **Phase 5** depends on Phases 3 and 4.

## Parallel Opportunities

- Phase 2: T006 (constitution) ∥ T002–T005 (pyproject/lock).
- Phase 3: T008 ∥ T009 ∥ T010 after T007.
- Phases 3 and 4 can run concurrently once Phase 2 is complete.

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1)**: the tool provably installs and runs on 3.11
with output unchanged on 3.14. Phase 4 (US2) makes the guarantee durable in CI; Phase 5
squares away docs and the final gate. Ship US1 first if splitting; US2 should land in the
same PR so the matrix guards the change from the moment it merges.

## Task Summary

- **Total**: 16 tasks
- **US1 (install/run on 3.11)**: 5 tasks (T007–T011)
- **US2 (CI matrix)**: 2 tasks (T012–T013)
- **Setup/Foundational/Polish**: 9 tasks (T001–T006, T014–T016)
- **Expected `src/` changes**: 0 (T001 confirms)
