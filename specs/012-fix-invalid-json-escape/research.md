# Research: Tolerate invalid backslash escapes in `yt` JSON output

Reproduced and verified locally before speccing.

## Decision: Repair stray backslashes on a JSONDecodeError fallback, then retry

- **Decision**: In `_load_json_issues`, wrap the existing `json.loads(stdout, strict=False)` so
  that on `JSONDecodeError` it calls `_escape_stray_backslashes(stdout)` and retries
  `json.loads(..., strict=False)` once. If the retry also raises, re-raise the existing
  `YouTrackUnavailable` (truncated excerpt) as today.
- **`_escape_stray_backslashes`**: a single `re.sub` with a callback:
  `re.sub(r'\\(["\\/bfnrtu])|\\(.)', lambda m: m.group(0) if m.group(1) else "\\\\" + m.group(2), text)`.
  The first alternative matches a **valid** escape (`\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`,
  `\t`, `\u…`) and is returned unchanged; the second matches any other `\X` and doubles the
  backslash (`\X` → `\\X`), making it a literal backslash. Consuming valid pairs first is what
  prevents corrupting an already-escaped `\\`.
- **Rationale**: `strict=False` only disables the control-character check; a backslash followed
  by a non-escape character (Windows path `C:\Users`, regex `\d`, `\U`, `\ `) still raises
  `Invalid \escape`. Doubling only the invalid backslashes makes the payload parseable while
  leaving valid escapes intact.
- **Verified locally**:
  - `[{"idReadable":"NG-1","description":"path C:\Users\ryan and regex \d+ here"}]` →
    `strict=False` raises `Invalid \escape`; after repair it parses.
  - A payload with `\t \\ \" \/ A` parses to the **same** values with and without the
    repair (valid escapes preserved).

## Decision: Fallback only — do not repair the happy path

- **Decision**: Run the repair only inside the `except JSONDecodeError` branch, not on every
  payload.
- **Rationale**: Keeps well-formed JSON (the overwhelming common case) on the untouched fast
  path, and confines the heuristic to genuinely-broken input. Lower risk, no measurable cost.
- **Alternatives considered**:
  - Always pre-processing every payload — rejected: runs a regex over large valid payloads for
    no benefit and risks surprising edits.
  - A third-party lenient/JSON-repair library — rejected: violates the no-new-dependency
    preference (VI); a few lines of stdlib `re` suffice.
  - Perfectly reconstructing intended text (e.g. distinguishing an intended `\r` in a path from
    a real carriage return) — out of scope and impossible without `yt`'s intent; parseability
    is the goal. Note `\r`/`\t`/`\n` are *valid* escapes and were already interpreted as control
    chars by `strict=False`, so this fix introduces no new behavior for them.

## Related / out of scope

- Same failure class as #29 (BOM), #34 (control chars): `yt` emitting malformed JSON, hardened
  in the one shared `_load_json_issues` so all callers/subcommands benefit.
- Upstream: `youtrack-cli` 0.24.4 (PR #731) parses API responses leniently, which may prevent
  this at the source — but the tool must not depend on the operator's `yt` version.
- The reporter's traceback is from a pre-0.3.4 build (old `_fetch_project(project, state)`
  signature); they should also upgrade. Not a code change here.
