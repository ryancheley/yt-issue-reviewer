"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yt_issue_reviewer.ingest.models import Issue, IssueLink

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


def load_fixture_issues(name: str = "issues_small.json") -> list[Issue]:
    """Load a fixture corpus of issues (with links) from tests/fixtures/."""
    data = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    issues: list[Issue] = []
    for raw in data:
        links = tuple(
            IssueLink(target_id=link["target_id"], link_type=link["link_type"])
            for link in raw.get("links", [])
        )
        issues.append(
            Issue(
                issue_id=raw["issue_id"],
                project=raw["project"],
                number=raw.get("number", 0),
                summary=raw["summary"],
                description=raw.get("description", ""),
                state=raw.get("state", ""),
                assignee=raw.get("assignee"),
                reporter=raw.get("reporter", ""),
                tags=tuple(raw.get("tags", [])),
                created=raw.get("created", ""),
                updated=raw.get("updated", ""),
                links=links,
            )
        )
    return issues


@pytest.fixture
def fixture_issues() -> list[Issue]:
    return load_fixture_issues()
