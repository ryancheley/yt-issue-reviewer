# Quickstart / Validation: `--state open` returns all genuinely-open issues

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_youtrack_subprocess.py -q
uv run pytest -q            # full suite: no regressions (SC-004)
```

Expected: the new regression test (a stubbed `yt` that returns a `State=New` issue only
when no `--state` argument is passed) confirms `fetch_issues([...], state="open")` returns
the `New` issue (SC-001). Also asserts `_fetch_project`'s command omits `--state Open`.

## Manual validation (operator, against live YouTrack)

Project THD has 2 issues, both `State=New`:

```bash
uv run yt-issue-reviewer analyze --project THD --state open \
  --ollama-host http://127.0.0.1:11434 --db ./yir.db
```

Expected **after the fix**: `2 issues` (SC-002). Before the fix it reported `0 issues`.
`--state all` also reports 2 (unchanged).

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
