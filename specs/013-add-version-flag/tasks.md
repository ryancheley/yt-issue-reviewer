# Tasks: `--version` flag for the CLI

**Feature**: 013-add-version-flag | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Single P1 user story (issue #51). Constitution VII (Test-First): write the failing test before
wiring the option. No setup/foundational work — `cli.py`, `__version__`, and the CLI test file
already exist.

## Phase 1: User Story 1 — Check the installed version (P1)

**Goal**: `yt-issue-reviewer --version` (and `-V`) prints the installed version and exits 0.

**Independent test**: `uv run pytest tests/unit/test_cli_options.py` — the new test fails before
the fix, passes after.

### Tests first (write, watch fail)

- [X] T001 [US1] In `tests/unit/test_cli_options.py`, add a `CliRunner` test that invokes `main` with `["--version"]`, asserts `exit_code == 0`, and asserts the output contains `yt_issue_reviewer.__version__` (compare to the source-of-truth value, not a hardcoded string).
- [X] T002 [US1] Add a `CliRunner` test that `["-V"]` produces the same version output and `exit_code == 0` (short alias, and it must not collide with `-v`/`--verbose`).

### Implementation

- [X] T003 [US1] In `src/yt_issue_reviewer/cli.py`, import the package version (`from . import __version__`) and add `@click.version_option(__version__, "-V", "--version", prog_name="yt-issue-reviewer")` to the `main` group (alongside the existing `@click.option` decorators on the `@click.group()`), so `-v` remains `--verbose`.

## Phase 2: Polish & verification

- [X] T004 Run `just check` (ruff + ty + full pytest + zizmor) and confirm the CI gate is green with no regressions (SC-004).
- [X] T005 Manual check: `uv run yt-issue-reviewer --version` and `-V` print `yt-issue-reviewer, version X.Y.Z` (matching pyproject); `--help` lists `--version`; `analyze --help` still works (SC-001/003/004).

## Dependencies

- T001, T002 (tests) before T003 (impl) — Test-First. T001 ∥ T002 (same file, but independent assertions; write together).
- T004/T005 after T003.

## MVP scope

The single P1 story *is* the MVP. Completing T001–T004 fully resolves issue #51.
