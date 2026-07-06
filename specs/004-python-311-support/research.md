# Phase 0 Research: Support Python 3.11+

## R1: Is `src/` free of 3.12+/3.14-only syntax and stdlib usage?

**Decision**: Yes — no source changes required; the audit is confirmatory.

**Rationale**: Grep audit of `src/yt_issue_reviewer/`:
- `from __future__ import annotations` in every module → all annotations are strings, so
  newer typing syntax in annotations wouldn't execute on 3.11 anyway.
- `tomllib` (config.py) → standard library since Python 3.11. Safe at the 3.11 floor.
- No PEP 695 `type X = ...` aliases, no PEP 695 generic syntax (`def f[T]`, `class C[T]`).
- No `match`/`case` (would be fine on 3.10+ regardless).
- No `itertools.batched` (3.12) or other version-gated stdlib symbols found.

**Alternatives considered**: Add `from __future__` guards or `sys.version_info` branches —
unnecessary since nothing version-gated is used. Floor of 3.10/3.9 — rejected: `tomllib`
requires 3.11 and issue #19 specifies 3.11.

## R2: Do all runtime dependencies support Python 3.11?

**Decision**: Yes. The floor is not blocked by any dependency.

**Rationale**: Requires-Python of declared deps:
- `youtrack-cli` → `>=3.10,<3.16` ✅ (its transitive deps: pydantic, httpx, textual, etc. all support 3.11)
- `click` → `>=3.10` ✅ (Requires-Python reported as generic; click 8.x supports 3.8+)
- `rich` → `>=3.9` ✅
- `ollama` → `>=3.8` ✅
- `numpy>=2.0` → resolves per-interpreter. The currently *locked* numpy reports
  `Requires-Python >=3.12`, but the `>=2.0` constraint lets uv pick a 3.11-compatible
  numpy (2.3.x supports 3.11) when solving for 3.11.

**Alternatives considered**: Pin numpy to a specific 3.11-compatible version — rejected as
premature; `>=2.0` already permits a valid universal solution. Revisit only if `uv lock` fails.

## R3: How to re-solve the lock for a multi-version floor?

**Decision**: Regenerate `uv.lock` with `uv lock` after editing `requires-python`.

**Rationale**: The existing lock was produced under `>=3.14`. uv's universal resolver
produces version-forked entries where needed (e.g. a different numpy for 3.11 vs 3.14), so a
single re-solve covers all four interpreters. Verified downstream by CI installing on 3.11.

**Alternatives considered**: Hand-edit the lock — rejected (error-prone, not reproducible).
Drop the lock entirely — rejected (loses reproducibility, Principle IV).

## R4: How should CI exercise every supported version?

**Decision**: Convert the `check` job to a `strategy.matrix` over `["3.11","3.12","3.13","3.14"]`,
parameterizing the `uv python install ${{ matrix.python-version }}` step. Keep `fail-fast: false`
so one version's failure still reports the others (supports spec acceptance scenario US2-2).
Leave the `zizmor` job as a single run (workflow-file audit is version-independent).

**Rationale**: A matrix is the standard GitHub Actions idiom for multi-version testing and
keeps the per-step gate identical to today. `fail-fast: false` gives full-matrix signal.
The change stays within the existing least-privilege + hash-pinned posture, so the zizmor
audit stays green (no new actions, no elevated permissions).

**Alternatives considered**: Four duplicated jobs — rejected (copy-paste, drifts). Only test
floor + ceiling (3.11 + 3.14) — rejected: FR-004/SC-002 require *each* supported version; the
middle versions can regress independently.

**`just check` note**: The local `check` recipe stays single-version (it runs on the
developer's active interpreter). CI is what fans out across versions; the recipe body (lint,
format-check, typecheck, test, security) is unchanged, honoring "just check == the CI gate"
per-version. The zizmor step remains part of the recipe but is not matrixed in CI.

## R5: Resolving the constitution's "Python 3.12+" statements

**Decision**: Amend the constitution — Principle VI ("targets Python 3.12+") and the
Technology Constraints bullet ("Python 3.12 or newer") → "3.11 or newer" — and bump the
constitution version 1.0.0 → 1.1.0 with a Sync Impact note.

**Rationale**: Governance says the principle wins on conflict, so shipping 3.11 support while
the constitution says 3.12+ would be a standing violation. The constitution's own amendment
process is the correct channel. Loosening a stated constraint is a MINOR bump (no principle
removed/redefined; non-negotiable I/II untouched).

**Alternatives considered**: Ignore the mismatch — rejected (constitution is a gate). Run a
full `/speckit-constitution` interactive session — rejected as heavyweight for a two-line
wording loosening; done inline as an in-scope task and re-checked in the plan gate.
