# yt-cli Upstream Contribution Candidates

Per Constitution Principle III, when `youtrack_cli` lacks a capability we need, we record
it here as a candidate upstream contribution rather than working around it with a parallel
REST client. These are drawn from research.md (R1).

## 1. Stable, documented programmatic API

`youtrack_cli/__init__.py` currently exports only `__version__`. The internal
`IssueManager` / `AuthManager` classes are undocumented, async, and return dict envelopes
that may change between 0.x releases. A documented, stable, typed client facade would let
downstream tools integrate in-process instead of shelling out.

**Our current workaround**: we invoke the `yt` CLI as a subprocess with JSON output,
behind our own `YouTrackSource` adapter. This is the stable contract today.

## 2. Bulk "dump issues as JSON" for a project/state/date range

A first-class command optimized for exporting all issues (with `custom_fields`, `links`,
`tags`) as JSON for a scope would simplify bulk ingest. We currently parse
`yt issues list --format json` per project and normalize fields client-side (notably
extracting `state`/`assignee` from `custom_fields`, and epoch-millis timestamps).

## How to file

Open issues on [`ryancheley/yt-cli`](https://github.com/ryancheley/yt-cli) referencing this
document. Keep this file updated as the integration evolves.
