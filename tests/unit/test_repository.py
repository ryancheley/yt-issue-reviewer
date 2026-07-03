"""Foundational schema + repository round-trip tests."""

from __future__ import annotations

from pathlib import Path

from yt_issue_reviewer.store.repository import Repository


def _open(tmp_path: Path) -> Repository:
    return Repository.open(tmp_path / "test.db")


def test_create_and_read_run(tmp_path: Path) -> None:
    repo = _open(tmp_path)
    run_id = repo.create_run(
        projects=["PROJ"],
        state_filter="open",
        date_from=None,
        date_to=None,
        min_score=0.6,
        embedding_model="nomic-embed-text",
        weight_semantic=0.7,
        weight_structural={"shared_tags": 0.5},
        label_model=None,
    )
    assert run_id
    assert repo.latest_run_id() == run_id

    info = repo.get_run(run_id)
    assert info is not None
    assert info.projects == ["PROJ"]
    assert info.state_filter == "open"
    assert info.min_score == 0.6
    assert info.finished_at is None
    assert info.degraded_structural_only is False

    repo.finish_run(run_id, issue_count=5, degraded_structural_only=True)
    info2 = repo.get_run(run_id)
    assert info2 is not None
    assert info2.finished_at is not None
    assert info2.issue_count == 5
    assert info2.degraded_structural_only is True
    repo.close()


def test_schema_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "idem.db"
    Repository.open(db).close()
    # Opening again must not error (CREATE TABLE IF NOT EXISTS).
    repo = Repository.open(db)
    assert repo.list_runs() == []
    repo.close()
