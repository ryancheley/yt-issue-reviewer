"""Shared error types for external-service boundaries."""

from __future__ import annotations


class YouTrackUnavailable(RuntimeError):
    """Raised when the ``yt`` CLI is missing, unauthenticated, or fails."""


class OllamaUnavailable(RuntimeError):
    """Raised when the configured Ollama host is unreachable or a model is absent.

    The ``analyze`` flow catches this to degrade to structural-only scoring or skip
    labeling — it MUST NEVER fall back to any third-party hosted service.
    """
