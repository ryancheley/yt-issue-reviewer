# Quickstart / Validation: Repair a backslash immediately before a newline

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_load_json_issues.py -q
uv run pytest -q            # full suite: no regressions (SC-004)
```

Expected: the new test confirms `_load_json_issues` parses a payload with a backslash immediately
before a raw newline inside a `description` (SC-001), and the existing #48 / valid-escape /
control-char / non-JSON tests still pass (SC-002/003).

## Manual reproduction (before the fix)

```python
import json
bad = '[{"d": "line ends with backslash\\\n next line"}]'  # backslash + raw newline
json.loads(bad, strict=False)   # JSONDecodeError: Invalid \escape  (issue #57)
```

After the fix, `_load_json_issues(bad)` returns the parsed issue list.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
