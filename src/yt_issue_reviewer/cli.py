"""Command-line interface for the Related Issue Finder.

Read-only against YouTrack; embeddings/labels via self-hosted Ollama only.
"""

from __future__ import annotations

import sys

import click

from .config import Config
from .embeddings.ollama import OllamaEmbedder
from .errors import OllamaUnavailable, YouTrackUnavailable
from .ingest.youtrack import CliYouTrackSource
from .llm.labeler import OllamaLabeler
from .pipeline import run_analysis
from .report import terminal
from .store.repository import Repository


def _err(message: str) -> None:
    click.echo(message, err=True)


@click.group()
@click.option("--db", "db_path", default=None, help="SQLite cache/results file.")
@click.option("--config", "config_path", default=None, help="TOML config file path.")
@click.option("--ollama-host", default=None, help="Ollama base URL (Tailscale ok).")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output to stderr.")
@click.pass_context
def main(
    ctx: click.Context,
    db_path: str | None,
    config_path: str | None,
    ollama_host: str | None,
    verbose: bool,
) -> None:
    """Find related issues across a YouTrack instance."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config.load(
        config_path=config_path, db_path=db_path, ollama_host=ollama_host
    )
    ctx.obj["verbose"] = verbose


def _config(ctx: click.Context) -> Config:
    return ctx.obj["config"]


# --- doctor -------------------------------------------------------------------


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check YouTrack and Ollama connectivity (read-only)."""
    cfg = _config(ctx)
    ok = True

    try:
        CliYouTrackSource().check_available()
        click.echo("YouTrack (yt): OK")
    except YouTrackUnavailable as exc:
        ok = False
        _err(f"YouTrack (yt): FAIL — {exc}")

    try:
        OllamaEmbedder(cfg.ollama_host, cfg.embedding_model).check_available()
        click.echo(f"Ollama embeddings ({cfg.embedding_model}): OK")
    except OllamaUnavailable as exc:
        ok = False
        _err(f"Ollama embeddings: FAIL — {exc}")

    if not ok:
        sys.exit(2)


# --- ingest -------------------------------------------------------------------


_project_option = click.option(
    "-p", "--project", "projects", multiple=True, required=True, help="Project(s) to include."
)
_state_option = click.option(
    "--state", type=click.Choice(["open", "all"]), default="open", show_default=True
)
_since_option = click.option("--since", default=None, help="Only issues on/after DATE.")
_until_option = click.option("--until", default=None, help="Only issues on/before DATE.")


@main.command()
@_project_option
@_state_option
@_since_option
@_until_option
@click.pass_context
def ingest(
    ctx: click.Context,
    projects: tuple[str, ...],
    state: str,
    since: str | None,
    until: str | None,
) -> None:
    """Fetch issues from YouTrack and cache them locally."""
    cfg = _config(ctx)
    repo = Repository.open(cfg.db_path)
    try:
        source = CliYouTrackSource()
        source.check_available()
        run_id = repo.create_run(
            projects=list(projects),
            state_filter=state,
            date_from=since,
            date_to=until,
            min_score=cfg.min_score,
            embedding_model=None,
            weight_semantic=cfg.weight_semantic,
            weight_structural=cfg.structural_weights,
            label_model=None,
        )
        from .pipeline import ingest_issues

        issues = ingest_issues(
            source,
            repo,
            run_id,
            projects=list(projects),
            state=state,
            since=since,
            until=until,
            refresh=False,
        )
        repo.finish_run(run_id, issue_count=len(issues), degraded_structural_only=False)
        fetched = {i.issue_id: (repo.fetched_at(i.issue_id) or "-") for i in issues}
        terminal.render_issues(issues, fetched)
    except YouTrackUnavailable as exc:
        _err(f"error: {exc}")
        sys.exit(2)
    finally:
        repo.close()


# --- embed --------------------------------------------------------------------


