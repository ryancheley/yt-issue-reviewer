"""Combined relatedness scoring and pair generation (pure, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..embeddings.ollama import cosine_matrix
from ..ingest.models import Issue
from . import structural
from .evidence import EvidenceItem, build_evidence


@dataclass(frozen=True)
class ScoredPair:
    issue_a: str
    issue_b: str
    semantic_score: float | None
    structural_score: float
    combined_score: float
    evidence: list[EvidenceItem]


def combine(
    semantic: float | None,
    structural_value: float,
    *,
    weight_semantic: float,
    weight_structural: float,
) -> float:
    """Weighted blend of semantic + structural, renormalized over available weights.

    In degraded mode (``semantic is None``) the score is structural-only.
    """
    if semantic is None:
        return structural_value
    total = weight_semantic + weight_structural
    if total <= 0:
        return 0.0
    return (weight_semantic * semantic + weight_structural * structural_value) / total


def generate_pairs(
    issues: list[Issue],
    vectors: np.ndarray | None,
    *,
    min_score: float,
    weight_semantic: float,
    weight_structural: float,
    structural_weights: dict[str, float],
    window_days: int,
    existing_links: set[frozenset[str]] | None = None,
) -> list[ScoredPair]:
    """Score all issue pairs; keep those >= ``min_score`` and not already linked.

    ``vectors`` rows align with ``issues`` order. Pass ``None`` for degraded
    (structural-only) scoring.
    """
    existing = existing_links or set()
    sim = cosine_matrix(vectors) if vectors is not None and len(issues) else None

    pairs: list[ScoredPair] = []
    for i in range(len(issues)):
        for j in range(i + 1, len(issues)):
            a, b = issues[i], issues[j]
            if frozenset((a.issue_id, b.issue_id)) in existing:
                continue

            semantic = float(sim[i, j]) if sim is not None else None
            signals = structural.structural_signals(a, b, window_days)
            struct = structural.structural_score(signals, structural_weights)
            combined = combine(
                semantic,
                struct,
                weight_semantic=weight_semantic,
                weight_structural=weight_structural,
            )
            if combined < min_score:
                continue

            evidence = build_evidence(
                a, b, semantic_score=semantic, signals=signals, window_days=window_days
            )
            # Order the pair deterministically for stable storage.
            lo, hi = sorted((a.issue_id, b.issue_id))
            pairs.append(
                ScoredPair(
                    issue_a=lo,
                    issue_b=hi,
                    semantic_score=semantic,
                    structural_score=struct,
                    combined_score=combined,
                    evidence=evidence,
                )
            )

    pairs.sort(key=lambda p: p.combined_score, reverse=True)
    return pairs
