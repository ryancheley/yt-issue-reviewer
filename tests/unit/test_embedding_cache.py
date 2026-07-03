"""Embedding cache hit/miss keyed on (issue_id, content_hash, model)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder
from yt_issue_reviewer.pipeline import embed_issues
from yt_issue_reviewer.store.repository import Repository


class CountingEmbedder(FakeEmbedder):
    def __init__(self) -> None:
        super().__init__(dim=32)
        self.calls: list[int] = []

    def embed_batch(self, texts):  # type: ignore[override]
        self.calls.append(len(texts))
        return super().embed_batch(texts)


def test_second_run_is_full_cache_hit(tmp_path: Path) -> None:
    issues = load_fixture_issues()
    repo = Repository.open(tmp_path / "e.db")
    emb = CountingEmbedder()

    embed_issues(emb, repo, issues)
    assert emb.calls == [len(issues)]  # all embedded first time

    embed_issues(emb, repo, issues)
    assert emb.calls == [len(issues)]  # no new embed calls -> full cache hit
    repo.close()


def test_changed_issue_reembeds_only_that_issue(tmp_path: Path) -> None:
    issues = load_fixture_issues()
    repo = Repository.open(tmp_path / "e2.db")
    emb = CountingEmbedder()
    embed_issues(emb, repo, issues)

    changed = [
        replace(i, description=i.description + " NEW DETAIL") if i.issue_id == "PROJ-1" else i
        for i in issues
    ]
    embed_issues(emb, repo, changed)
    assert emb.calls == [len(issues), 1]  # only the changed issue re-embedded
    repo.close()
