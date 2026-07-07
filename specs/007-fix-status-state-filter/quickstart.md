# Quickstart / Validation: Respect `Status` custom-field state

## Prerequisites

- `uv sync` (dev dependencies installed)

## Automated validation

```bash
uv run pytest tests/unit/test_youtrack_source.py tests/unit/test_ingest_filters.py -q
uv run pytest -q            # full suite: no regressions (SC-003)
```

Expected: the new regression test (a `CliYouTrackSource` whose stubbed `yt` returns issues
with a `Status` custom field of `Done`, called with `state="open"`) returns zero `Done`
issues (SC-001). All existing tests still pass.

## Manual validation (operator, optional)

Against a real `Status`-based project (e.g. the repro NGDEV: 15 `Done`, 3 `In Progress`,
3 `Waiting`):

```bash
uv run yt-issue-reviewer analyze --project NGDEV --state open --min-score 0.6 --db ./yir.db
```

Expected: exactly 6 issues ingested — the 15 `Done` are excluded (SC-002). With
`--state all`, all 21 are ingested.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest
```
