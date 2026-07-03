"""Union-find grouping behavior."""

from __future__ import annotations

from yt_issue_reviewer.analyze.clustering import group_pairs
from yt_issue_reviewer.analyze.scoring import ScoredPair


def _pair(a: str, b: str, score: float) -> ScoredPair:
    return ScoredPair(
        a, b, semantic_score=score, structural_score=score, combined_score=score, evidence=[]
    )


def test_connected_components_form_one_group() -> None:
    pairs = [_pair("A", "B", 0.9), _pair("B", "C", 0.8)]
    groups = group_pairs(pairs)
    assert len(groups) == 1
    assert set(groups[0].members) == {"A", "B", "C"}


def test_separate_components_form_separate_groups() -> None:
    pairs = [_pair("A", "B", 0.9), _pair("X", "Y", 0.7)]
    groups = group_pairs(pairs)
    assert len(groups) == 2


def test_groups_ranked_by_score_desc() -> None:
    pairs = [_pair("A", "B", 0.6), _pair("X", "Y", 0.95)]
    groups = group_pairs(pairs)
    assert groups[0].members == ["X", "Y"]
    assert groups[0].score >= groups[1].score


def test_no_pairs_no_groups() -> None:
    assert group_pairs([]) == []
