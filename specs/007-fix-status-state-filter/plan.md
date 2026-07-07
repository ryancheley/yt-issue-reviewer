# Implementation Plan: Respect `Status` custom-field state when filtering open issues

**Branch**: `007-fix-status-state-filter` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-fix-status-state-filter/spec.md`

## Summary

`analyze --state open` leaks resolved (`Done`) issues for YouTrack projects that store
workflow state in a custom field named `Status` rather than the built-in `State` field.
Two compounding defects, both in `src/yt_issue_reviewer/ingest/youtrack.py`:

- **B (parser blind spot)**: `parse_issue` reads state from custom fields `State`/`Stage`
  only, so `issue.state` is empty for `Status`-based projects.
- **C (no client-side safety net)**: `CliYouTrackSource` trusts the server-side
  `yt --state Open` result, which is a no-op when state lives in `Status`. The existing
  `_matches_state` filter is applied by `FakeYouTrackSource` (so tests pass) but never on
  the production path.

Fix: (B) add `"Status"` to the recognized custom-field names in `parse_issue`; (C) apply
`_matches_state` in `CliYouTrackSource.fetch_issues` after parsing, before returning.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (CLI), stdlib `json`/`subprocess`; external `yt` binary on PATH

**Storage**: SQLite (unaffected by this change)

**Testing**: pytest — unit tests in `tests/unit/` (`test_ingest_filters.py`, `test_youtrack_source.py`, `test_youtrack_subprocess.py`)

**Target Platform**: cross-platform CLI (macOS, Linux, Windows)

**Project Type**: single project (CLI + library)

**Performance Goals**: N/A — an extra in-memory filter pass over an already-fetched list

**Constraints**: read-only; no new dependencies; behavior for existing `State`-based projects unchanged

**Scale/Scope**: two edits + one regression test in one module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ No AI/network path touched; purely local filtering.
- **II. Read-Only by Default** — ✅ Filtering out issues is read-only; nothing is mutated in YouTrack.
- **III. Build on yt-cli** — ✅ Still reads exclusively through the `yt` subprocess seam.
- **IV. Reproducibility / Transparency** — ✅ `--state all` still returns everything; the filter is deterministic and documented.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ Reuses the existing `_matches_state` helper; no new abstraction, no new dependency.
- **VII. Test-First** — ✅ A failing regression test (Status=Done leaks under `--state open`) is written before the fix.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/007-fix-status-state-filter/
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
src/yt_issue_reviewer/ingest/youtrack.py   # both edits (parse_issue + CliYouTrackSource.fetch_issues)

tests/unit/
├── test_youtrack_source.py                 # regression: CliYouTrackSource drops Status=Done under --state open
└── test_ingest_filters.py                  # parse_issue reads Status custom field
```

**Structure Decision**: Single-project layout, already established. No data-model or
external-contract changes — the `Issue` shape is unchanged and the `yt` command line is
unchanged. `data-model.md` and `contracts/` are intentionally omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
