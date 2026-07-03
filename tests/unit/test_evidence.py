"""Every retained pair must carry at least one evidence item."""

from __future__ import annotations

import numpy as np

from tests.conftest import load_fixture_issues
from yt_issue_reviewer.analyze import scoring, structural
from yt_issue_reviewer.analyze.evidence import build_evidence
from yt_issue_reviewer.config import DEFAULT_STRUCTURAL_WEIGHTS
from yt_issue_reviewer.embeddings.ollama import FakeEmbedder


def test_related_pair_has_evidence() -> None:
    issues = {i.issue_id: i for i in load_fixture_issues()}
    a, b = issues["PROJ-1"], issues["PROJ-2"]
    signals = structural.structural_signals(a, b, window_days=7)
    items = build_evidence(a, b, semantic_score=0.9, signals=signals, window_days=7)
    kinds = {i.signal for i in items}
    assert "shared_terms" in kinds
    assert "shared_tags" in kinds
    assert "same_reporter" in kinds
    assert "semantic_similarity" in kinds


def test_all_generated_pairs_have_evidence() -> None:
    issues = load_fixture_issues()
    vectors = np.array(FakeEmbedder(dim=128).embed_batch([i.embed_text() for i in issues]))
    pairs = scoring.generate_pairs(
        issues,
        vectors,
        min_score=0.3,
        weight_semantic=0.6,
        weight_structural=0.4,
        structural_weights=DEFAULT_STRUCTURAL_WEIGHTS,
        window_days=7,
    )
    assert pairs
    assert all(len(p.evidence) >= 1 for p in pairs)
