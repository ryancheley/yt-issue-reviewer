# Related Issue Finder (`yt-issue-reviewer`)

A run-on-demand CLI that helps a team lead find **related issues** across a YouTrack
instance — probable duplicates, issues about the same feature/root cause, and issues with
overlapping subject matter worded differently — so they can be merged, recognized, and
consolidated.

## Privacy & boundaries (non-negotiable)

- **Read-only** against YouTrack. This tool never links, merges, tags, or closes issues.
- **Self-hosted Ollama only** for embeddings and optional labels. Issue content never
  leaves infrastructure you control; there is no third-party hosted-AI fallback.
- All YouTrack access goes through the `youtrack_cli` package (the `yt` CLI).

## How it works

1. **Ingest** issues via `yt` and cache them locally in SQLite (Datasette-friendly).
2. **Embed** title+description via Ollama, caching vectors on
   `(issue_id, content_hash, model)` so unchanged issues are never re-embedded.
3. **Score** relatedness = weighted blend of semantic cosine similarity + local
   structural signals (shared tags, reporter overlap, temporal proximity).
4. **Group** high-scoring pairs into ranked groups (existing YouTrack links excluded).
5. **Report** ranked groups with human-readable evidence; optionally add a flag-gated,
   generated one-line label per group.

## Usage

```bash
uv sync
uv run yt-issue-reviewer doctor --ollama-host http://<host>:11434
uv run yt-issue-reviewer analyze --project PROJ --state open --min-score 0.6 --db ./yir.db
uv run yt-issue-reviewer show --db ./yir.db      # re-display a stored run, offline
datasette ./yir.db                                # browse results externally
```

See `specs/001-related-issue-finder/` for the full spec, plan, and contracts.
