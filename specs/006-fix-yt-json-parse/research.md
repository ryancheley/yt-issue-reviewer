# Phase 0 Research: Graceful handling of non-JSON `yt` output

## Decision 1 — Root cause of `Expecting value: line 1 column 1 (char 0)`

**Decision**: Treat a leading UTF-8 BOM as the primary cause and strip it before parsing.

**Rationale**: That exact `JSONDecodeError` message (position `char 0`) is the canonical
signature of a byte-order mark (`﻿`) at the start of the string. `json.loads` rejects a
leading BOM. Crucially, Python's `str.strip()` does **not** remove `﻿` (it is not treated
as whitespace), so the current `stdout.strip()` leaves it in place. Windows toolchains commonly
emit BOM-prefixed UTF-8, matching the issue #29 environment.

**Alternatives considered**:
- Decode subprocess bytes with `utf-8-sig` instead: rejected — the subprocess is already read
  as text via `encoding="utf-8"` in `youtrack.py`, and re-plumbing the decode is a larger,
  riskier change than a one-line strip at the parse site. Stripping at the shared parse point
  also protects against a BOM arriving from any future stdout path.

## Decision 2 — How to surface non-JSON output

**Decision**: Wrap `json.loads` in `try/except json.JSONDecodeError` and re-raise the existing
`YouTrackUnavailable` with a truncated excerpt of the offending output.

**Rationale**: `YouTrackUnavailable` is already caught in all four CLI subcommands
(`cli.py:96/173/242/317`) and rendered as a clean operator-facing message — no traceback. Every
other subprocess failure in this module already raises it, so this is consistent. Including a
short excerpt of the actual stdout lets the operator diagnose the real cause (wrong `yt`
version, unsupported `--format json`, an auth/banner line, etc.).

**Alternatives considered**:
- New dedicated exception type: rejected (YAGNI) — no caller distinguishes it from other
  YouTrack failures; a new type adds a catch site everywhere for zero benefit.
- Silently return `[]` on bad JSON: rejected — hides real failures and would make "0 related
  issues" indistinguishable from "yt is broken", violating Transparency (Principle IV).

## Decision 3 — Excerpt length

**Decision**: First ~200 characters of the stripped output.

**Rationale**: Enough to recognize a banner/table/error line without dumping a large payload
into the terminal. A fixed small cap keeps the message readable.
