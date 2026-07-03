"""Rich-formatted terminal rendering for issues, pairs, groups, and runs."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ..ingest.models import Issue
from ..store.repository import RunInfo

console = Console()


def render_issues(issues: list[Issue], fetched_at: dict[str, str]) -> None:
    table = Table(title=f"Ingested issues ({len(issues)})")
    for col in ("Issue", "Project", "State", "Reporter", "Summary", "Fetched"):
        table.add_column(col, overflow="fold")
    for issue in issues:
        table.add_row(
            issue.issue_id,
            issue.project,
            issue.state or "-",
            issue.reporter or "-",
            issue.summary,
            fetched_at.get(issue.issue_id, "-"),
        )
    console.print(table)


def render_pairs(pairs: list, summaries: dict[str, str]) -> None:
    table = Table(title=f"Related pairs ({len(pairs)})")
    for col in ("Score", "Issue A", "Issue B", "Evidence"):
        table.add_column(col, overflow="fold")
    for p in pairs:
        ev = "; ".join(e.detail for e in p.evidence)
        table.add_row(
            f"{p.combined_score:.2f}",
            f"{p.issue_a} {summaries.get(p.issue_a, '')}",
            f"{p.issue_b} {summaries.get(p.issue_b, '')}",
            ev,
        )
    console.print(table)


def render_groups(groups: list[dict], summaries: dict[str, str]) -> None:
    if not groups:
        console.print("[yellow]No related groups found above the threshold.[/yellow]")
        return
    for g in groups:
        header = f"[bold]Group #{g['rank']}[/bold]  score={g['group_score']:.2f}  size={g['size']}"
        if g.get("label"):
            tag = " [dim](generated)[/dim]" if g.get("label_is_generated") else ""
            header += f"\n[cyan]{g['label']}[/cyan]{tag}"
            if g.get("rationale"):
                header += f"\n[dim]{g['rationale']}[/dim]"
        console.print(header)

        table = Table(show_header=True, header_style="bold")
        table.add_column("Issue")
        table.add_column("Summary", overflow="fold")
        for issue_id in g["members"]:
            table.add_row(issue_id, summaries.get(issue_id, ""))
        console.print(table)

        evidence = g.get("evidence") or []
        if evidence:
            seen = set()
            lines = []
            for e in evidence:
                key = (e["signal"], e["detail"])
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"  • {e['detail']}")
            console.print("[dim]Evidence:[/dim]\n" + "\n".join(lines))
        console.print()


def render_runs(runs: list[RunInfo]) -> None:
    table = Table(title=f"Analysis runs ({len(runs)})")
    for col in ("Run", "Started", "Projects", "State", "Model", "Issues", "Degraded"):
        table.add_column(col, overflow="fold")
    for r in runs:
        table.add_row(
            r.run_id[:8],
            r.started_at,
            ", ".join(r.projects),
            r.state_filter or "-",
            r.embedding_model or "-",
            str(r.issue_count),
            "yes" if r.degraded_structural_only else "no",
        )
    console.print(table)
