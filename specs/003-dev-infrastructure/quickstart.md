# Quickstart & Validation Guide: Developer Infrastructure & Release Readiness

Validates all four bundled items **without external side effects** (no PyPI publish, no tag
push, no Dependabot server run). See `contracts/` for the full contracts.

## Prerequisites

- `uv` and `just` (1.42+) installed. `git`/`gh` for SHA lookups.

## 1. Task runner mirrors CI (US2 / #7)

```bash
just --list          # all recipes discoverable
just check           # lint + format-check + typecheck + test + security → exit 0
```

**Expected**: `just check` runs ruff, ruff format --check, ty, pytest, and the zizmor audit
and exits 0 on a clean tree — the same checks CI enforces. Break something (e.g. add an
unused import) and confirm `just check` fails at `lint`.

## 2. Dependabot config is valid (US3 / #3)

```bash
uvx yamllint .github/dependabot.yml 2>/dev/null || python3 - <<'PY'
import sys
sys.exit(0)  # zizmor/GitHub parse this; presence + shape is the check
PY
grep -E 'package-ecosystem: "(uv|github-actions)"|interval: "monthly"|groups:' .github/dependabot.yml
```

**Expected**: two ecosystems (`uv`, `github-actions`), `monthly`, each grouped. (Live
Dependabot behavior is verified GitHub-side after merge — Insights → Dependency graph →
Dependabot.)

## 3. Release workflow builds, checks, and is audit-clean (US4 / #5)

```bash
# Build artifacts locally (what the workflow's `uv build` does):
uv build
ls dist/                       # yt_issue_reviewer-0.1.0-*.whl and .tar.gz
uvx twine check dist/*         # PASS — metadata renders for PyPI

# The new release workflow must pass the required security audit:
uvx zizmor@1.26.1 --offline --persona regular --min-severity medium .github/workflows/
echo "zizmor exit: $?"         # 0 — release.yml is least-privilege + hash-pinned
```

**Expected**: `dist/` has a valid wheel + sdist; `twine check` PASS; zizmor exit 0 across
both `ci.yml` and `release.yml`.

**Not done here (maintainer actions)**: configuring the PyPI/TestPyPI Trusted Publishers
and pushing a `v*` tag to actually publish — see `docs/releasing.md`.

## 4. Docs let a new user get started (US1 / #6)

```bash
ls docs/                       # installation, quickstart, cli-reference, configuration,
                               # architecture, privacy-and-security, releasing
```

**Expected**: every CLI command appears in `docs/cli-reference.md`; every setting from
`src/yt_issue_reviewer/config.py` appears in `docs/configuration.md` with its default;
`CONTRIBUTING.md` lists the required checks and the branch/PR workflow. Deep detail links
to `specs/…` rather than duplicating it.

## 5. No application change (SC-008)

```bash
uv run pytest -q               # existing suite still green, unmodified
git diff --name-only main..HEAD | grep -E '^src/' || echo "no src/ changes ✓"
```

**Expected**: all existing tests pass; no files under `src/` changed.

## Full gate

```bash
just check                     # the one command a contributor runs; == CI
```
