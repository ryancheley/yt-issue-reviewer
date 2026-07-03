"""Datasette-friendly SQLite schema for the cache + results store.

Only TEXT / INTEGER / REAL columns; embedding vectors are stored as JSON text. No
extensions or exotic types, so a self-hosted Datasette can browse everything directly.
"""

from __future__ import annotations

import sqlite3

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS run_metadata (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        projects TEXT NOT NULL,
        state_filter TEXT,
        date_from TEXT,
        date_to TEXT,
        min_score REAL NOT NULL,
        embedding_model TEXT,
        embedding_model_version TEXT,
        weight_semantic REAL NOT NULL,
        weight_structural TEXT NOT NULL,
        label_model TEXT,
        degraded_structural_only INTEGER NOT NULL DEFAULT 0,
        issue_count INTEGER NOT NULL DEFAULT 0,
        tool_version TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS issues (
        issue_id TEXT PRIMARY KEY,
        project TEXT NOT NULL,
        number INTEGER,
        summary TEXT NOT NULL,
        description TEXT,
        state TEXT,
        assignee TEXT,
        reporter TEXT,
        tags TEXT,
        created TEXT,
        updated TEXT,
        content_hash TEXT NOT NULL,
        fetched_at TEXT NOT NULL,
        run_id TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS issue_links (
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        link_type TEXT NOT NULL,
        run_id TEXT NOT NULL,
        PRIMARY KEY (source_id, target_id, link_type, run_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS embeddings (
        issue_id TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        model TEXT NOT NULL,
        model_version TEXT,
        dim INTEGER NOT NULL,
        vector TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (issue_id, content_hash, model)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pairs (
        run_id TEXT NOT NULL,
        issue_a TEXT NOT NULL,
        issue_b TEXT NOT NULL,
        semantic_score REAL,
        structural_score REAL,
        combined_score REAL NOT NULL,
        PRIMARY KEY (run_id, issue_a, issue_b)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS groups (
        run_id TEXT NOT NULL,
        group_id TEXT NOT NULL,
        rank INTEGER NOT NULL,
        group_score REAL NOT NULL,
        size INTEGER NOT NULL,
        label TEXT,
        label_is_generated INTEGER NOT NULL DEFAULT 0,
        rationale TEXT,
        PRIMARY KEY (run_id, group_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS group_members (
        run_id TEXT NOT NULL,
        group_id TEXT NOT NULL,
        issue_id TEXT NOT NULL,
        PRIMARY KEY (run_id, group_id, issue_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence (
        run_id TEXT NOT NULL,
        group_id TEXT,
        issue_a TEXT NOT NULL,
        issue_b TEXT,
        signal TEXT NOT NULL,
        detail TEXT NOT NULL,
        weight REAL
    )
    """,
)


def apply_schema(conn: sqlite3.Connection) -> None:
    """Create all tables idempotently."""
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()
