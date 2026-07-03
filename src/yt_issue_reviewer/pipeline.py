"""End-to-end analysis orchestration: ingest → embed → score → group → label.

Kept separate from the CLI so it can be driven directly by tests with fakes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .analyze import clustering, scoring
from .config import Config
from .embeddings.ollama import Embedder
from .errors import OllamaUnavailable
from .ingest.models import Issue
from .ingest.youtrack import YouTrackSource
from .llm.labeler import Labeler
from .store.repository import Repository


@dataclass
class AnalysisResult:
    run_id: str
    issue_count: int
    degraded: bool
    warnings: list[str] = field(default_factory=list)
    groups: list[dict] = field(default_factory=list)
    summaries: dict[str, str] = field(default_factory=dict)
    pairs: list[scoring.ScoredPair] = field(default_factory=list)


def ingest_issues(
    source: YouTrackSource,
    repo: Repository,
    run_id: str,
    *,
    projects: list[str],
    state: str,
    since: str | None,
    until: str | None,
    refresh: bool,
) -> list[Issue]:
    """Fetch issues and cache them, preserving ``fetched_at`` for unchanged content."""
    issues = source.fetch_issues(projects, state=state, since=since, until=until)
    for issue in issues:
        old_hash = repo.cached_content_hash(issue.issue_id)
        if not refresh and old_hash == issue.content_hash():
            fetched = repo.fetched_at(issue.issue_id)  # keep prior staleness
        else:
            fetched = None  # stamp "now"
        repo.upsert_issue(issue, run_id, fetched_at=fetched)
        repo.save_links(issue, run_id)
    repo.commit()
    return issues


def embed_issues(
    embedder: Embedder,
    repo: Repository,
    issues: list[Issue],
) -> tuple[np.ndarray, str | None]:
    """Return an embedding matrix aligned to ``issues`` order, using the cache.

    Only cache-miss issues are sent to the embedder. Raises OllamaUnavailable if the
    embedder is unreachable.
    """
    embedder.check_available()

    cached: dict[str, list[float]] = {}
    misses: list[Issue] = []
    for issue in issues:
        vec = repo.get_embedding(issue.issue_id, issue.content_hash(), embedder.model)
        if vec is None:
            misses.append(issue)
        else:
            cached[issue.issue_id] = vec

    if misses:
        vectors = embedder.embed_batch([i.embed_text() for i in misses])
        for issue, vec in zip(misses, vectors, strict=True):
            repo.save_embedding(
                issue.issue_id,
                issue.content_hash(),
                embedder.model,
                vec,
                model_version=embedder.model_version,
            )
            cached[issue.issue_id] = vec
        repo.commit()

    matrix = np.array([cached[i.issue_id] for i in issues], dtype=np.float64)
    return matrix, embedder.model_version


def run_analysis(
    *,
    source: YouTrackSource,
    embedder: Embedder,
    repo: Repository,
    config: Config,
    projects: list[str],
    state: str = "open",
    since: str | None = None,
    until: str | None = None,
    min_score: float | None = None,
    weight_semantic: float | None = None,
    weight_structural: float | None = None,
    refresh: bool = False,
    labeler: Labeler | None = None,
) -> AnalysisResult:
    """Run the full pipeline, persist everything, and return a renderable result."""
    min_score = config.min_score if min_score is None else min_score
    w_sem = config.weight_semantic if weight_semantic is None else weight_semantic
    w_struct = config.weight_structural if weight_structural is None else weight_structural
    warnings: list[str] = []

    run_id = repo.create_run(
        projects=projects,
        state_filter=state,
        date_from=since,
        date_to=until,
        min_score=min_score,
        embedding_model=embedder.model,
        weight_semantic=w_sem,
        weight_structural=config.structural_weights,
        label_model=labeler.model if labeler else None,
    )

    issues = ingest_issues(
        source,
        repo,
        run_id,
        projects=projects,
        state=state,
        since=since,
        until=until,
        refresh=refresh,
    )

    # Embedding pass with graceful degradation (never egress content — Constitution I).
    vectors: np.ndarray | None
    degraded = False
    model_version: str | None = None
    try:
        vectors, model_version = embed_issues(embedder, repo, issues)
    except OllamaUnavailable as exc:
        degraded = True
        vectors = None
        warnings.append(f"Ollama unavailable ({exc}). Degrading to structural-only scoring.")

    pairs = scoring.generate_pairs(
        issues,
        vectors,
        min_score=min_score,
        weight_semantic=w_sem,
        weight_structural=w_struct,
        structural_weights=config.structural_weights,
        window_days=config.temporal_window_days,
        existing_links=repo.existing_links(run_id),
    )

    for p in pairs:
        repo.save_pair(
            run_id,
            p.issue_a,
            p.issue_b,
            semantic_score=p.semantic_score,
            structural_score=p.structural_score,
            combined_score=p.combined_score,
        )
        for ev in p.evidence:
            repo.save_evidence(
                run_id,
                signal=ev.signal,
                detail=ev.detail,
                issue_a=p.issue_a,
                issue_b=p.issue_b,
                weight=ev.weight,
            )

    groups = clustering.group_pairs(pairs)
    for rank, group in enumerate(groups, start=1):
        group_id = f"g{rank}"
        repo.save_group(
            run_id, group_id, rank=rank, group_score=group.score, size=len(group.members)
        )
        for issue_id in group.members:
            repo.save_group_member(run_id, group_id, issue_id)

    repo.commit()

    # Optional, presentation-only labeling (Constitution IV) — never changes groups.
    if labeler is not None:
        _apply_labels(labeler, repo, run_id, groups, warnings)

    repo.finish_run(
        run_id,
        issue_count=len(issues),
        degraded_structural_only=degraded,
        embedding_model_version=model_version,
    )

    summaries = repo.issue_summaries([i.issue_id for i in issues])
    return AnalysisResult(
        run_id=run_id,
        issue_count=len(issues),
        degraded=degraded,
        warnings=warnings,
        groups=repo.load_groups(run_id),
        summaries=summaries,
        pairs=pairs,
    )


def _apply_labels(
    labeler: Labeler,
    repo: Repository,
    run_id: str,
    groups: list[clustering.Group],
    warnings: list[str],
) -> None:
    try:
        labeler.check_available()
    except OllamaUnavailable as exc:
        warnings.append(f"Label model unavailable ({exc}). Skipping labels.")
        return

    for rank, group in enumerate(groups, start=1):
        summaries = list(repo.issue_summaries(group.members).values())
        evidence = [ev.detail for p in group.pairs for ev in p.evidence]
        try:
            label = labeler.label_group(summaries, evidence)
        except OllamaUnavailable as exc:  # pragma: no cover - defensive
            warnings.append(f"Labeling failed for group g{rank} ({exc}).")
            continue
        repo.update_group_label(run_id, f"g{rank}", label=label.label, rationale=label.rationale)
    repo.commit()
