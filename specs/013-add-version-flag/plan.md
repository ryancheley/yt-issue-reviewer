# Implementation Plan: `--version` flag for the CLI

**Branch**: `013-add-version-flag` | **Date**: 2026-07-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/013-add-version-flag/spec.md`

## Summary

`yt-issue-reviewer --version` errors today (`No such option '--version'`). The version is
already a single source of truth — `yt_issue_reviewer.__version__`, read from installed
distribution metadata in `src/yt_issue_reviewer/__init__.py`. Fix: attach Click's built-in
`version_option` to the `main` group in `src/yt_issue_reviewer/cli.py`, exposing `--version`
and a `-V` short alias (`-v` is already `--verbose`, so no collision).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (already the CLI framework); stdlib `importlib.metadata` (already used for `__version__`)

**Storage**: N/A — `--version` short-circuits before any DB/network access

**Testing**: pytest with Click's `CliRunner` — `tests/unit/test_cli_options.py`

**Target Platform**: cross-platform CLI

**Project Type**: single project (CLI + library)

**Performance Goals**: N/A

**Constraints**: no new dependency; must not shadow `--verbose` (`-v`) or any subcommand; version stays a single source of truth

**Scale/Scope**: one decorator + one import in `cli.py`, and one unit test

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ Prints a local version string; no network/AI/data path.
- **II. Read-Only by Default** — ✅ Read-only; short-circuits before any subcommand.
- **III. Build on yt-cli** — ✅ Unrelated to the YouTrack seam; unaffected.
- **IV. Reproducibility / Transparency** — ✅ Exposing the exact installed version improves transparency and bug-report triage.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ Uses Click's built-in `version_option` against the existing `__version__`; no new value, no new dependency, no custom code.
- **VII. Test-First** — ✅ A failing `CliRunner` test (`--version` prints the version, exit 0) is written before wiring the option.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/013-add-version-flag/
├── plan.md              # This file
├── spec.md              # Feature spec
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/yt_issue_reviewer/cli.py     # add @click.version_option to the main group; import __version__
                                 # (src/yt_issue_reviewer/__init__.py already exposes __version__)

tests/unit/test_cli_options.py   # CliRunner: --version and -V print the version, exit 0
```

**Structure Decision**: Single-project layout, established. Pure CLI surface addition — no
data model, no external contract change beyond the new option. `data-model.md` and `contracts/`
omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
