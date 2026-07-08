# Quickstart / Validation: Fetch issues in bounded chunks

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_youtrack_subprocess.py -q
uv run pytest -q            # full suite: no regressions (SC-005)
```

Expected: new tests (stubbing `subprocess.run` with synthetic ascending-`created` pages)
confirm the loop assembles multiple pages into the complete set (SC-001), stops on a short
page, de-duplicates the boundary overlap so no issue repeats (SC-004), keeps each request
bounded to `PAGE` (SC-002), and raises `YouTrackUnavailable` on a same-date stall.

## Manual validation

**On a normal/fast connection** (small project fits in one page — behavior unchanged, SC-003):

```bash
uv run yt-issue-reviewer analyze --project NGDEV --state all \
  --ollama-host http://127.0.0.1:11434 --db ./ngdev.db
# ingested count unchanged from before (e.g. 178)
```

**On the gated/remote instance** (the repro — the whole point, SC-001):

```bash
uv run yt-issue-reviewer analyze --project NGDEV --state all --db ./yir.db
```

Expected **after the fix**: the full project is ingested via several ~200-issue requests, each
finishing well under the ~20s gateway limit — instead of `0 issues`. Confirm the ingested count
matches the project's real total (e.g. `yt issues list --project-id NGDEV --top 250 | ...`).

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
