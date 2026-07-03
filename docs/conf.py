"""Sphinx configuration for the yt-issue-reviewer documentation.

The docs are authored in Markdown and rendered with MyST-Parser. See
``docs/requirements.txt`` for the build dependencies and ``.readthedocs.yaml``
for the Read the Docs build.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

# -- Project information -----------------------------------------------------

_pyproject = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text())

project = "yt-issue-reviewer"
author = "Ryan Cheley"
copyright = "2026, Ryan Cheley"  # noqa: A001 - Sphinx requires this exact name
release = str(_pyproject["project"]["version"])
version = release

# -- General configuration ---------------------------------------------------

extensions = ["myst_parser"]

# Recognize GitHub-style admonitions/anchors; colon_fence lets directives use :::.
myst_enable_extensions = ["colon_fence", "linkify"]
myst_heading_anchors = 3

# Non-doc files under docs/ that should not be built as pages.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "requirements.txt",
    "yt-cli-upstream-candidates.md",
]

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = "yt-issue-reviewer"
