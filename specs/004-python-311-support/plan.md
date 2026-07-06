# Implementation Plan: Support Python 3.11+

**Branch**: `004-python-311-support` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-python-311-support/spec.md`

## Summary

Lower the project's Python floor from `>=3.14` to `>=3.11` so the tool installs and runs
on the four current interpreters (3.11–3.14). This is packaging + CI + governance work,
not source refactoring: a preliminary audit shows `src/` already avoids 3.12+/3.14-only
language features (`from __future__ import annotations` everywhere, `tomllib` which is
stdlib since 3.11, no PEP 695 aliases/generics, no `match`, no `itertools.batched`).

Technical approach:
1. Set `requires-python = ">=3.11"`, add trove classifiers for 3.11/3.12/3.13, and set the
   `ty` target to `python-version = "3.11"` in `pyproject.toml`.
2. Regenerate `uv.lock` under the new floor (the current lock resolved under `>=3.14` and
   pins a `numpy` that requires `>=3.12`; a universal lock across 3.11–3.14 must be re-solved).
3. Convert the single-version CI `check` job to a `matrix` over 3.11/3.12/3.13/3.14, running
   the existing quality gate on each; keep the `zizmor` job single-run.
4. Amend the constitution's "Python 3.12+" references to "3.11+" so governance and code agree.
5. Confirm the `src/` audit (no code changes expected) and validate the full gate on the floor.

## Technical Context

**Language/Version**: Python 3.11 (new floor) through 3.14 (current) — universal support target

**Primary Dependencies**: click>=8.1, rich>=13.7, numpy>=2.0, ollama>=0.6, youtrack-cli>=0.24.0. All support 3.11 (youtrack-cli is `>=3.10,<3.16`; numpy resolves per-interpreter to a 3.11-compatible build).

**Storage**: SQLite (local cache) — unaffected

**Testing**: pytest (existing suite); ruff + ty as part of the gate

**Target Platform**: Any OS with CPython 3.11–3.14 (dev on macOS, CI on ubuntu-latest)

**Project Type**: Single-project Python CLI (packaging/CI change; no `src/` structure change)

**Performance Goals**: N/A (no runtime behavior change; FR-006 forbids behavioral drift)

**Constraints**: Change is additive-compatibility only — must not alter output on 3.14. Lock must resolve across all four versions. All new/modified workflow YAML must keep the zizmor audit green (least-privilege, hash-pinned actions).

**Scale/Scope**: 3 files edited (`pyproject.toml`, `.github/workflows/ci.yml`, constitution), 1 regenerated (`uv.lock`), 0 expected `src/` changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries (NON-NEGOTIABLE)**: ✅ Unaffected. No inference/embedding path changes; no issue content moves anywhere new.
- **II. Read-Only by Default**: ✅ Unaffected. No YouTrack write paths touched.
- **III. Build on yt-cli**: ✅ Unaffected. `youtrack_cli` remains the only client; it supports 3.11.
- **IV. Reproducibility/Transparency**: ✅ Unaffected. Scoring/evidence untouched. FR-006 guarantees identical output across versions.
- **V. Local-First Data**: ✅ Unaffected. SQLite cache unchanged.
- **VI. Simplicity**: ✅ Reinforced — no new dependencies, no new layers; smaller barrier to install. **⚠️ Wording conflict**: this principle and the Technology Constraints section both state "Python 3.12+". Lowering the floor to 3.11 requires amending those two references (see Complexity Tracking). This is a deliberate governance update, not a violation — 3.11+ is a superset and the amendment is the correct resolution channel per the constitution's own Governance section.
- **VII. Test-First**: ✅ Reinforced — the CI matrix runs the existing offline unit tests on every supported version, strengthening the safety net. No test depends on live YouTrack/Ollama.

**Gate result**: PASS, with one required governance amendment (constitution 3.12+→3.11+) tracked below. No non-negotiable principle (I/II) is affected.

## Project Structure

### Documentation (this feature)

```text
specs/004-python-311-support/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — decisions on floor, lock, CI matrix, deps
├── quickstart.md        # Phase 1 output — how to validate 3.11 support
└── checklists/
    └── requirements.md  # Spec quality checklist (from /speckit-specify)
```

No `data-model.md` or `contracts/` are generated: this feature introduces no data entities
and changes no public interface (the CLI command surface, config schema, and output are all
unchanged — FR-006). Those artifacts would be empty ceremony here.

### Source Code (repository root)

```text
pyproject.toml            # EDIT: requires-python, classifiers, [tool.ty] python-version
uv.lock                   # REGENERATE: re-solve under >=3.11
.github/workflows/ci.yml  # EDIT: check job → matrix over 3.11–3.14
.specify/memory/constitution.md  # EDIT: 3.12+ → 3.11+ (2 references), version bump

src/yt_issue_reviewer/    # AUDIT ONLY — no changes expected
tests/                    # unchanged (run unchanged on every matrix version)
```

**Structure Decision**: Single-project Python CLI, unchanged. This is a metadata/CI/governance
change layered on the existing layout; no directories are added or moved.

## Complexity Tracking

| Item | Why Needed | Note |
|------|------------|------|
| Amend constitution "3.12+" → "3.11+" (Principle VI + Technology Constraints), bump 1.0.0 → 1.1.0 | The feature's entire purpose (issue #19) is to support 3.11; leaving the constitution at 3.12+ would make governance contradict shipped reality. | MINOR bump (materially loosens a stated constraint; no principle removed or redefined). Non-negotiable principles I/II untouched. Handled as an in-scope task, not a separate `/speckit-constitution` run, since it's a two-line wording change. |
| Regenerate `uv.lock` | Current lock was solved under `>=3.14` and pins a numpy requiring `>=3.12`; a 3.11 install needs a re-solved universal lock. | Mechanical (`uv lock`); verified by CI resolving/installing on 3.11. |
