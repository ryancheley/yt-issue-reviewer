# Quickstart / Validation: Fetch every issue in a project

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_youtrack_subprocess.py -q
uv run pytest -q            # full suite: no regressions (SC-003)
```

Expected: the new regression test asserts the issued `yt issues list` command includes
`--all` (stub `subprocess.run`, capture the command).

## Manual validation (operator, against a large project)

On a project with more than 100 issues (e.g. the Jira-imported one on the remote instance):

```bash
# Confirm the raw counts differ:
yt issues list --project-id PROJ --format json | jq 'length'          # 100 (old cap)
yt issues list --project-id PROJ --format json --all | jq 'length'    # full count

# Confirm analyze now ingests the full set:
uv run yt-issue-reviewer analyze --project PROJ --state all \
  --ollama-host http://<host>:11434 --db ./yir.db
```

Expected **after the fix**: the ingested-issue count equals the `--all` count (SC-001), not 100.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
