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

# --- release ---
# Cutting a release is a PR-gated, two-step flow (see docs/releasing.rst). The version is
# single-sourced in pyproject.toml and the pushed tag MUST match it (release.yml verifies).
#   1. `just release-prep X.Y.Z`  → opens a version-bump PR (never pushes to main directly)
#   2. merge that PR, then `just release X.Y.Z` → tags main and pushes the tag; the release
#      workflow builds → TestPyPI → PyPI → GitHub Release.

# Validate a version string and classify the bump (major/minor/patch) against pyproject.toml.
release-check version:
    #!/bin/sh
    set -eu
    current=$(grep -m1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    uv run --no-project python -c '
    import re, sys
    new, cur = sys.argv[1], sys.argv[2]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", new):
        sys.exit(f"ERROR: {new!r} is not semver X.Y.Z (e.g. 1.2.3).")
    nt = tuple(map(int, new.split(".")))
    ct = tuple(map(int, cur.split(".")))
    if nt <= ct:
        sys.exit(f"ERROR: {new} is not an increment over the current version {cur}.")
    if nt == (ct[0] + 1, 0, 0):
        print(f"{new} is a valid MAJOR bump from {cur}")
    elif nt == (ct[0], ct[1] + 1, 0):
        print(f"{new} is a valid MINOR bump from {cur}")
    elif nt == (ct[0], ct[1], ct[2] + 1):
        print(f"{new} is a valid PATCH bump from {cur}")
    else:
        sys.exit(
            f"ERROR: {new} is not a single increment from {cur} "
            f"(expected {ct[0] + 1}.0.0, {ct[0]}.{ct[1] + 1}.0, or {ct[0]}.{ct[1]}.{ct[2] + 1})."
        )
    ' "{{ version }}" "$current"

# Show current version, last tag, commits since, and recent CI runs.
release-status:
    #!/bin/sh
    set -u
    echo "Current version: $(grep -m1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')"
    last=$(git describe --tags --abbrev=0 2>/dev/null || echo none)
    echo "Last tag:        $last"
    if [ "$last" != "none" ]; then
        echo "Commits since:   $(git rev-list "$last"..HEAD --count)"
    else
        echo "Commits total:   $(git rev-list HEAD --count)"
    fi
    echo "Recent CI runs:"
    gh run list --limit 5 2>/dev/null || echo "  (gh unavailable)"

# Step 1: open the version-bump PR. Bumps pyproject.toml on a branch, re-locks, pushes, and
# opens a PR — never touches main directly (branch protection + required checks apply).
release-prep version: (release-check version)
    #!/bin/sh
    set -eu
    v="{{ version }}"
    if [ -n "$(git status --porcelain)" ]; then
        echo "ERROR: Working tree is dirty. Commit or stash your changes first." >&2
        exit 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
        echo "ERROR: GitHub CLI is not authenticated. Run: gh auth login" >&2
        exit 1
    fi
    git switch main --quiet
    git pull --quiet
    branch="release-v$v"
    git switch -c "$branch"
    uv run --no-project python -c '
    import pathlib, re, sys
    p = pathlib.Path("pyproject.toml")
    p.write_text(re.sub(r"(?m)^version = \".*\"$", f"version = \"{sys.argv[1]}\"", p.read_text(), count=1))
    ' "$v"
    uv lock --quiet
    git add pyproject.toml uv.lock
    git commit -m "🔖 Bump version to $v"
    git push -u origin "$branch"
    gh pr create --title "🔖 Bump version to $v" \
        --body "Version bump to \`v$v\`. After this merges, cut the release with \`just release $v\`."
    echo "Opened the bump PR. Once it merges: git switch main && git pull && just release $v"

# Step 2: cut the release — tag main and push the tag. Run AFTER the release-prep PR merged.
# Pushes only a tag (never a commit to main); release.yml takes it from there. No release-check
# here: pyproject is already AT the target (the merged bump PR did that), which release-check
# would reject as "not an increment". The `$pkg != $v` guard below verifies the match instead.
release version:
    #!/bin/sh
    set -eu
    v="{{ version }}"
    branch=$(git branch --show-current)
    if [ "$branch" != "main" ]; then
        echo "ERROR: Not on main (on '$branch'). Run: git switch main && git pull" >&2
        exit 1
    fi
    if [ -n "$(git status --porcelain)" ]; then
        echo "ERROR: Working tree is dirty. Commit or stash your changes first." >&2
        exit 1
    fi
    git fetch origin main --quiet
    if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
        echo "ERROR: Local main differs from origin/main. Run: git pull, then retry." >&2
        exit 1
    fi
    pkg=$(grep -m1 '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
    if [ "$pkg" != "$v" ]; then
        echo "ERROR: pyproject.toml is at $pkg, not $v. Bump it first: just release-prep $v (then merge the PR)." >&2
        exit 1
    fi
    if ! gh auth status >/dev/null 2>&1; then
        echo "ERROR: GitHub CLI is not authenticated. Run: gh auth login" >&2
        exit 1
    fi
    if git rev-parse -q --verify "refs/tags/v$v" >/dev/null; then
        echo "ERROR: Tag v$v already exists locally. Roll back first: just rollback-release $v" >&2
        exit 1
    fi
    if [ -n "$(git ls-remote --tags origin "refs/tags/v$v")" ]; then
        echo "ERROR: Tag v$v already exists on origin. Pick a new version or roll back first." >&2
        exit 1
    fi
    if ! just check; then
        echo "ERROR: 'just check' failed. Fix the failures, then re-run the release." >&2
        exit 1
    fi
    echo "Pre-flight passed. Tagging v$v..."
    git tag "v$v"
    if ! git push origin "v$v"; then
        git tag -d "v$v"
        echo "ERROR: Tag push failed; local tag removed. Retry: git tag v$v && git push origin v$v" >&2
        exit 1
    fi
    echo "Pushed tag v$v — release.yml now builds → TestPyPI → PyPI → GitHub Release."
    echo "Watch it with: gh run watch"

# Undo a release: delete the tag (remote + local). Revert the version bump via a separate PR.
rollback-release version:
    #!/bin/sh
    set -eu
    v="{{ version }}"
    echo "This deletes tag v$v (remote and local). A merged version bump must be reverted via a PR."
    printf "Type 'yes' to continue: "
    read -r answer
    case "$answer" in
        yes|y) ;;
        *) echo "Aborted. Nothing changed."; exit 1 ;;
    esac
    remote_tag=$(git ls-remote --tags origin "refs/tags/v$v")
    local_tag=$(git rev-parse -q --verify "refs/tags/v$v" || true)
    if [ -z "$remote_tag" ] && [ -z "$local_tag" ]; then
        echo "ERROR: Tag v$v exists neither locally nor on origin — nothing to roll back." >&2
        exit 1
    fi
    if [ -n "$remote_tag" ]; then
        git push origin ":refs/tags/v$v"
        echo "Deleted remote tag v$v."
    else
        echo "Remote tag v$v not found (already deleted?) — skipping."
    fi
    if [ -n "$local_tag" ]; then
        git tag -d "v$v"
        echo "Deleted local tag v$v."
    fi
    echo "Tag v$v rolled back. If the bump already merged, open a revert PR for '🔖 Bump version to $v'."
