# Implementation Plan: Surface `yt`'s stdout in failure messages

**Branch**: `014-surface-yt-stdout-errors` | **Date**: 2026-07-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/014-surface-yt-stdout-errors/spec.md`

## Summary

When a `yt` invocation exits non-zero, `CliYouTrackSource` raises `YouTrackUnavailable` using
only `proc.stderr`. But `yt` often writes the real reason to **stdout** — e.g. youtrack-cli
0.24.5 prints `❌ Not authenticated` to stdout while stderr only has `Error: Failed to list
issues` — so operators can't tell they need to re-run `yt auth login` (issue #54).

Fix: add a small helper `_proc_output(proc)` that joins the non-empty stripped stdout and
stderr with a newline, and use it in both failure branches — `check_available()` (the
`yt auth token --show` rc!=0 path) and `_fetch_page()` (the `yt issues list` rc!=0 path). The
existing "Run `yt auth login`" guidance and the success path are unchanged.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib `subprocess`; external `yt` binary on PATH

**Storage**: N/A

**Testing**: pytest — `tests/unit/test_youtrack_subprocess.py` (stubs `subprocess.run`)

**Target Platform**: cross-platform CLI

**Performance Goals**: N/A

**Constraints**: no new dependency; only the two `yt` failure branches change; success path untouched

**Scale/Scope**: one small helper + two one-line edits in one module, and unit tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries** — ✅ Only formats a local error string; no network/AI path.
- **II. Read-Only by Default** — ✅ Error handling only.
- **III. Build on yt-cli** — ✅ Improves how `yt` failures are reported; the seam is unchanged.
- **IV. Reproducibility / Transparency** — ✅ Directly improves transparency: operators see the real reason (e.g. "Not authenticated") instead of a vague message.
- **V. Local-First Data** — ✅ Unaffected.
- **VI. Simplicity** — ✅ One tiny helper; net-simpler than duplicating the join at two sites. No new dependency.
- **VII. Test-First** — ✅ Failing tests (stdout-only reason surfaced; stderr-only preserved) written before the change.

No violations. Complexity Tracking not needed.

## Project Structure

### Documentation (this feature)

```text
specs/014-surface-yt-stdout-errors/
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
    # _proc_output(proc) helper; use it in check_available() and _fetch_page() failure branches

tests/unit/test_youtrack_subprocess.py
    # stub subprocess.run rc!=0 with reason on stdout -> raised message contains it;
    # stderr-only case still included
```

**Structure Decision**: Single-project layout, established. Pure error-message improvement — no
data model, no contract change. `data-model.md` and `contracts/` omitted (nothing to add).

## Complexity Tracking

No constitution violations; table omitted.
