"""Structural signal functions."""

from __future__ import annotations

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.analyze import structural


def _issues() -> dict:
    return {i.issue_id: i for i in load_fixture_issues()}


def test_tag_jaccard() -> None:
    issues = _issues()
    # PROJ-1 and PROJ-2 both tagged auth+backend -> jaccard 1.0
    assert structural.tag_jaccard(issues["PROJ-1"], issues["PROJ-2"]) == 1.0
    # PROJ-1 (auth,backend) vs PROJ-3 (export,reports) -> 0.0
    assert structural.tag_jaccard(issues["PROJ-1"], issues["PROJ-3"]) == 0.0


def test_same_reporter() -> None:
    issues = _issues()
    assert structural.same_reporter(issues["PROJ-1"], issues["PROJ-2"]) is True
    assert structural.same_reporter(issues["PROJ-1"], issues["PROJ-3"]) is False


def test_temporal_proximity_decays_with_distance() -> None:
    issues = _issues()
    near = structural.temporal_proximity(issues["PROJ-1"], issues["PROJ-2"], window_days=7)
    far = structural.temporal_proximity(issues["PROJ-1"], issues["PROJ-3"], window_days=7)
    assert near > far
    assert 0.0 <= far <= near <= 1.0


def test_structural_score_bounded() -> None:
    issues = _issues()
    signals = structural.structural_signals(issues["PROJ-1"], issues["PROJ-2"], window_days=7)
    weights = {"shared_tags": 0.5, "same_reporter": 0.2, "temporal_proximity": 0.3}
    score = structural.structural_score(signals, weights)
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # strongly related structurally
