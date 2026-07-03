# Contract: justfile developer recipes

**File**: `justfile` (repo root).

## Recipes

| Recipe | Behavior |
|--------|----------|
| `default` | `just --list` (discoverability) |
| `install` | `uv sync --dev` |
| `lint` | `uv run ruff check .` |
| `lint-fix` | `uv run ruff check --fix .` |
| `format` | `uv run ruff format .` |
| `format-check` | `uv run ruff format --check .` |
| `typecheck` | `uv run ty check` |
| `security` | `uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/` |
| `test *args` | `uv run pytest {{args}}` |
| `run *args` | `uv run yt-issue-reviewer {{args}}` |
| `doctor` | `uv run yt-issue-reviewer doctor` |
| `clean` | remove `dist/ build/ .pytest_cache .ruff_cache .ty_cache **/__pycache__` (NOT `*.db`) |
| `deps-update` | `uv sync --upgrade` |
| **`check`** | `lint` + `format-check` + `typecheck` + `test` + `security` |
| `fix` | `lint-fix` + `format` |

## Guarantees

- **`check` == CI gate**: it runs exactly the same checks as `.github/workflows/ci.yml`
  (the `check` job's ruff/ruff-format/ty/pytest **and** the `zizmor` job's audit).
- `security` runs zizmor via `uvx` — no dependency added to `pyproject.toml`.
- All Python tooling goes through `uv run`.

## Verification

1. `just --list` shows all recipes.
2. `just check` exits 0 on a clean working tree.
3. Introducing a lint/format/type/test error makes `just check` fail at that step.
4. The set of checks in `check` matches `ci.yml` (manual lock-step review; documented in
   CONTRIBUTING that the two must change together).
