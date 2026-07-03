"""Contract tests for YouTrackSource via the fake, plus the parse_issue mapper."""

from __future__ import annotations

import pytest

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.errors import YouTrackUnavailable
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource, parse_issue


def test_fetch_respects_project_filter() -> None:
    src = FakeYouTrackSource(load_fixture_issues())
    issues = src.fetch_issues(["PROJ"], state="all")
    assert {i.issue_id for i in issues} == {"PROJ-1", "PROJ-2", "PROJ-3", "PROJ-4", "PROJ-5"}
    assert src.fetch_issues(["OTHER"], state="all") == []


def test_links_are_present() -> None:
    src = FakeYouTrackSource(load_fixture_issues())
    by_id = {i.issue_id: i for i in src.fetch_issues(["PROJ"], state="all")}
    assert by_id["PROJ-4"].links[0].target_id == "PROJ-3"


def test_check_available_raises_when_unavailable() -> None:
    src = FakeYouTrackSource([], available=False)
    with pytest.raises(YouTrackUnavailable):
        src.check_available()


def test_parse_issue_extracts_state_and_assignee_from_custom_fields() -> None:
    raw = {
        "idReadable": "ABC-9",
        "summary": "Broken thing",
        "description": "details",
        "project": {"shortName": "ABC"},
        "reporter": {"login": "bob"},
        "created": 1735689600000,
        "customFields": [
            {"name": "State", "value": {"name": "In Progress"}},
            {"name": "Assignee", "value": {"login": "alice"}},
        ],
        "tags": [{"name": "backend"}],
    }
    issue = parse_issue(raw)
    assert issue.issue_id == "ABC-9"
    assert issue.project == "ABC"
    assert issue.state == "In Progress"
    assert issue.assignee == "alice"
    assert issue.reporter == "bob"
    assert issue.tags == ("backend",)
    assert issue.created.startswith("2025-01-01")
