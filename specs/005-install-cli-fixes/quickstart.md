# Quickstart / Validation Guide: Cross-Platform Install and CLI Robustness Fixes

Runnable checks that prove each fix. Run from the repo root.

## Prerequisites

- `uv` installed.
- For the live commands only: an authenticated `yt` (youtrack-cli) on PATH and a reachable Ollama.
  The automated checks below are all **offline** and need neither.

## 1. Dependency no longer pulls in pywin32/docker (#22)

```bash
uv lock          # regenerate after removing youtrack-cli from pyproject.toml
uv tree          # inspect the resolved dependency graph
```

**Expected**: `youtrack-cli`, `docker`, and `pywin32` do **not** appear in the tree.
`pyproject.toml` `[project].dependencies` no longer lists `youtrack-cli`.

## 2. UTF-8 subprocess env (#23)

Offline unit test asserts the `yt` subprocess is invoked with a UTF-8 I/O environment
(`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`) and `encoding="utf-8"`:

```bash
uv run pytest tests/unit/test_youtrack_subprocess.py -q
```

**Expected**: passes. (Manual Windows check: on a cp1252 console, `ingest --project P` completes
even when `yt` prints an emoji, instead of raising `UnicodeEncodeError`.)

## 3. Post-subcommand option placement (#24)

Offline unit test drives the CLI with options placed after the subcommand:

```bash
uv run pytest tests/unit/test_cli_options.py -q
```

**Expected**: passes — `analyze/doctor/show … --db … --ollama-host …` are accepted, and
`--db A … --db B` resolves to `B`.

Manual smoke (no network needed — it fails at connectivity, not option parsing):

```bash
uv run yt-issue-reviewer show --db ./yir.db          # accepted, not "No such option"
uv run yt-issue-reviewer doctor --ollama-host http://127.0.0.1:11434   # accepted
```

## 4. Full gate

```bash
just check       # ruff, ruff format, ty, pytest, zizmor — must be green
```

**Expected**: all green. Analysis output for an equivalent run is unchanged (FR-010).
