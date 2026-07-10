# Implementation Plan: Tolerate invalid backslash escapes in `yt` JSON output

**Branch**: `012-fix-invalid-json-escape` | **Date**: 2026-07-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/012-fix-invalid-json-escape/spec.md`

## Summary

`analyze` crashes with `json.decoder.JSONDecodeError: Invalid \escape` when `yt`'s JSON
contains a backslash that isn't a valid JSON escape — e.g. a Windows path (`C:\Users`) or a
regex (`\d+`) in an issue description that `yt` emitted unescaped (issue #48). `strict=False`
in `_load_json_issues` relaxes only the control-character rule (#29/#34), not escape validity.

Fix: in `_load_json_issues`, when `json.loads(stdout, strict=False)` raises `JSONDecodeError`,
repair the payload once — double every `\` that is **not** part of a valid JSON escape
(`\" \\ \/ \b \f \n \r \t \uXXXX`) via a function-based regex — and retry `json.loads(...,
strict=False)`. If the retry still fails, re-raise the existing operator-facing
`YouTrackUnavailable` with a truncated excerpt. The repair is a fallback only, so well-formed
JSON is untouched and valid escapes are preserved (verified).

## Technical Context

**Language/Version**: Python 3.11+ (reporter hit it on 3.12/Windows)

**Primary Dependencies**: stdlib `json`, `re`; external `yt` binary on PATH

**Storage**: SQLite (unaffected)

**Testing**: pytest — `tests/unit/test_load_json_issues.py`

**Target Platform**: cross-platform CLI (bug surfaced on Windows via Windows-path backslashes)

**Project Type**: single project (CLI + library)

**Performance Goals**: N/A — the repair runs only on the rare malformed-payload fallback path

**Constraints**: read-only; no new dependencies (stdlib `re` only); happy path unchanged

**Scale/Scope**: one helper function + a few lines in `_load_json_issues`, and unit tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ Local text handling only; no AI/third-party path.
- **II. Read-Only by Default** — ✅ Parsing only; nothing mutated.
- **III. Build on yt-cli** — ✅ Still reads `yt` stdout through the same seam; just parses it more robustly.
- **IV. Reproducibility / Transparency** — ✅ Turns a raw traceback into a completed analysis (or the existing clear error); repair is a documented, deterministic fallback.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ One small stdlib-regex helper on the fallback path; no new dependency, no new abstraction.
- **VII. Test-First** — ✅ A failing regression test (unescaped backslash inside a description) is written before the fix.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/012-fix-invalid-json-escape/
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
    # _load_json_issues: on JSONDecodeError, repair stray backslashes and retry once
    # + a module helper `_escape_stray_backslashes(text)`

tests/unit/
└── test_load_json_issues.py   # unescaped-backslash payload parses; valid escapes preserved;
                               # still-non-JSON banner raises YouTrackUnavailable
```

**Structure Decision**: Single-project layout, established. No data-model or contract change —
the parsed `Issue` shape is unchanged; only the JSON-loading robustness changes.
`data-model.md` and `contracts/` are omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
