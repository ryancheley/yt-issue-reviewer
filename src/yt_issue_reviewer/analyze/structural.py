"""Local structural relatedness signals (pure functions, no LLM, no I/O)."""

from __future__ import annotations

from datetime import datetime

from ..ingest.models import Issue


def _parse_day(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.fromisoformat(value[:10])
        except ValueError:
            return None


def shared_tags(a: Issue, b: Issue) -> set[str]:
    return set(a.tags) & set(b.tags)


def tag_jaccard(a: Issue, b: Issue) -> float:
    sa, sb = set(a.tags), set(b.tags)
    if not sa and not sb:
        return 0.0
    union = sa | sb
    return len(sa & sb) / len(union) if union else 0.0


def same_reporter(a: Issue, b: Issue) -> bool:
    return bool(a.reporter) and a.reporter == b.reporter


def days_apart(a: Issue, b: Issue) -> float | None:
    da, db = _parse_day(a.created), _parse_day(b.created)
    if da is None or db is None:
        return None
    return abs((da - db).total_seconds()) / 86400.0


def temporal_proximity(a: Issue, b: Issue, window_days: int) -> float:
    """1.0 when created at the same time, decaying to 0.0 at ``window_days`` apart."""
    delta = days_apart(a, b)
    if delta is None or window_days <= 0:
        return 0.0
    return max(0.0, 1.0 - delta / window_days)


def structural_signals(a: Issue, b: Issue, window_days: int) -> dict[str, float]:
    """Return each structural signal in [0, 1], keyed by signal name."""
    return {
        "shared_tags": tag_jaccard(a, b),
        "same_reporter": 1.0 if same_reporter(a, b) else 0.0,
        "temporal_proximity": temporal_proximity(a, b, window_days),
    }


def structural_score(signals: dict[str, float], weights: dict[str, float]) -> float:
    """Weighted average of signals, normalized by the total applied weight → [0, 1]."""
    total_weight = sum(weights.get(k, 0.0) for k in signals)
    if total_weight <= 0:
        return 0.0
    return sum(signals[k] * weights.get(k, 0.0) for k in signals) / total_weight
