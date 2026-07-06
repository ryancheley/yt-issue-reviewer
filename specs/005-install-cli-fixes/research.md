# Phase 0 Research: Cross-Platform Install and CLI Robustness Fixes

No open NEEDS CLARIFICATION markers. This records the decisions behind each fix.

## R1 — Remove `youtrack-cli` from bundled dependencies (#22)

**Decision**: Delete `"youtrack-cli>=0.24.0"` from `[project].dependencies` in `pyproject.toml`
and regenerate `uv.lock`. Keep `youtrack-cli` as a documented, separately-installed prerequisite.

**Rationale**:
- `grep` confirms the code **never imports** `youtrack_cli` — it is named only in docstrings.
  `CliYouTrackSource` invokes the `yt` binary via `subprocess` after `shutil.which("yt")`.
- The install docs already require an authenticated `youtrack-cli` as a prerequisite, and real
  users install it separately (the issue #23 traceback shows `yt` from a pipx venv).
- `youtrack-cli` pulls `docker` which pulls `pywin32`; the native `pywin32` DLLs are what the
  Windows on-access scanner locks, causing `uv`'s `os error 5` rename failure. Removing the dep
  removes the entire chain — one edit fixes the root cause for `uv tool install`, `pip install`,
  and all platforms.

**Alternatives considered**:
- `[tool.uv] override-dependencies = ["pywin32; sys_platform != 'win32'"]` (issue's suggestion 1):
  rejected — `[tool.uv]` overrides are workspace-local config that is **not** embedded in the
  published wheel metadata, so it would not help end users doing `pip install`/`uv tool install`
  from PyPI. It also keeps the unused `docker` dependency.
- Documenting the manual `--override` workaround only (issue's suggestion 3): rejected — leaves
  every Windows user to discover and apply a workaround for a dependency the tool doesn't use.

**Risk / mitigation**: Users who relied on the tool transitively installing `yt` must install it
themselves. This is already the documented contract and is reinforced in FR-008; the existing
`check_available()` error message tells them exactly what to do.

## R2 — Force UTF-8 subprocess I/O (#23)

**Decision**: When spawning `yt`, pass an environment with `PYTHONUTF8=1` and
`PYTHONIOENCODING=utf-8` (merged over `os.environ`), and set `encoding="utf-8"` on the
`subprocess.run(...)` calls that use `text=True`. Apply to **both** call sites in
`CliYouTrackSource` (`check_available` → `yt auth token --show`, and `_fetch_project` →
`yt issues list`).

**Rationale**:
- The crash is in the **child** `yt` process: `rich` writes an emoji to stdout, which Python has
  opened with the Windows console default code page (cp1252), raising `UnicodeEncodeError`.
- `PYTHONUTF8=1` enables Python UTF-8 Mode in the child, forcing its `sys.stdout` to UTF-8;
  `PYTHONIOENCODING=utf-8` is a belt-and-suspenders for interpreters/paths where UTF-8 Mode is
  not honored. Both are standard CPython env knobs, safe and no-op on already-UTF-8 platforms.
- Setting `encoding="utf-8"` on our side ensures we decode the captured bytes as UTF-8 rather
  than the parent's locale preferred encoding (also cp1252 on Windows).

**Alternatives considered**:
- Decode with `errors="replace"` only: rejected as the primary fix — it would silence *our*
  decode step but the child would still crash before writing anything, because the failure is in
  the child's encode, not our decode. (We may still keep robust decoding as defense in depth.)
- Reconfiguring the parent's stdout: irrelevant — the parent captures via a pipe; the failing
  encode is inside the child.

## R3 — Post-subcommand option placement for `--db` / `--ollama-host` / `--config` (#24)

**Decision**: Keep the three options on the top-level group (backward compatible) **and** add them
to each subcommand via a shared `@_common_options` decorator. Resolve the effective config
per-command as `subcommand value → group value → env → TOML → default`, reusing the existing
`Config.load(...)` precedence logic (no change to `config.py`'s public behavior).

**Rationale**:
- `click` binds options to the command that declares them; a group option must appear *before*
  the subcommand. Every README/quickstart example places these options *after* the subcommand,
  so all documented forms currently error with "No such option".
- Declaring the options on each subcommand makes the documented placement work. Keeping them on
  the group too means both placements work, so no existing invocation breaks; when both are
  given, the subcommand-level (more specific) value wins — a deterministic, documented rule
  (Edge Cases / FR-006).
- A single shared decorator avoids repeating three `@click.option` lines per command.

**Alternatives considered**:
- Rewrite all docs to put options *before* the subcommand: rejected — worse ergonomics, and it
  would still surprise users who reasonably expect `analyze --db …` to work.
- Move options *off* the group entirely (subcommand-only): rejected — would break any existing
  pre-subcommand usage for no benefit; keeping both is strictly more compatible.

## R4 — Regenerate lock and validate gate (#22/#009)

**Decision**: Run `uv lock` (or `uv sync`) to regenerate `uv.lock` under the reduced dependency
set, then run the full `just check` gate (ruff, ruff format, ty, pytest). The lock must still
resolve universally across Python 3.11–3.14 (feature 004 invariant).

**Rationale**: Dropping a dependency changes the resolution graph; the committed lock must match
`pyproject.toml`. The gate proves lint/type/test all pass with the new tests added.
