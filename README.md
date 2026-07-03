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

## Quickstart

```bash
uv sync
uv run yt-issue-reviewer doctor --ollama-host http://<host>:11434
uv run yt-issue-reviewer analyze --project PROJ --state open --min-score 0.6 --db ./yir.db
uv run yt-issue-reviewer show --db ./yir.db      # re-display a stored run, offline
datasette ./yir.db                                # browse results externally
```

Prerequisites: [uv](https://docs.astral.sh/uv/), an authenticated `youtrack-cli`, and a
reachable self-hosted Ollama with `nomic-embed-text` pulled. Full walkthrough in
[docs/quickstart.md](./docs/quickstart.md).

## Documentation

| Doc | What it covers |
|-----|----------------|
| [Installation](./docs/installation.md) | Prerequisites and install |
| [Quickstart](./docs/quickstart.md) | Zero → first analysis |
| [CLI reference](./docs/cli-reference.md) | Every command, flag, and exit code |
| [Configuration](./docs/configuration.md) | Env vars + `config.toml` with defaults |
| [Architecture](./docs/architecture.md) | The hybrid scoring pipeline |
| [Privacy & security](./docs/privacy-and-security.md) | What leaves your infra (nothing) |
| [Releasing](./docs/releasing.md) | Tag-driven PyPI release process |
| [Contributing](./CONTRIBUTING.md) | The `just check` gate and PR workflow |

The full spec, plan, and contracts live under `specs/001-related-issue-finder/`.

## Development

```bash
just --list      # all developer recipes
just check       # the exact CI gate: ruff, ruff format, ty, pytest, zizmor
```

See [CONTRIBUTING.md](./CONTRIBUTING.md). Licensed under the [MIT License](./LICENSE).
