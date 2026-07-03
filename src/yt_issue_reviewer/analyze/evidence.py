"""Assemble human-readable evidence for a pair (pure, no I/O).

Constitution IV: every surfaced relationship carries human-readable evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ingest.models import Issue
from . import structural, terms


@dataclass(frozen=True)
class EvidenceItem:
    signal: str
    detail: str
    weight: float | None = None


def build_evidence(
    a: Issue,
    b: Issue,
    *,
    semantic_score: float | None,
    signals: dict[str, float],
    window_days: int,
) -> list[EvidenceItem]:
    """Produce one evidence item per meaningfully-contributing signal."""
    items: list[EvidenceItem] = []

    common = sorted(terms.shared_terms(a, b))
    if common:
        shown = ", ".join(common[:6])
        items.append(EvidenceItem("shared_terms", f"shared terms: {shown}", None))

    common_tags = sorted(structural.shared_tags(a, b))
    if common_tags:
        items.append(
            EvidenceItem(
                "shared_tags",
                f"shared tags: {', '.join(common_tags)}",
                signals.get("shared_tags"),
            )
        )

    if structural.same_reporter(a, b):
        delta = structural.days_apart(a, b)
        when = f" within {delta:.1f} days" if delta is not None else ""
        items.append(
            EvidenceItem(
                "same_reporter",
                f"same reporter ({a.reporter}){when}",
                signals.get("same_reporter"),
            )
        )

    prox = signals.get("temporal_proximity", 0.0)
    if prox > 0 and not structural.same_reporter(a, b):
        delta = structural.days_apart(a, b)
        if delta is not None:
            items.append(
                EvidenceItem(
                    "temporal_proximity",
                    f"created {delta:.1f} days apart",
                    prox,
                )
            )

    if semantic_score is not None and semantic_score > 0:
        items.append(
            EvidenceItem(
                "semantic_similarity",
                f"semantic similarity {semantic_score:.2f}",
                semantic_score,
            )
        )

    return items
