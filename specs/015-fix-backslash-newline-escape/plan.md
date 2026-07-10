# Implementation Plan: Repair a backslash immediately before a newline in `yt` JSON

**Branch**: `015-fix-backslash-newline-escape` | **Date**: 2026-07-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/015-fix-backslash-newline-escape/spec.md`

## Summary

`analyze` still crashes with `Invalid \escape` on projects whose issue text ends a line with a
literal backslash: `yt` emits that as a backslash directly before a raw newline, which is invalid
JSON. The #48 repair (`_escape_stray_backslashes`) misses it because its `\\(.)` branch uses `.`,
which does not match a newline without `re.DOTALL`.

Fix: add `flags=re.DOTALL` to the `re.sub` in `_escape_stray_backslashes` so the `\\(.)` branch
also matches a backslash before a newline (turning `\<newline>` into `\\<newline>` = escaped
backslash + raw newline, which `json.loads(strict=False)` then tolerates). One flag; valid escapes
and the #48 cases are unaffected (verified locally).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib `json`, `re`; external `yt` binary on PATH

**Storage**: N/A

**Testing**: pytest — `tests/unit/test_load_json_issues.py`

**Target Platform**: cross-platform CLI

**Performance Goals**: N/A — repair runs only on the rare malformed-payload fallback path

**Constraints**: no new dependency; happy path unchanged; #48 behavior and valid escapes preserved

**Scale/Scope**: one-flag change in one function, plus a regression test

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ Local text handling only; no AI/third-party path.
- **II. Read-Only by Default** — ✅ Parsing only.
- **III. Build on yt-cli** — ✅ Same `yt` stdout seam; just parses more robustly.
- **IV. Reproducibility / Transparency** — ✅ Turns a raw crash into a completed analysis (or the existing clear error).
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ A single `re.DOTALL` flag on the existing fallback regex; no new dependency or abstraction.
- **VII. Test-First** — ✅ A failing regression test (backslash-before-newline) is written before the flag change.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/015-fix-backslash-newline-escape/
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
    # _escape_stray_backslashes: add flags=re.DOTALL to the re.sub

tests/unit/test_load_json_issues.py
    # regression: backslash immediately before a raw newline inside a description parses
```

**Structure Decision**: Single-project layout, established. No data-model or contract change —
only the JSON-repair robustness changes. `data-model.md` and `contracts/` omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
