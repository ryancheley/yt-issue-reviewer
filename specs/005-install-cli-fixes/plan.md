# Implementation Plan: Cross-Platform Install and CLI Robustness Fixes

**Branch**: `005-install-cli-fixes` | **Date**: 2026-07-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-install-cli-fixes/spec.md`

## Summary

Fix three defects on the install/CLI surface that block Windows users and break documented
usage, with **no change to analysis behavior**:

1. **#22** — Drop `youtrack-cli` from `[project].dependencies`. The code never imports it; it
   only shells out to the `yt` binary on PATH (already a documented, separately-installed
   prerequisite). Removing it eliminates the transitive `docker → pywin32` native chain that
   fails to install on Windows behind on-access scanners. Regenerate `uv.lock`.
2. **#23** — Force UTF-8 standard I/O in the `yt` child process (`PYTHONUTF8=1` +
   `PYTHONIOENCODING=utf-8` in its env) and decode captured output as UTF-8, so a non-ASCII
   byte (e.g. an emoji `yt` prints) no longer crashes on a legacy Windows code page. Applies to
   both `yt` invocations (auth check + issue fetch).
3. **#24** — Make `--db`, `--ollama-host`, and `--config` accept their documented
   post-subcommand placement across all subcommands, keeping existing pre-subcommand placement
   working and preserving config precedence.

## Technical Context

**Language/Version**: Python 3.11–3.14 (existing floor, feature 004)

**Primary Dependencies**: click>=8.1, rich>=13.7, numpy>=2.0, ollama>=0.6. `youtrack-cli` is
**removed** as a bundled dependency and becomes a documented external prerequisite (the `yt`
binary on PATH). No new dependency is added.

**Storage**: SQLite local cache — unaffected.

**Testing**: pytest (existing offline suite); ruff + ty as part of the gate.

**Target Platform**: Any OS with CPython 3.11–3.14. This feature specifically hardens the
Windows path (native-dep install + console encoding).

**Project Type**: Single-project Python CLI. No structure change.

**Performance Goals**: N/A (no runtime-behavior change; FR-010 forbids analysis drift).

**Constraints**: Change must not alter analysis output; `uv.lock` must still resolve across
3.11–3.14; CI/zizmor stay green. Reads remain read-only and routed exclusively through `yt`.

**Scale/Scope**: ~4 files edited — `pyproject.toml` (drop dep), `src/.../ingest/youtrack.py`
(UTF-8 subprocess env), `src/.../cli.py` + `src/.../config.py` (per-command option resolution),
plus doc alignment (README + docs) and a regenerated `uv.lock`. Tests added for the subprocess
env and option placement.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Privacy / Data Boundaries (NON-NEGOTIABLE)**: ✅ Unaffected. No inference/embedding path
  changes; no issue content moves anywhere new. UTF-8 env only affects local subprocess I/O.
- **II. Read-Only by Default**: ✅ Unaffected. The `yt` invocations remain the same read-only
  `auth token --show` and `issues list` commands; no write path added.
- **III. Build on yt-cli**: ✅ Honored. The tool still interacts with YouTrack **exclusively**
  through the `yt` CLI. Dropping the *pip dependency* does not add a parallel HTTP client; it
  reflects reality — the code shells out to `yt` and never imports `youtrack_cli`. `youtrack-cli`
  remains required, as a separately-installed prerequisite (as the install docs already state).
  ⚠️ Nuance: the principle names the package `youtrack_cli`; this plan keeps it as the sole
  YouTrack client, just un-bundled. No parallel client is introduced, so the principle's intent
  (one shared client, no bespoke REST client) is preserved.
- **IV. Reproducibility / Transparency**: ✅ Unaffected. Scoring/evidence/model-recording
  untouched.
- **V. Local-First Data**: ✅ Unaffected. SQLite cache unchanged.
- **VI. Simplicity**: ✅ Reinforced — a dependency is *removed*, no new dependency or layer added;
  the option-placement fix is a small shared decorator, not a framework.
- **VII. Test-First**: ✅ New offline tests cover the UTF-8 subprocess env and post-subcommand
  option placement. No test needs live YouTrack/Ollama.

**Gate result**: PASS. No non-negotiable principle affected. Principle III nuance documented
above (un-bundling, not replacing, the client) — not a violation.

## Project Structure

### Documentation (this feature)

```text
specs/005-install-cli-fixes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (n/a entities — records the "no data model" decision)
├── quickstart.md        # Phase 1 output (validation guide)
├── contracts/
│   └── cli-options.md   # CLI option-placement contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
pyproject.toml                              # drop youtrack-cli from dependencies
uv.lock                                     # regenerated
src/yt_issue_reviewer/
├── cli.py                                  # per-command --db/--ollama-host/--config resolution
├── config.py                              # (unchanged API; Config.load already merges overrides)
└── ingest/youtrack.py                      # UTF-8 subprocess env for both yt invocations
tests/
├── test_youtrack_subprocess.py            # NEW: asserts UTF-8 env passed to subprocess
└── test_cli_options.py                     # NEW: asserts post-subcommand option placement works
docs/                                       # README + docs: option placement already matches; verify
```

**Structure Decision**: Single-project CLI, no structural change. The fix touches packaging,
the one subprocess seam (`ingest/youtrack.py`), and the CLI wiring (`cli.py`), plus docs.

## Complexity Tracking

> No constitution violations. Table intentionally empty.
