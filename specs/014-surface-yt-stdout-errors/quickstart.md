# Quickstart / Validation: Surface `yt`'s stdout in failure messages

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_youtrack_subprocess.py -q
uv run pytest -q            # full suite: no regressions (SC-003)
```

Expected: new tests confirm that when a stubbed `yt` exits non-zero with the reason on **stdout**
(empty stderr), the raised `YouTrackUnavailable` message contains that reason (SC-001); and that a
stderr-only failure still includes the stderr text (SC-002).

## Manual reproduction (the real-world case)

On youtrack-cli 0.24.5 with stale/invalid auth (before `yt auth login`):

```bash
uv run yt-issue-reviewer analyze --project NGDEV --state all --db ./yir.db
```

Expected **after the fix**: the error message includes `❌ Not authenticated` (from `yt`'s stdout),
not just `Error: Failed to list issues` — so the operator knows to run `yt auth login`.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
