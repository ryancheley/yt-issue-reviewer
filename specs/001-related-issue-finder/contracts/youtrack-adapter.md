# Interface Contract: `YouTrackSource`

The single seam through which the tool reads YouTrack (Constitution III). The production
implementation shells out to the `yt` CLI with JSON output; a fake backs tests
(Constitution VII). **Read-only** — no method mutates YouTrack (Constitution II).

## Interface

```python
# ingest/youtrack.py
from typing import Protocol
from .models import Issue

class YouTrackSource(Protocol):
    def fetch_issues(
        self,
        projects: list[str],
        state: str = "open",          # "open" | "all"
        since: str | None = None,     # ISO-8601 date
        until: str | None = None,     # ISO-8601 date
    ) -> list[Issue]:
        """Return issues matching the scope, including parsed links.

        MUST be read-only. MUST include existing issue links so the analysis
        layer can exclude already-linked pairs from new findings (FR-007).
        """
        ...

    def check_available(self) -> None:
        """Raise YouTrackUnavailable if the `yt` CLI is missing or not
        authenticated. Used by `doctor` and pre-flight of `analyze`."""
        ...
```

## `Issue` shape (`ingest/models.py`)

```python
@dataclass(frozen=True)
class IssueLink:
    target_id: str
    link_type: str          # e.g. "duplicates", "relates to"

@dataclass(frozen=True)
class Issue:
    issue_id: str           # "PROJ-123"
    project: str
    number: int
    summary: str            # title (YouTrack `summary`)
    description: str        # may be ""
    state: str              # parsed from custom_fields
    assignee: str | None    # parsed from custom_fields
    reporter: str
    tags: tuple[str, ...]   # tags + components
    created: str            # ISO-8601 UTC
    updated: str            # ISO-8601 UTC
    links: tuple[IssueLink, ...]
```

## Production implementation: `CliYouTrackSource`

- Invokes `yt issues list` / `yt issues search` as a subprocess with JSON output,
  scoping by project/state and (client-side if needed) date range.
- Parses `custom_fields` to populate `state` and `assignee` (these are not top-level in
  YouTrack — see research R1).
- Reuses existing auth from the shared `youtrack-cli` config / env vars — no credential
  handling in this tool.
- Pins the `youtrack-cli` version; treats any missing capability as an upstream
  contribution candidate, never as license to call the REST API directly.
- Normalizes timestamps to ISO-8601 UTC.

**Errors**: raises `YouTrackUnavailable` (CLI missing / auth failure / nonzero exit) —
maps to CLI exit code 2. Never partially writes analysis results on this failure.

## Test fake: `FakeYouTrackSource`

- Constructed with an in-memory list of `Issue` objects (from `tests/fixtures/`).
- `fetch_issues` applies the same project/state/date filtering semantics in pure Python so
  filter behavior (US2) is testable without a network.
- `check_available` configurable to raise, so degraded/failure paths are testable.

## Contract tests (must hold for any implementation)

1. Returned issues respect the `projects`, `state`, `since`, `until` filters.
2. `state` and `assignee` are populated (not left empty when present in source data).
3. `links` includes every existing YouTrack link for returned issues.
4. No method performs or attempts a write.
5. `check_available` raises `YouTrackUnavailable` when the source is misconfigured.
