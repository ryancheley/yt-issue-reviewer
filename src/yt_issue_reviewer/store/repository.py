"""Typed read/write access over the SQLite cache + results store."""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .. import __version__
from ..ingest.models import Issue
from .schema import apply_schema


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class RunInfo:
    run_id: str
    started_at: str
    finished_at: str | None
    projects: list[str]
    state_filter: str | None
    min_score: float
    embedding_model: str | None
    weight_semantic: float
    label_model: str | None
    degraded_structural_only: bool
    issue_count: int


class Repository:
    """Owns a SQLite connection and all persistence for a run."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    @classmethod
    def open(cls, db_path: str | Path) -> Repository:
        path = Path(db_path)
        if path.parent and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        apply_schema(conn)
        return cls(conn)

    def close(self) -> None:
        self.conn.close()

    # --- run_metadata -----------------------------------------------------

    def create_run(
        self,
        *,
        projects: list[str],
        state_filter: str | None,
        date_from: str | None,
        date_to: str | None,
        min_score: float,
        embedding_model: str | None,
        weight_semantic: float,
        weight_structural: dict[str, float],
        label_model: str | None,
    ) -> str:
        run_id = uuid.uuid4().hex
        self.conn.execute(
            """
            INSERT INTO run_metadata (
                run_id, started_at, finished_at, projects, state_filter,
                date_from, date_to, min_score, embedding_model, embedding_model_version,
                weight_semantic, weight_structural, label_model,
                degraded_structural_only, issue_count, tool_version
            ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, 0, 0, ?)
            """,
            (
                run_id,
                _now(),
                json.dumps(projects),
                state_filter,
                date_from,
                date_to,
                min_score,
                embedding_model,
                weight_semantic,
                json.dumps(weight_structural),
                label_model,
                __version__,
            ),
        )
        self.conn.commit()
        return run_id

    def finish_run(
        self,
        run_id: str,
        *,
        issue_count: int,
        degraded_structural_only: bool,
        embedding_model_version: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE run_metadata
            SET finished_at = ?, issue_count = ?, degraded_structural_only = ?,
                embedding_model_version = COALESCE(?, embedding_model_version)
            WHERE run_id = ?
            """,
            (
                _now(),
                issue_count,
                1 if degraded_structural_only else 0,
                embedding_model_version,
                run_id,
            ),
        )
        self.conn.commit()

    def latest_run_id(self) -> str | None:
        row = self.conn.execute(
            "SELECT run_id FROM run_metadata ORDER BY started_at DESC LIMIT 1"
        ).fetchone()
        return row["run_id"] if row else None

    def list_runs(self) -> list[RunInfo]:
        rows = self.conn.execute("SELECT * FROM run_metadata ORDER BY started_at DESC").fetchall()
        return [self._run_info(r) for r in rows]

    def get_run(self, run_id: str) -> RunInfo | None:
        row = self.conn.execute("SELECT * FROM run_metadata WHERE run_id = ?", (run_id,)).fetchone()
        return self._run_info(row) if row else None

    @staticmethod
    def _run_info(row: sqlite3.Row) -> RunInfo:
        return RunInfo(
            run_id=row["run_id"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            projects=json.loads(row["projects"]),
            state_filter=row["state_filter"],
            min_score=row["min_score"],
            embedding_model=row["embedding_model"],
            weight_semantic=row["weight_semantic"],
            label_model=row["label_model"],
            degraded_structural_only=bool(row["degraded_structural_only"]),
            issue_count=row["issue_count"],
        )

    # --- issues + links ---------------------------------------------------

    def cached_content_hash(self, issue_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT content_hash FROM issues WHERE issue_id = ?", (issue_id,)
        ).fetchone()
        return row["content_hash"] if row else None

    def upsert_issue(self, issue: Issue, run_id: str, *, fetched_at: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO issues (
                issue_id, project, number, summary, description, state, assignee,
                reporter, tags, created, updated, content_hash, fetched_at, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(issue_id) DO UPDATE SET
                project=excluded.project, number=excluded.number,
                summary=excluded.summary, description=excluded.description,
                state=excluded.state, assignee=excluded.assignee,
                reporter=excluded.reporter, tags=excluded.tags,
                created=excluded.created, updated=excluded.updated,
                content_hash=excluded.content_hash, fetched_at=excluded.fetched_at,
                run_id=excluded.run_id
            """,
            (
                issue.issue_id,
                issue.project,
                issue.number,
                issue.summary,
                issue.description,
                issue.state,
                issue.assignee,
                issue.reporter,
                json.dumps(list(issue.tags)),
                issue.created,
                issue.updated,
                issue.content_hash(),
                fetched_at or _now(),
                run_id,
            ),
        )

    def save_links(self, issue: Issue, run_id: str) -> None:
        for link in issue.links:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO issue_links (source_id, target_id, link_type, run_id)
                VALUES (?, ?, ?, ?)
                """,
                (issue.issue_id, link.target_id, link.link_type, run_id),
            )

    def commit(self) -> None:
        self.conn.commit()

    def load_issue(self, issue_id: str) -> Issue | None:
        row = self.conn.execute("SELECT * FROM issues WHERE issue_id = ?", (issue_id,)).fetchone()
        return self._issue_from_row(row) if row else None

    @staticmethod
    def _issue_from_row(row: sqlite3.Row) -> Issue:
        return Issue(
            issue_id=row["issue_id"],
            project=row["project"],
            number=row["number"] or 0,
            summary=row["summary"],
            description=row["description"] or "",
            state=row["state"] or "",
            assignee=row["assignee"],
            reporter=row["reporter"] or "",
            tags=tuple(json.loads(row["tags"]) if row["tags"] else ()),
            created=row["created"] or "",
            updated=row["updated"] or "",
            links=(),
        )

    def fetched_at(self, issue_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT fetched_at FROM issues WHERE issue_id = ?", (issue_id,)
        ).fetchone()
        return row["fetched_at"] if row else None

    def existing_links(self, run_id: str) -> set[frozenset[str]]:
        """Unordered issue pairs already linked in YouTrack (for exclusion)."""
        rows = self.conn.execute(
            "SELECT source_id, target_id FROM issue_links WHERE run_id = ?", (run_id,)
        ).fetchall()
        return {frozenset((r["source_id"], r["target_id"])) for r in rows}

    # --- embeddings -------------------------------------------------------

    def get_embedding(self, issue_id: str, content_hash: str, model: str) -> list[float] | None:
        row = self.conn.execute(
            """
            SELECT vector FROM embeddings
            WHERE issue_id = ? AND content_hash = ? AND model = ?
            """,
            (issue_id, content_hash, model),
        ).fetchone()
        return json.loads(row["vector"]) if row else None

    def save_embedding(
        self,
        issue_id: str,
        content_hash: str,
        model: str,
        vector: list[float],
        *,
        model_version: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO embeddings
                (issue_id, content_hash, model, model_version, dim, vector, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                issue_id,
                content_hash,
                model,
                model_version,
                len(vector),
                json.dumps(vector),
                _now(),
            ),
        )

    # --- pairs / groups / evidence ---------------------------------------

    def save_pair(
        self,
        run_id: str,
        issue_a: str,
        issue_b: str,
        *,
        semantic_score: float | None,
        structural_score: float,
        combined_score: float,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO pairs
                (run_id, issue_a, issue_b, semantic_score, structural_score, combined_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (run_id, issue_a, issue_b, semantic_score, structural_score, combined_score),
        )

    def save_group(
        self,
        run_id: str,
        group_id: str,
        *,
        rank: int,
        group_score: float,
        size: int,
        label: str | None = None,
        label_is_generated: bool = False,
        rationale: str | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO groups
                (run_id, group_id, rank, group_score, size, label, label_is_generated, rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                group_id,
                rank,
                group_score,
                size,
                label,
                1 if label_is_generated else 0,
                rationale,
            ),
        )

    def update_group_label(self, run_id: str, group_id: str, *, label: str, rationale: str) -> None:
        self.conn.execute(
            """
            UPDATE groups SET label = ?, rationale = ?, label_is_generated = 1
            WHERE run_id = ? AND group_id = ?
            """,
            (label, rationale, run_id, group_id),
        )

    def save_group_member(self, run_id: str, group_id: str, issue_id: str) -> None:
        self.conn.execute(
            """
            INSERT OR IGNORE INTO group_members (run_id, group_id, issue_id)
            VALUES (?, ?, ?)
            """,
            (run_id, group_id, issue_id),
        )

    def save_evidence(
        self,
        run_id: str,
        *,
        signal: str,
        detail: str,
        issue_a: str,
        issue_b: str | None = None,
        group_id: str | None = None,
        weight: float | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO evidence
                (run_id, group_id, issue_a, issue_b, signal, detail, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, group_id, issue_a, issue_b, signal, detail, weight),
        )

    # --- read-back for `show` --------------------------------------------

    def load_groups(self, run_id: str, *, min_score: float | None = None) -> list[dict]:
        """Reconstruct ranked groups with members + evidence for display (no network)."""
        group_rows = self.conn.execute(
            "SELECT * FROM groups WHERE run_id = ? ORDER BY rank ASC", (run_id,)
        ).fetchall()
        groups: list[dict] = []
        for g in group_rows:
            if min_score is not None and g["group_score"] < min_score:
                continue
            members = [
                r["issue_id"]
                for r in self.conn.execute(
                    "SELECT issue_id FROM group_members WHERE run_id = ? AND group_id = ?",
                    (run_id, g["group_id"]),
                ).fetchall()
            ]
            ev_rows = self.conn.execute(
                "SELECT signal, detail, issue_a, issue_b FROM evidence "
                "WHERE run_id = ? AND (group_id = ? OR issue_a IN "
                "(SELECT issue_id FROM group_members WHERE run_id = ? AND group_id = ?))",
                (run_id, g["group_id"], run_id, g["group_id"]),
            ).fetchall()
            groups.append(
                {
                    "group_id": g["group_id"],
                    "rank": g["rank"],
                    "group_score": g["group_score"],
                    "size": g["size"],
                    "label": g["label"],
                    "label_is_generated": bool(g["label_is_generated"]),
                    "rationale": g["rationale"],
                    "members": members,
                    "evidence": [
                        {
                            "signal": e["signal"],
                            "detail": e["detail"],
                            "issue_a": e["issue_a"],
                            "issue_b": e["issue_b"],
                        }
                        for e in ev_rows
                    ],
                }
            )
        return groups

    def issue_summaries(self, issue_ids: list[str]) -> dict[str, str]:
        if not issue_ids:
            return {}
        placeholders = ",".join("?" * len(issue_ids))
        rows = self.conn.execute(
            f"SELECT issue_id, summary FROM issues WHERE issue_id IN ({placeholders})",
            issue_ids,
        ).fetchall()
        return {r["issue_id"]: r["summary"] for r in rows}
