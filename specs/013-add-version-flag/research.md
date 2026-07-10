# Research: `--version` flag for the CLI

Small, well-understood change; no open unknowns.

## Decision: Use Click's `version_option` against the existing `__version__`

- **Decision**: Add `@click.version_option(__version__, "-V", "--version", prog_name="yt-issue-reviewer")`
  to the `main` group in `cli.py`, importing `__version__` from the package (`from . import __version__`).
- **Rationale**: Click's built-in `version_option` prints `<prog>, version <X.Y.Z>` and exits 0,
  handling the short-circuit for us — no custom callback needed (VI. Simplicity). The version value
  reuses `yt_issue_reviewer.__version__`, which `src/yt_issue_reviewer/__init__.py` already derives
  from installed distribution metadata (`importlib.metadata.version("yt-issue-reviewer")`), so there
  is exactly one source of truth (FR-003).
- **Short alias**: `-v` is already bound to `--verbose` on the group, so the version short flag is
  the capital `-V` (Click/GNU convention) — no collision (FR-005).
- **Alternatives considered**:
  - `@click.version_option(package_name="yt-issue-reviewer")` (let Click read metadata itself) —
    equivalent, but passing the already-imported `__version__` keeps the tool's single accessor as
    the one path and works even if invoked from a source tree; either is fine.
  - A hand-rolled `--version` flag + callback — rejected: reinvents what Click provides.

## Verification approach

- `CliRunner().invoke(main, ["--version"])` → `exit_code == 0` and output contains
  `yt_issue_reviewer.__version__` (asserting against the source-of-truth value, not a hardcoded
  string, so the test never needs updating on a version bump).
- Same for `-V`.

## Out of scope

- Changing where the version is declared (stays in `pyproject.toml`, read via metadata).
- A separate `version` subcommand (the `--version` flag is the conventional, sufficient surface).
