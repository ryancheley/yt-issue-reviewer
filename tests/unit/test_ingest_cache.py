"""Ingest cache reuse: unchanged issues keep their fetched_at (staleness visible)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource
from yt_issue_reviewer.pipeline import ingest_issues
from yt_issue_reviewer.store.repository import Repository


def test_unchanged_issue_keeps_fetched_at(tmp_path: Path) -> None:
    issues = load_fixture_issues()
    repo = Repository.open(tmp_path / "c.db")

    run1 = repo.create_run(
        projects=["PROJ"],
        state_filter="all",
        date_from=None,
        date_to=None,
        min_score=0.6,
        embedding_model=None,
        weight_semantic=0.7,
        weight_structural={},
        label_model=None,
    )
    ingest_issues(
        FakeYouTrackSource(issues),
        repo,
        run1,
        projects=["PROJ"],
        state="all",
        since=None,
        until=None,
        refresh=False,
    )
    first_fetch = repo.fetched_at("PROJ-1")
    assert first_fetch is not None

    # Second run, unchanged content -> fetched_at preserved (reused, not re-stamped).
    run2 = repo.create_run(
        projects=["PROJ"],
        state_filter="all",
        date_from=None,
        date_to=None,
        min_score=0.6,
        embedding_model=None,
        weight_semantic=0.7,
        weight_structural={},
        label_model=None,
    )
    ingest_issues(
        FakeYouTrackSource(issues),
        repo,
        run2,
        projects=["PROJ"],
        state="all",
        since=None,
        until=None,
        refresh=False,
    )
    assert repo.fetched_at("PROJ-1") == first_fetch
    repo.close()


def test_changed_issue_restamps_fetched_at(tmp_path: Path) -> None:
    issues = load_fixture_issues()
    repo = Repository.open(tmp_path / "c2.db")
    run1 = repo.create_run(
        projects=["PROJ"],
        state_filter="all",
        date_from=None,
        date_to=None,
        min_score=0.6,
        embedding_model=None,
        weight_semantic=0.7,
        weight_structural={},
        label_model=None,
    )
    ingest_issues(
        FakeYouTrackSource(issues),
        repo,
        run1,
        projects=["PROJ"],
        state="all",
        since=None,
        until=None,
        refresh=False,
    )
    original = repo.cached_content_hash("PROJ-1")

    changed = [
        replace(i, summary=i.summary + " EDIT") if i.issue_id == "PROJ-1" else i for i in issues
    ]
    run2 = repo.create_run(
        projects=["PROJ"],
        state_filter="all",
        date_from=None,
        date_to=None,
        min_score=0.6,
        embedding_model=None,
        weight_semantic=0.7,
        weight_structural={},
        label_model=None,
    )
    ingest_issues(
        FakeYouTrackSource(changed),
        repo,
        run2,
        projects=["PROJ"],
        state="all",
        since=None,
        until=None,
        refresh=False,
    )
    assert repo.cached_content_hash("PROJ-1") != original
    repo.close()
