# Quickstart / Validation: `--version` flag

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_cli_options.py -q
uv run pytest -q            # full suite: no regressions (SC-004)
```

Expected: new tests confirm `--version` and `-V` exit 0 and print the version equal to
`yt_issue_reviewer.__version__` (SC-001/002/003).

## Manual validation

```bash
uv run yt-issue-reviewer --version     # -> "yt-issue-reviewer, version X.Y.Z", exit 0
uv run yt-issue-reviewer -V            # same
uv run yt-issue-reviewer --help        # unchanged; --version now listed
uv run yt-issue-reviewer analyze --help  # subcommands unaffected (SC-004)
```

The printed `X.Y.Z` must match the version in `pyproject.toml` / installed metadata.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
