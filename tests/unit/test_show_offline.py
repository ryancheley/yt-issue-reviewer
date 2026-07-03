"""`show` must reconstruct a run from the DB with no YouTrack/Ollama access."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.config import Config
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource
from yt_issue_reviewer.pipeline import run_analysis
from yt_issue_reviewer.store.repository import Repository


def test_stored_run_reloads_without_services(tmp_path: Path) -> None:
    db = tmp_path / "show.db"
    repo = Repository.open(db)
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
    )
    run_id = result.run_id
    repo.close()

    # Reopen a fresh Repository (no source/embedder in scope at all).
    repo2 = Repository.open(db)
    groups = repo2.load_groups(run_id)
    assert groups
    for g in groups:
        assert g["members"]
        assert g["evidence"]  # evidence survived the round-trip
    # Members resolve to summaries purely from the DB.
    member_ids = [m for g in groups for m in g["members"]]
    summaries = repo2.issue_summaries(member_ids)
    assert all(mid in summaries for mid in member_ids)
    repo2.close()
