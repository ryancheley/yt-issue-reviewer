# Research: Repair a backslash immediately before a newline

Reproduced and the fix verified locally before speccing.

## Decision: Add `re.DOTALL` to the `_escape_stray_backslashes` regex

- **Decision**: Change the repair to
  `re.sub(r'\\(["\\/bfnrtu])|\\(.)', <repl>, text, flags=re.DOTALL)`.
- **Rationale**: The second alternative `\\(.)` matches an invalid escape `\X` and doubles the
  backslash. Without `re.DOTALL`, `.` does not match a newline, so `\<newline>` (a literal
  backslash at a line end, with `yt` emitting a raw newline) is not repaired and
  `json.loads(strict=False)` still raises `Invalid \escape`. `re.DOTALL` makes `.` match the
  newline too, so `\<newline>` → `\\<newline>` (escaped backslash + raw newline), and `strict=False`
  already tolerates the raw newline.
- **Verified locally**:
  - `[{"d": "line ends with backslash\<newline> next line"}]` → fails before; parses after.
  - Valid escapes (`\n \t \" \\ \/ \uXXXX`) parse identically to plain `json.loads` (the first
    alternative is a character class, unaffected by `DOTALL`).
  - The #48 cases (`C:\Users`, `\d+`) still parse.
- **Why DOTALL is safe**: `re.DOTALL` only changes what `.` matches. The first alternative
  (`["\\/bfnrtu]`) is a fixed character class and is untouched, so valid escapes are still kept
  verbatim; only the invalid-escape branch gains newline coverage.
- **Alternatives considered**:
  - Replace `.` with `[\s\S]` — equivalent effect; `flags=re.DOTALL` is the smaller, clearer change.
  - A broader JSON-repair library — rejected (no new dependency; VI. Simplicity).

## Related / out of scope

- Same `Invalid \escape` error class as #48 (BOM #29, control chars #34 are the sibling classes),
  all hardened in the one shared `_load_json_issues` fallback.
- A backslash at the very end of the payload (no following character at all) is not this bug and
  is out of scope; the reported failure is specifically backslash-before-newline.
- Upstream: `yt` emitting invalid JSON is the true source; a `yt-cli` ticket about that is separate.
