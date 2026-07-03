"""Labels are presentation-only: they never change groups or scores."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.config import Config
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource
from yt_issue_reviewer.llm.labeler import FakeLabeler
from yt_issue_reviewer.pipeline import run_analysis
from yt_issue_reviewer.store.repository import Repository


def _groups_signature(tmp_path: Path, name: str, *, labeler) -> list[tuple]:
    repo = Repository.open(tmp_path / name)
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
        labeler=labeler,
    )
    sig = [(tuple(g["members"]), round(g["group_score"], 6)) for g in result.groups]
    repo.close()
    return sig


def test_labeling_does_not_change_groups_or_scores(tmp_path: Path) -> None:
    without = _groups_signature(tmp_path, "no_label.db", labeler=None)
    with_labels = _groups_signature(tmp_path, "label.db", labeler=FakeLabeler())
    assert without == with_labels
    assert without  # sanity: there ARE groups to compare
