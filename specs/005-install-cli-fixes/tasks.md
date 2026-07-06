# Tasks: Cross-Platform Install and CLI Robustness Fixes

**Feature**: `005-install-cli-fixes` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

**Tests**: Included (offline unit tests) — the constitution's Principle VII (Test-First) and the
spec's Independent Test criteria call for them.

## Phase 1: Setup

- [x] T001 Confirm clean working tree on branch `005-install-cli-fixes` and baseline the gate: run `just check` to record the current green state before changes.

## Phase 2: Foundational

_None. The three fixes are independent; there is no shared prerequisite beyond the repo itself._

---

## Phase 3: User Story 1 — Install succeeds on Windows behind endpoint protection (#22, P1)

**Goal**: Remove the unused `youtrack-cli` dependency so the `docker → pywin32` native chain is no
longer bundled; the tool still works via the `yt` binary on PATH.

**Independent Test**: `uv tree` shows no `youtrack-cli`/`docker`/`pywin32`; the tool still imports
and runs; `check_available()` still gives the clear "install youtrack-cli" message when `yt` is absent.

- [x] T002 [US1] Remove `"youtrack-cli>=0.24.0"` from `[project].dependencies` in `pyproject.toml`.
- [x] T003 [US1] Regenerate the lock with `uv lock`; verify `uv tree` shows no `youtrack-cli`, `docker`, or `pywin32`.
- [x] T004 [P] [US1] Update the docstring in `src/yt_issue_reviewer/ingest/youtrack.py` (module + `CliYouTrackSource`) so it states `youtrack_cli` is an external prerequisite invoked as the `yt` binary, not a bundled dependency.
- [x] T005 [P] [US1] Verify install/prerequisite docs (`README.md`, `docs/installation.rst`) still clearly require a separately-installed, authenticated `youtrack-cli`; adjust wording only if it implied the tool bundles it.

**Checkpoint**: US1 independently verifiable via `uv tree` + existing `test_youtrack_source.py`.

---

## Phase 4: User Story 2 — Fetching issues works on a Windows console (#23, P1)

**Goal**: Force UTF-8 standard I/O in the spawned `yt` process and decode captured output as UTF-8,
at both invocation sites, so non-ASCII output no longer crashes on a legacy code page.

**Independent Test**: `tests/unit/test_youtrack_subprocess.py` asserts the subprocess is called with
`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, and `encoding="utf-8"`.

- [x] T006 [US2] Add UTF-8 subprocess handling in `src/yt_issue_reviewer/ingest/youtrack.py`: a module-level UTF-8 env (merged over `os.environ`) and pass `env=...` + `encoding="utf-8"` to `subprocess.run(...)` in both `check_available()` (`yt auth token --show`) and `_fetch_project()` (`yt issues list`).
- [x] T007 [US2] Write `tests/unit/test_youtrack_subprocess.py`: monkeypatch `subprocess.run` to capture kwargs; assert both call sites pass the UTF-8 env keys and `encoding="utf-8"`, using a fake returning valid JSON so `_fetch_project` parses.

**Checkpoint**: `uv run pytest tests/unit/test_youtrack_subprocess.py -q` passes.

---

## Phase 5: User Story 3 — Documented CLI option placement works (#24, P2)

**Goal**: Accept `--db`, `--ollama-host`, `--config` after the subcommand for all subcommands,
keeping pre-subcommand placement working, with subcommand value winning; precedence otherwise unchanged.

**Independent Test**: `tests/unit/test_cli_options.py` drives the CLI (via click's runner) with
options after the subcommand and asserts acceptance + correct resolution.

- [x] T008 [US3] In `src/yt_issue_reviewer/cli.py`: add a shared `_common_options` decorator declaring `--db`/`--config`/`--ollama-host` (default `None`); have the group store its own raw values + verbose in `ctx.obj`; change `_config` to resolve effective values as subcommand-or-group and build via `Config.load(...)`.
- [x] T009 [US3] Apply `@_common_options` to `doctor`, `ingest`, `embed`, `analyze`, `show`, `runs`; thread the three params into each signature and pass them to `_config(ctx, ...)`. Keep all existing option behavior.
- [x] T010 [US3] Write `tests/unit/test_cli_options.py` using `click.testing.CliRunner`: assert `show --db X` / `doctor --ollama-host U` / `analyze … --db X --ollama-host U` are accepted (no "No such option"), and that `--db A show --db B` resolves to `B` (assert via a monkeypatched `Repository.open`/`Config` capture, no network).
- [x] T011 [P] [US3] Align docs with the [cli-options contract](./contracts/cli-options.md): confirm every `--db`/`--ollama-host`/`--config` example in `README.md`, `docs/quickstart.rst`, `docs/cli-reference.rst`, `docs/installation.rst` now matches accepted placement.

**Checkpoint**: `uv run pytest tests/unit/test_cli_options.py -q` passes; documented commands parse.

---

## Phase 6: Polish & Cross-Cutting

- [x] T012 Run the full gate `just check` (ruff, ruff format, ty, pytest, zizmor) — all green.
- [x] T013 Sanity: `uv run yt-issue-reviewer --help` and each subcommand `--help` render; `show --db ./yir.db` and `doctor --ollama-host http://127.0.0.1:11434` reach connectivity (not an option-parse) error.
- [x] T014 Verify FR-010: an equivalent analysis run (offline integration test `tests/integration/test_analyze_end_to_end.py`) produces unchanged output.

---

## Dependencies & Execution Order

- **Setup (T001)** → baseline before changes.
- **US1 (T002–T005)**, **US2 (T006–T007)**, **US3 (T008–T011)** are mutually independent and may be done in any order. US1 and US2 both touch `ingest/youtrack.py` (US1 only the docstring, US2 the subprocess code) — do T004 and T006 sequentially to avoid a conflict, or in one edit pass.
- **Polish (T012–T014)** after all stories.

## Parallel Opportunities

- Within US1: T004 and T005 are `[P]` (different files: source docstring vs docs).
- T011 `[P]` (docs) can proceed alongside US3 code once T008–T009 land.
- The three user stories can be developed in parallel by different agents (distinct files, except the noted youtrack.py docstring/subprocess coordination).

## MVP Scope

**US1 + US2** (both P1) are the minimum: together they make the tool installable and runnable on
Windows. US3 (P2) fixes documented ergonomics and should ship in the same PR since it's small.

## Format Validation

All tasks use `- [x] Txxx [P?] [US?] description with file path`. Setup/Foundational/Polish carry no
story label; US phases are labeled [US1]/[US2]/[US3].
