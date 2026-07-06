# Quickstart: Validate Python 3.11+ Support

This guide proves the feature end-to-end: the tool installs, type-checks, and passes its
full quality gate on the new floor (3.11) and unchanged on the ceiling (3.14).

## Prerequisites

- `uv` installed
- `just` installed
- Network access for uv to fetch interpreters and wheels

## 1. Confirm the declared floor

```bash
grep 'requires-python' pyproject.toml          # → requires-python = ">=3.11"
grep -A6 'classifiers' pyproject.toml           # → lists 3.11, 3.12, 3.13, 3.14
grep 'python-version' pyproject.toml            # → [tool.ty] python-version = "3.11"
```

**Expected**: floor is `>=3.11`; classifiers advertise all four versions; ty targets 3.11.

## 2. Lock re-solves under the new floor

```bash
uv lock --check       # passes if uv.lock is already consistent with pyproject
```

**Expected**: no error. (If it reports drift, run `uv lock` and commit the result.)

## 3. Full gate passes on the floor (Python 3.11)

```bash
uv python install 3.11
uv sync --dev --python 3.11
uv run --python 3.11 ruff check .
uv run --python 3.11 ruff format --check .
uv run --python 3.11 ty check
uv run --python 3.11 pytest
```

**Expected**: install succeeds (no "requires Python >=3.14" error — SC-001), and lint,
format, type check, and tests all pass on 3.11 (SC-002). No `SyntaxError`/`ImportError`.

## 4. Behavior unchanged on the ceiling (Python 3.14)

```bash
uv run --python 3.14 pytest      # same suite, same results as before this change (SC-004)
```

**Expected**: identical pass result to pre-change 3.14 runs (FR-006 — no behavioral drift).

## 5. CI matrix (verified on PR)

Open the pull request and confirm the `check` job runs once per version in
`[3.11, 3.12, 3.13, 3.14]` and all pass; the `zizmor` audit stays green (SC-002, FR-004).

## Mapping to requirements

| Step | Validates |
|------|-----------|
| 1    | FR-001, FR-002, FR-003, SC-003 |
| 2    | FR-007 (dep resolvability on the floor) |
| 3    | FR-005, SC-001, SC-002 |
| 4    | FR-006, SC-004 |
| 5    | FR-004, SC-002 (each supported version verified in CI) |
