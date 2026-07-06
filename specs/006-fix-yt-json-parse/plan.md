# Implementation Plan: Graceful handling of non-JSON `yt` output

**Branch**: `006-fix-yt-json-parse` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-fix-yt-json-parse/spec.md`

## Summary

Harden the single shared JSON-loading step `_load_json_issues()` in
`src/yt_issue_reviewer/ingest/youtrack.py` so that (1) a leading UTF-8 BOM is stripped before
`json.loads` — recovering the exact failure reported in issue #29 — and (2) any other non-JSON
stdout raises the existing operator-facing `YouTrackUnavailable` (with a truncated excerpt of
the bad output) instead of a raw `json.decoder.JSONDecodeError` traceback. All callers route
through this one function, so the fix is one small diff at the root. No analysis-behavior change.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: click (CLI), stdlib `json`; `yt` CLI invoked as a subprocess (external prerequisite, not bundled)

**Storage**: SQLite result store (unaffected)

**Testing**: pytest — unit tests under `tests/unit/`

**Target Platform**: cross-platform CLI (bug reported on Windows; must not regress macOS/Linux)

**Project Type**: single-project CLI/library

**Performance Goals**: N/A (parsing a single subprocess payload)

**Constraints**: no new dependencies; read-only w.r.t. YouTrack; no analysis-behavior change; excerpt in error message truncated to a readable length

**Scale/Scope**: one function hardened, ~2 unit tests added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries (NON-NEGOTIABLE)**: PASS — no data leaves user infra; the
  error excerpt is printed locally to the operator only. No hosted AI involved.
- **II. Read-Only by Default**: PASS — no writes to YouTrack; parsing only.
- **III. Build on yt-cli**: PASS — still consumes `yt` subprocess output; only hardens parsing.
- **IV. Reproducibility & Transparency**: PASS — clearer, deterministic error surfaces the
  actual `yt` output instead of hiding it in a traceback.
- **V. Local-First Data**: PASS — unaffected.
- **VI. Simplicity**: PASS — smallest change at the shared seam; no new abstraction or dep.
- **VII. Test-First**: PASS — two unit tests (BOM-prefixed valid JSON; non-JSON output) added
  and must fail before / pass after the change.

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-fix-yt-json-parse/
├── plan.md              # This file
├── spec.md              # Feature spec
├── research.md          # Phase 0 output
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

data-model.md and contracts/ are intentionally omitted: no new data entities and no change to
any external/CLI contract — this is internal hardening of one existing function.

### Source Code (repository root)

```text
src/yt_issue_reviewer/
├── ingest/
│   └── youtrack.py      # EDIT: _load_json_issues() — BOM strip + JSONDecodeError guard
└── errors.py            # REUSE: YouTrackUnavailable (no change)

tests/
└── unit/
    └── test_youtrack_ingest.py  # ADD/EXTEND: BOM + non-JSON cases
```

**Structure Decision**: Single-project layout (existing). The only production edit is
`_load_json_issues()`; the only test addition targets that function directly (no subprocess,
no network — the function takes a raw string).

## Design Notes

- **BOM strip**: `str.strip()` does not remove `﻿`. Remove a single leading BOM explicitly
  (e.g. `stdout.lstrip("﻿")` or `removeprefix("﻿")`) *before* the existing empty check
  so BOM-then-empty is still treated as empty.
- **Guard**: wrap the `json.loads` call in `try/except json.JSONDecodeError` and re-raise as
  `YouTrackUnavailable`, using `from exc`, with a message like
  `"'yt' did not return JSON. Got: <excerpt>"` where the excerpt is the first ~200 chars.
- **Preserve**: the empty/whitespace early-return and the dict/list unwrapping stay exactly as
  they are; the dict-wrapper and non-list-JSON behavior is unchanged (still "no issues").
- **Coverage**: all callers (`_fetch_project` for every project/subcommand) go through this one
  function — no per-caller patching.
