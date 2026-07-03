"""Scope-filtering semantics (project / state / date range)."""

from __future__ import annotations

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource


def _src() -> FakeYouTrackSource:
    return FakeYouTrackSource(load_fixture_issues())


def test_state_open_excludes_closed() -> None:
    open_ids = {i.issue_id for i in _src().fetch_issues(["PROJ"], state="open")}
    assert "PROJ-5" not in open_ids  # PROJ-5 is Closed
    all_ids = {i.issue_id for i in _src().fetch_issues(["PROJ"], state="all")}
    assert "PROJ-5" in all_ids


def test_date_range_filters_by_created() -> None:
    issues = _src().fetch_issues(["PROJ"], state="all", since="2026-06-05", until="2026-06-30")
    ids = {i.issue_id for i in issues}
    # PROJ-1/2 created early June, PROJ-5 in May -> excluded; PROJ-3/4 in range.
    assert ids == {"PROJ-3", "PROJ-4"}
