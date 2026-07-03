# Implementation Plan: Related Issue Finder

**Branch**: `001-related-issue-finder` | **Date**: 2026-07-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-related-issue-finder/spec.md`

## Summary

A run-on-demand CLI that helps a team lead find related issues across a YouTrack
instance. It ingests issues through the `youtrack_cli` package, caches them locally in
SQLite, and scores relatedness with a **hybrid engine**: semantic similarity from
self-hosted Ollama embeddings (cosine similarity over title+description vectors) blended
with locally-computed structural signals (shared tags/components, reporter overlap,
temporal proximity). Pairs above a threshold are grouped; each group carries a
relatedness score and human-readable evidence. An optional, flag-gated Ollama chat call
adds a generated one-line label and rationale that is presentation-only and never
affects scores or membership. Results render as rich terminal tables and persist as
Datasette-friendly SQLite tables that double as the durable, shareable export. Embeddings
are cached keyed on `(issue_id, content_hash, model)` so unchanged issues are never
re-embedded, making repeat runs near-instant.

## Technical Context

**Language/Version**: Python 3.14+

**Primary Dependencies**:
- `youtrack_cli` (the `yt` CLI) — the ONLY path to YouTrack (Constitution III)
- `ollama` (official Python client) — embeddings + chat against self-hosted Ollama
- `click` — CLI framework (consistent with yt-cli conventions)
- `rich` — terminal tables
- Standard library `sqlite3` — cache + results store
- `numpy` — cosine similarity over embedding vectors (small, well-maintained)

**Storage**: SQLite (single file), Datasette-friendly plain tables:
`issues`, `issue_links`, `embeddings`, `pairs`, `groups`, `group_members`, `evidence`,
`run_metadata`. No exotic types (vectors stored as JSON text or float blobs with a
documented, plain representation).

**Testing**: pytest. Pure analysis logic (structural signals, scoring, clustering,
tokenization/term extraction) unit-tested against small fixture corpora with known
related sets. Ollama and YouTrack access behind interfaces with in-memory fakes.

**Target Platform**: Local developer/operator machine (macOS/Linux); Ollama reached over
Tailscale or localhost.

**Project Type**: Single-project CLI application.

**Performance Goals**: Full run over ~1,000 issues completes in minutes (dominated by the
initial embedding pass). Repeat runs over unchanged issues near-instant via the embedding
cache. Embeddings requested in batches.

**Constraints**:
- No issue content leaves user-controlled infrastructure; Ollama only, no third-party
  hosted AI, no fallback (Constitution I).
- Read-only against YouTrack — no writes of any kind in this version (Constitution II).
- All YouTrack access via `youtrack_cli` — no parallel REST client (Constitution III).
- Ollama base URL configurable (env var / config file). If Ollama is unreachable, fail
  with a clear error and degrade to structural-signals-only scoring with a warning,
  rather than crashing or falling back to any hosted service.
- Every surfaced relationship carries human-readable evidence; embedding model
  name+version recorded per run (Constitution IV).

**Scale/Scope**: Several hundred to a few thousand issues across multiple projects;
performance anchored at ~1,000 issues per run. Single operator; no multi-user access
control.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Compliance in this plan | Status |
|---|-----------|-------------------------|--------|
| I | Privacy & Data Boundaries (NON-NEGOTIABLE) | Embeddings + labels via self-hosted Ollama only; base URL configurable; no third-party AI, no fallback. Ollama-unreachable path degrades to structural-only, never egresses content. | ✅ PASS |
| II | Read-Only by Default | Only `yt` read commands (`issues list`/`search`) are invoked. No write path exists in this version; automatic linking/merging explicitly out of scope. | ✅ PASS |
| III | Build on yt-cli | All YouTrack access goes through the `youtrack_cli` package via a single adapter (subprocess `yt ... --format json`). No direct REST client. Gaps recorded as upstream candidates (see research.md). | ✅ PASS |
| IV | Reproducibility & Transparency | Every pair/group stores evidence rows (shared terms, tags, reporter proximity). LLM labels flagged as generated and stored separately from scores; embedding model name+version + weights recorded in `run_metadata`. | ✅ PASS |
| V | Local-First Data | Issues + embeddings cached in SQLite; analysis re-runs without re-hitting YouTrack. `run_metadata` and per-issue `fetched_at` surface staleness. | ✅ PASS |
| VI | Simplicity | Stdlib `sqlite3`; small deps (`click`, `rich`, `numpy`, `ollama`). CLI only — no web layer (Datasette is an external viewer, not code we build). Threshold pairwise clustering before anything fancier. | ✅ PASS |
| VII | Test-First | Tokenization, structural signals, scoring, clustering are pure functions unit-tested on fixtures. Ollama + YouTrack behind interfaces with fakes; no live services in tests. | ✅ PASS |

**Result**: PASS — no violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-related-issue-finder/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI + interface contracts)
│   ├── cli.md
│   ├── youtrack-adapter.md
│   └── ollama-client.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/yt_issue_reviewer/
├── __init__.py
├── cli.py                    # click command group + subcommands (analyze, show, etc.)
├── config.py                 # config resolution: Ollama URL, model names, weights, threshold
├── ingest/
│   ├── __init__.py
│   ├── models.py             # Issue, IssueLink dataclasses (pure)
│   └── youtrack.py           # YouTrackSource interface + CliYouTrackSource (subprocess) + FakeYouTrackSource
├── analyze/
│   ├── __init__.py
│   ├── terms.py              # tokenization + significant-term extraction (pure)
│   ├── structural.py         # shared tags/components, reporter overlap, temporal proximity (pure)
│   ├── scoring.py            # weighted blend of semantic + structural (pure)
│   ├── clustering.py         # threshold pairwise grouping via union-find (pure)
│   └── evidence.py           # assemble human-readable evidence per pair/group (pure)
├── embeddings/
│   ├── __init__.py
│   └── ollama.py             # Embedder interface + OllamaEmbedder + FakeEmbedder; cosine similarity
├── llm/
│   ├── __init__.py
│   └── labeler.py            # Labeler interface + OllamaLabeler + FakeLabeler (flag-gated, presentation-only)
├── store/
│   ├── __init__.py
│   ├── schema.py             # SQLite DDL (Datasette-friendly)
│   └── repository.py         # typed read/write over the tables
└── report/
    ├── __init__.py
    └── terminal.py           # rich table rendering

tests/
├── unit/                     # terms, structural, scoring, clustering, evidence, cosine
├── integration/             # end-to-end run with FakeYouTrackSource + FakeEmbedder over a fixture corpus
└── fixtures/                # small issue corpora with known related sets

pyproject.toml               # uv-managed; Python 3.14+; deps + ruff + ty + pytest config
```

**Structure Decision**: Single-project CLI (Constitution VI — start as a CLI). Pure
analysis logic lives under `analyze/` and is import-clean (no I/O, no network) so it can
be unit-tested directly (Constitution VII). All external I/O — YouTrack, Ollama, SQLite —
sits behind small interfaces (`ingest/youtrack.py`, `embeddings/ollama.py`,
`llm/labeler.py`, `store/repository.py`) with fakes for tests. The SQLite file is both the
cache and the durable export, explored externally with a self-hosted Datasette (no web
code in this repo).

## Complexity Tracking

> No Constitution violations — this section intentionally left empty.