@main.command()
@_project_option
@_state_option
@_since_option
@_until_option
@click.option("--embedding-model", default=None, help="Ollama embedding model.")
@click.pass_context
def embed(
    ctx: click.Context,
    projects: tuple[str, ...],
    state: str,
    since: str | None,
    until: str | None,
    embedding_model: str | None,
) -> None:
    """Ensure issues are cached and embedded (reports cache hits)."""
    cfg = _config(ctx)
    model = embedding_model or cfg.embedding_model
    repo = Repository.open(cfg.db_path)
    try:
        source = CliYouTrackSource()
        source.check_available()
        run_id = repo.create_run(
            projects=list(projects),
            state_filter=state,
            date_from=since,
            date_to=until,
            min_score=cfg.min_score,
            embedding_model=model,
            weight_semantic=cfg.weight_semantic,
            weight_structural=cfg.structural_weights,
            label_model=None,
        )
        from .pipeline import embed_issues, ingest_issues

        issues = ingest_issues(
            source,
            repo,
            run_id,
            projects=list(projects),
            state=state,
            since=since,
            until=until,
            refresh=False,
        )
        hits_before = sum(
            1 for i in issues if repo.get_embedding(i.issue_id, i.content_hash(), model) is not None
        )
        embedder = OllamaEmbedder(cfg.ollama_host, model)
        embed_issues(embedder, repo, issues)
        repo.finish_run(run_id, issue_count=len(issues), degraded_structural_only=False)
        click.echo(
            f"Embedded {len(issues) - hits_before} issue(s); {hits_before} cache hit(s); "
            f"model={model}"
        )
    except YouTrackUnavailable as exc:
        _err(f"error: {exc}")
        sys.exit(2)
    except OllamaUnavailable as exc:
        _err(f"error: {exc}")
        sys.exit(1)
    finally:
        repo.close()


# --- analyze ------------------------------------------------------------------


@main.command()
@_project_option
@_state_option
@_since_option
@_until_option
@click.option("--min-score", type=float, default=None, help="Minimum relatedness threshold.")
@click.option("--embedding-model", default=None, help="Ollama embedding model.")
@click.option("--weight-semantic", type=float, default=None, help="Weight of semantic score.")
@click.option("--weight-structural", type=float, default=None, help="Weight of structural signals.")
@click.option("--label/--no-label", default=False, help="Generate group labels (flag-gated).")
@click.option("--label-model", default=None, help="Chat model used when --label is set.")
@click.option("--refresh/--no-refresh", default=False, help="Ignore cache and re-fetch.")
@click.pass_context
def analyze(
    ctx: click.Context,
    projects: tuple[str, ...],
    state: str,
    since: str | None,
    until: str | None,
    min_score: float | None,
    embedding_model: str | None,
    weight_semantic: float | None,
    weight_structural: float | None,
    label: bool,
    label_model: str | None,
    refresh: bool,
) -> None:
    """Run a full related-issue analysis and report ranked groups."""
    cfg = _config(ctx)
    model = embedding_model or cfg.embedding_model
    repo = Repository.open(cfg.db_path)
    try:
        source = CliYouTrackSource()
        source.check_available()
        embedder = OllamaEmbedder(cfg.ollama_host, model)
        labeler = OllamaLabeler(cfg.ollama_host, label_model or cfg.label_model) if label else None
        result = run_analysis(
            source=source,
            embedder=embedder,
            repo=repo,
            config=cfg,
            projects=list(projects),
            state=state,
            since=since,
            until=until,
            min_score=min_score,
            weight_semantic=weight_semantic,
            weight_structural=weight_structural,
            refresh=refresh,
            labeler=labeler,
        )
        for warning in result.warnings:
            _err(f"warning: {warning}")
        terminal.render_groups(result.groups, result.summaries)
        click.echo(
            f"run {result.run_id[:8]} — {result.issue_count} issues, "
            f"{len(result.groups)} group(s)" + (" [structural-only]" if result.degraded else "")
        )
    except YouTrackUnavailable as exc:
        _err(f"error: {exc}")
        sys.exit(2)
    finally:
        repo.close()


# --- show / runs --------------------------------------------------------------


@main.command()
@click.option("--run-id", default=None, help="Which stored run to display (default: latest).")
@click.option("--min-score", type=float, default=None, help="Re-filter stored groups for display.")
@click.pass_context
def show(ctx: click.Context, run_id: str | None, min_score: float | None) -> None:
    """Re-display a stored run from the SQLite artifact (no network)."""
    cfg = _config(ctx)
    repo = Repository.open(cfg.db_path)
    try:
        rid = run_id or repo.latest_run_id()
        if rid is None:
            _err("no runs found in the database.")
            sys.exit(1)
        groups = repo.load_groups(rid, min_score=min_score)
        member_ids = [m for g in groups for m in g["members"]]
        summaries = repo.issue_summaries(member_ids)
        terminal.render_groups(groups, summaries)
    finally:
        repo.close()


@main.command()
@click.pass_context
def runs(ctx: click.Context) -> None:
    """List stored analysis runs with their settings and staleness."""
    cfg = _config(ctx)
    repo = Repository.open(cfg.db_path)
    try:
        terminal.render_runs(repo.list_runs())
    finally:
        repo.close()


if __name__ == "__main__":  # pragma: no cover
    main()
