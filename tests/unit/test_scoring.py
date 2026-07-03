"""Combined scoring, threshold filtering, and existing-link exclusion."""

from __future__ import annotations

import numpy as np

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.analyze import scoring
from yt_issue_reviewer.config import DEFAULT_STRUCTURAL_WEIGHTS
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder


def _vectors(issues: list) -> np.ndarray:
    emb = FakeEmbedder(dim=128)
    return np.array(emb.embed_batch([i.embed_text() for i in issues]))


def test_combine_degraded_is_structural_only() -> None:
    assert scoring.combine(None, 0.8, weight_semantic=0.7, weight_structural=0.3) == 0.8


def test_combine_blends_and_renormalizes() -> None:
    val = scoring.combine(1.0, 0.0, weight_semantic=0.75, weight_structural=0.25)
    assert abs(val - 0.75) < 1e-9


def test_related_pair_scores_above_unrelated() -> None:
    issues = load_fixture_issues()
    pairs = scoring.generate_pairs(
        issues,
        _vectors(issues),
        min_score=0.0,
        weight_semantic=0.6,
        weight_structural=0.4,
        structural_weights=DEFAULT_STRUCTURAL_WEIGHTS,
        window_days=7,
    )
    scores = {(p.issue_a, p.issue_b): p.combined_score for p in pairs}
    # PROJ-1/PROJ-2 (dup login bug) should outrank PROJ-1/PROJ-5 (unrelated).
    assert scores[("PROJ-1", "PROJ-2")] > scores[("PROJ-1", "PROJ-5")]


def test_existing_links_excluded() -> None:
    issues = load_fixture_issues()
    existing = {frozenset(("PROJ-3", "PROJ-4"))}
    pairs = scoring.generate_pairs(
        issues,
        _vectors(issues),
        min_score=0.0,
        weight_semantic=0.6,
        weight_structural=0.4,
        structural_weights=DEFAULT_STRUCTURAL_WEIGHTS,
        window_days=7,
        existing_links=existing,
    )
    assert all(frozenset((p.issue_a, p.issue_b)) != frozenset(("PROJ-3", "PROJ-4")) for p in pairs)


def test_threshold_filters_low_scores() -> None:
    issues = load_fixture_issues()
    high = scoring.generate_pairs(
        issues,
        _vectors(issues),
        min_score=0.95,
        weight_semantic=0.6,
        weight_structural=0.4,
        structural_weights=DEFAULT_STRUCTURAL_WEIGHTS,
        window_days=7,
    )
    low = scoring.generate_pairs(
        issues,
        _vectors(issues),
        min_score=0.0,
        weight_semantic=0.6,
        weight_structural=0.4,
        structural_weights=DEFAULT_STRUCTURAL_WEIGHTS,
        window_days=7,
    )
    assert len(high) <= len(low)
    assert all(p.combined_score >= 0.95 for p in high)
