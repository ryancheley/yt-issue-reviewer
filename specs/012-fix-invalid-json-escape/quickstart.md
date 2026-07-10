# Quickstart / Validation: Tolerate invalid backslash escapes

## Prerequisites

- `uv sync`

## Automated validation

```bash
uv run pytest tests/unit/test_load_json_issues.py -q
uv run pytest -q            # full suite: no regressions (SC-004)
```

Expected: new tests confirm that
- a payload with an unescaped backslash inside a `description` (`C:\Users`, `\d+`) parses
  instead of raising (SC-001),
- valid escapes (`\n \t \" \\ \/ \uXXXX`) parse to the same values as before (SC-002),
- a genuinely non-JSON banner still raises `YouTrackUnavailable` (SC-003).

## Manual reproduction (before the fix)

```python
import json
bad = r'[{"idReadable":"NG-1","description":"path C:\Users\ryan and regex \d+ here"}]'
json.loads(bad, strict=False)   # JSONDecodeError: Invalid \escape  (this is issue #48)
```

After the fix, `_load_json_issues(bad)` returns the parsed issue list.

## Lint / type gate (before pushing)

```bash
just check    # == the CI gate: ruff + ty + pytest + zizmor
```
