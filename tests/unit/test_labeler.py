"""Labeler persistence + unreachable-degradation behavior."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.config import Config
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource
from yt_issue_reviewer.llm.labeler import FakeLabeler
from yt_issue_reviewer.pipeline import run_analysis
from yt_issue_reviewer.store.repository import Repository


def _run(tmp_path: Path, labeler) -> tuple[Repository, str]:
    repo = Repository.open(tmp_path / "l.db")
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
        labeler=labeler,
    )
    return repo, result.run_id


def test_labels_persist_marked_generated(tmp_path: Path) -> None:
    repo, run_id = _run(tmp_path, FakeLabeler())
    groups = repo.load_groups(run_id)
    assert groups
    assert all(g["label"] and g["label_is_generated"] for g in groups)
    repo.close()


def test_unreachable_label_model_degrades_to_no_label(tmp_path: Path) -> None:
    repo = Repository.open(tmp_path / "l2.db")
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
        labeler=FakeLabeler(available=False),
    )
    assert any("label" in w.lower() for w in result.warnings)
    groups = repo.load_groups(result.run_id)
    assert all(g["label"] is None for g in groups)
    repo.close()
