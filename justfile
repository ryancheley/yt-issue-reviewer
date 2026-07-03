# yt-issue-reviewer — developer task runner.
# `just check` runs EXACTLY the CI gate (see .github/workflows/ci.yml): ruff, ruff format,
# ty, pytest, and the zizmor workflow audit. Keep this recipe and ci.yml in lock-step.

# Pinned zizmor version (matches the `zizmor` CI job).
ZIZMOR_VERSION := "1.26.1"

# Show available recipes.
default:
    @just --list

# --- setup ---

# Sync the dev environment.
install:
    uv sync --dev

# --- quality (this set == the CI gate) ---

# Lint with ruff.
lint:
    uv run ruff check .

# Lint and auto-fix.
lint-fix:
    uv run ruff check --fix .

# Format with ruff.
format:
    uv run ruff format .

# Verify formatting (no changes written).
format-check:
    uv run ruff format --check .

# Type-check with ty.
typecheck:
    uv run ty check

# Audit GitHub Actions workflows with zizmor (via uvx — no project dependency).
security:
    uvx zizmor@{{ZIZMOR_VERSION}} --offline --persona regular --min-severity medium .github/workflows/

# Run the test suite (pass extra args through, e.g. `just test -k scoring`).
test *args:
    uv run pytest {{args}}

# The full gate — identical to the `check` + `zizmor` CI jobs.
check: lint format-check typecheck test security

# Auto-fix lint + formatting.
fix: lint-fix format

# --- run the tool ---

# Run the CLI (e.g. `just run analyze --project PROJ`).
run *args:
    uv run yt-issue-reviewer {{args}}

# Shortcut for the connectivity check.
doctor:
    uv run yt-issue-reviewer doctor

# --- maintenance ---

# Remove build/cache artifacts (leaves *.db result stores alone).
clean:
    rm -rf dist build .pytest_cache .ruff_cache .ty_cache
    find . -type d -name __pycache__ -prune -exec rm -rf {} +

# Upgrade locked dependencies.
deps-update:
    uv sync --upgrade
