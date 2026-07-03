# Contributing

Thanks for contributing to `yt-issue-reviewer`. This project follows a spec-driven
workflow and a strict, automated quality gate.

## Setup

```bash
uv sync --dev
# `just` is used as the task runner — install it if you don't have it:
#   brew install just    |    uv tool install rust-just    |    cargo install just
```

## The required gate (`just check`)

`just check` runs **exactly** what CI enforces, so you get local == CI feedback:

```bash
just check      # ruff check, ruff format --check, ty type-check, pytest, and the zizmor audit
just fix        # auto-fix lint + formatting
```

Run `just --list` to see every recipe (`install`, `lint`, `format`, `typecheck`, `test`,
`security`, `run`, `doctor`, `clean`, `deps-update`).

> The `check` recipe in `justfile` and the jobs in `.github/workflows/ci.yml` must stay in
> lock-step. If you add or remove a check, update **both**.

Tooling: the type checker is **ty** (not mypy/pyright); the linter/formatter is **ruff**;
tests use **pytest**; the workflow security audit is **zizmor** (run via `uvx`, not a
project dependency).

## Branch & PR workflow

- Always work on a **feature branch** — never commit or push directly to `main`.
- Open a pull request. Branch protection requires the `check` **and** `zizmor` status
  checks to pass before merge; do not bypass them.
- Once approved, **squash-merge**, then switch back to `main` and pull.
- Keep commit messages emoji-prefixed.

## Design constraints (the constitution)

All changes must respect the [project constitution](./.specify/memory/constitution.md) —
notably: read-only against YouTrack, self-hosted Ollama only (no third-party hosted AI),
all YouTrack access via `youtrack_cli`, evidence-backed and reproducible results, local-first
data, and simplicity. New GitHub Actions must use least-privilege permissions and hash-pinned
actions so the `zizmor` gate stays green.

## Spec-driven changes

Larger features use the spec-kit flow under `specs/` (spec → plan → tasks → implement). See
existing features in `specs/` for the pattern.
