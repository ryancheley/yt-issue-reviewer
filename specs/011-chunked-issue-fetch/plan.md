# Implementation Plan: Fetch issues in bounded chunks so slow/gated networks work

**Branch**: `011-chunked-issue-fetch` | **Date**: 2026-07-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/011-chunked-issue-fetch/spec.md`

## Summary

`analyze` returns 0 issues against instances behind a gateway that kills any `yt` request
running past ~20s. `CliYouTrackSource._fetch_project` fetches the whole project in one
`--all` request, which exceeds that limit; `yt` returns empty and the tool reports 0 issues.

Fix: replace the single `--all` request with a **creation-date cursor** loop of bounded
requests. Each page fetches the oldest `PAGE` issues via
`yt issues list --query "project: <P> sort by: created asc" --top PAGE --format json`; the
cursor advances to the newest `created` date in the page **minus one day** (overlap, never a
gap, to survive timezone skew), and the next page adds `created: <cursor> ..` to the query.
Issues are de-duplicated by id; the loop stops on a short page (< PAGE). A same-date stall
(a full page with no new issues) raises the operator-facing `YouTrackUnavailable` with
guidance. `--all` is removed. `PAGE ≈ 200` keeps each request well under ~20s.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (CLI), stdlib `subprocess`/`json`/`datetime`; external `yt` binary on PATH

**Storage**: SQLite (unaffected)

**Testing**: pytest — `tests/unit/test_youtrack_subprocess.py` (stubs `subprocess.run` to return synthetic pages)

**Target Platform**: cross-platform CLI, including behind corporate/remote gateways with per-request time limits

**Project Type**: single project (CLI + library)

**Performance Goals**: each request bounded (~200 issues, well under the ~20s gateway ceiling); total fetch = ceil(total/PAGE) sequential requests

**Constraints**: read-only; no new dependencies; stays on the `yt` binary seam; small projects behave as before

**Scale/Scope**: one function reworked (`_fetch_project`) plus a small cursor helper, and unit tests, in one module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ No AI/third-party path; only how issues are read from the operator's own YouTrack.
- **II. Read-Only by Default** — ✅ Still purely read; paging changes only how issues are fetched.
- **III. Build on yt-cli** — ✅ Stays entirely on the `yt` binary (uses its `--query`/`--top`/sort); no direct REST, no re-added dependency.
- **IV. Reproducibility / Transparency** — ✅ Result is the complete issue set instead of a silent empty; the same-date stall fails loudly with guidance.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ A single cursor loop with dedup; no new abstraction or dependency. Removes the `--all` flag.
- **VII. Test-First** — ✅ Failing unit tests (paging, overlap dedup, short-page stop, same-date stall) written before the implementation.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/011-chunked-issue-fetch/
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
src/yt_issue_reviewer/ingest/youtrack.py
    # _fetch_project: replace the single --all request with the created-date cursor loop
    # (+ a small helper for the "minus one day" cursor and one for a single bounded page)

tests/unit/
└── test_youtrack_subprocess.py   # stub subprocess.run with synthetic ascending-created
                                  # pages: assert multi-page assembly, overlap dedup,
                                  # short-page stop, and same-date stall raises
```

**Structure Decision**: Single-project layout, established. No data-model or external-contract
change — the `Issue` shape, JSON parsing, and downstream filtering are unchanged; only the
fetch strategy inside `_fetch_project` changes (bounded pages instead of one `--all`).
`data-model.md` and `contracts/` are omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
