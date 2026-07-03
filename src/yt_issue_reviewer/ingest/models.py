"""Domain models for issues and their links (pure, no I/O)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IssueLink:
    """An existing explicit link between two issues in YouTrack."""

    target_id: str
    link_type: str


@dataclass(frozen=True)
class Issue:
    """A single YouTrack issue under review.

    ``state`` and ``assignee`` are parsed out of YouTrack ``custom_fields`` by the
    source layer; here they are plain values. ``tags`` covers tags and components.
    """

    issue_id: str
    project: str
    number: int
    summary: str
    description: str
    state: str
    assignee: str | None
    reporter: str
    tags: tuple[str, ...] = ()
    created: str = ""
    updated: str = ""
    links: tuple[IssueLink, ...] = field(default_factory=tuple)

    def embed_text(self) -> str:
        """The exact text used for embedding: title then description."""
        body = self.description.strip()
        if body:
            return f"{self.summary}\n\n{body}"
        return self.summary

    def content_hash(self) -> str:
        """SHA-256 of the embedded text — the cache-invalidation key component."""
        return hashlib.sha256(self.embed_text().encode("utf-8")).hexdigest()
