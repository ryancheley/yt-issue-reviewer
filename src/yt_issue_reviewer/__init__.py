"""Related Issue Finder — find related YouTrack issues via local embeddings + signals."""

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth: the version declared in pyproject.toml, read from the
    # installed distribution metadata. Avoids hardcoding the version in two places.
    __version__ = version("yt-issue-reviewer")
except PackageNotFoundError:  # pragma: no cover - running from a non-installed checkout
    __version__ = "0.0.0"
