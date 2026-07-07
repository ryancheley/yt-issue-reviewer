# Implementation Plan: Fetch every issue in a project, not just the first page

**Branch**: `010-fetch-all-issues` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-fetch-all-issues/spec.md`

## Summary

`analyze` silently ingests at most 100 issues per project. `CliYouTrackSource._fetch_project`
runs `yt issues list --project-id <P> --format json` with no pagination flag, and `yt`'s
`--page-size` defaults to 100, so issues past the first page are dropped without warning —
surfaced on a large Jira-imported project on a remote instance.

Fix: add `--all` to the `yt issues list` command in `_fetch_project` so `yt` pages through
the entire result set. Client-side state/date filtering already runs over the full fetched
set, so it composes unchanged.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (CLI), stdlib `subprocess`/`json`; external `yt` binary on PATH

**Storage**: SQLite (unaffected)

**Testing**: pytest — `tests/unit/test_youtrack_subprocess.py` (subprocess-stub harness captures the issued command)

**Target Platform**: cross-platform CLI

**Project Type**: single project (CLI + library)

**Performance Goals**: N/A functionally; fetch now returns the full project (more pages → longer fetch, bounded by the existing 300s subprocess timeout)

**Constraints**: read-only; no new dependencies; behavior for ≤100-issue projects unchanged

**Scale/Scope**: one added CLI argument + one regression test in one module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ No AI/network path touched.
- **II. Read-Only by Default** — ✅ Still read-only; fetches more issues, mutates nothing.
- **III. Build on yt-cli** — ✅ Uses `yt`'s own `--all` pagination flag; still the sole seam.
- **IV. Reproducibility / Transparency** — ✅ Results are now complete instead of silently truncated at 100.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ One flag; delegates paging to `yt` rather than hand-rolling a page loop. No new abstraction/dependency.
- **VII. Test-First** — ✅ A failing regression test (issued command lacks `--all`) is written before the fix.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/010-fetch-all-issues/
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
src/yt_issue_reviewer/ingest/youtrack.py   # add `--all` to _fetch_project's yt command

tests/unit/
└── test_youtrack_subprocess.py            # regression: issued command includes --all
```

**Structure Decision**: Single-project layout, established. No data-model or contract
changes — the `Issue` shape and the JSON parsing are unchanged; only one argument is added
to the `yt` command line. `data-model.md` and `contracts/` are omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
