"""End-to-end analysis with fakes over the fixture corpus."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.config import Config
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder
from yt_issue_reviewer.ingest.youtrack import FakeYouTrackSource
from yt_issue_reviewer.pipeline import run_analysis
from yt_issue_reviewer.store.repository import Repository


def _analyze(tmp_path: Path, **kwargs):
    repo = Repository.open(tmp_path / "e2e.db")
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
        **kwargs,
    )
    return repo, result


def test_related_issues_grouped_with_evidence(tmp_path: Path) -> None:
    repo, result = _analyze(tmp_path)
    assert result.issue_count == 5
    assert not result.degraded

    # The known login-bug duplicates should land in the same group.
    member_sets = [set(g["members"]) for g in result.groups]
    assert any({"PROJ-1", "PROJ-2"} <= s for s in member_sets)

    # Every reported group carries evidence (Constitution IV / SC-004).
    for g in result.groups:
        assert g["evidence"], f"group {g['group_id']} has no evidence"
    repo.close()


def test_existing_link_excluded_from_findings(tmp_path: Path) -> None:
    repo, result = _analyze(tmp_path)
    # PROJ-3 <-> PROJ-4 are explicitly linked -> must not appear as a new pair.
    for p in result.pairs:
        assert frozenset((p.issue_a, p.issue_b)) != frozenset(("PROJ-3", "PROJ-4"))
    repo.close()


def test_degraded_mode_when_ollama_unavailable(tmp_path: Path) -> None:
    repo = Repository.open(tmp_path / "degraded.db")
    result = run_analysis(
        source=FakeYouTrackSource(load_fixture_issues()),
        embedder=FakeEmbedder(dim=128, available=False),
        repo=repo,
        config=Config(min_score=0.3),
        projects=["PROJ"],
        state="all",
    )
    assert result.degraded
    assert any("structural-only" in w.lower() for w in result.warnings)
    info = repo.get_run(result.run_id)
    assert info is not None and info.degraded_structural_only is True
    # Structural-only still finds the tag+reporter-related login pair.
    assert any({"PROJ-1", "PROJ-2"} <= set(g["members"]) for g in result.groups)
    repo.close()
