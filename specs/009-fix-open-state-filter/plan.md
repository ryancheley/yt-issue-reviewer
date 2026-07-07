# Implementation Plan: `--state open` must return all genuinely-open issues

**Branch**: `009-fix-open-state-filter` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-fix-open-state-filter/spec.md`

## Summary

`analyze --state open` returns zero issues for projects whose issues are genuinely open
(e.g. all `State=New`), because `CliYouTrackSource._fetch_project` passes `--state Open` to
the `yt` CLI and `yt`'s server-side filter unreliably returns nothing. This is the mirror
of #35: there `yt --state Open` leaked resolved issues *in*; here it drops open issues *out*.

The #35 fix already applies the client-side `_matches_state` filter unconditionally in
`CliYouTrackSource.fetch_issues`, so the server-side `--state Open` hint is now redundant
and actively harmful. Fix: delete the two-line `if state == "open": cmd += ["--state", "Open"]`
branch in `_fetch_project` so `yt` returns all issues; the client-side filter already keeps
`New`/`In Progress` and drops `Done`/`Closed`/`Resolved`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (CLI), stdlib `json`/`subprocess`; external `yt` binary on PATH

**Storage**: SQLite (unaffected)

**Testing**: pytest — `tests/unit/test_youtrack_subprocess.py` (subprocess-stub harness), `test_youtrack_source.py`

**Target Platform**: cross-platform CLI

**Project Type**: single project (CLI + library)

**Performance Goals**: N/A — fetches all issues per project then filters in memory (as it already does for date ranges)

**Constraints**: read-only; no new dependencies; `--state all` and non-state behavior unchanged

**Scale/Scope**: one deletion (2 lines) + one regression test in one module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ No AI/network path touched.
- **II. Read-Only by Default** — ✅ Still read-only; only changes which issues are read.
- **III. Build on yt-cli** — ✅ Still reads through the `yt` subprocess seam; just drops an unreliable filter arg.
- **IV. Reproducibility / Transparency** — ✅ Open/closed determination is now deterministic and client-side, not dependent on `yt`'s server-side quirks.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ Net deletion; reuses existing `_matches_state`. No new abstraction or dependency.
- **VII. Test-First** — ✅ A failing regression test (source returns `New` only without server-side state arg) is written before the fix.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/009-fix-open-state-filter/
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
src/yt_issue_reviewer/ingest/youtrack.py   # remove `--state Open` from _fetch_project

tests/unit/
└── test_youtrack_subprocess.py            # regression: New issue surfaces under --state open
```

**Structure Decision**: Single-project layout, established. No data-model or contract
changes — the `Issue` shape is unchanged; the only change is the `yt` command line for the
`open` case (an argument is removed). `data-model.md` and `contracts/` are omitted (nothing
to add).

## Complexity Tracking

No constitution violations; table omitted.
