# Quickstart

Get from zero to a first related-issue analysis. Assumes the
[prerequisites](./installation.md) are met (uv, authenticated `yt`, reachable Ollama).

## 1. Check connectivity

```bash
uv run yt-issue-reviewer doctor --ollama-host http://<host>:11434
```

Expect `YouTrack (yt): OK` and `Ollama embeddings (nomic-embed-text): OK`.

## 2. Run an analysis

```bash
uv run yt-issue-reviewer analyze \
  --project PROJ \
  --state open \
  --min-score 0.6 \
  --ollama-host http://<host>:11434 \
  --db ./yir.db
```

This ingests issues (cached in `./yir.db`), embeds them, scores relatedness (semantic +
structural), groups the high-scoring pairs, and prints **ranked groups with evidence**.
Existing YouTrack links are excluded from new findings.

Add `--label` to get a generated one-line theme label per group (marked *(generated)* —
it never affects scores or membership).

## 3. Re-display or browse results

```bash
uv run yt-issue-reviewer show --db ./yir.db     # re-render the latest run, offline
uv run yt-issue-reviewer runs --db ./yir.db     # list runs + settings + staleness
datasette ./yir.db                              # browse all tables in a web UI
```

Repeat runs over unchanged issues are near-instant thanks to the embedding cache.

## What next

- Every command and flag: [CLI reference](./cli-reference.md).
- Tune models, weights, threshold: [configuration](./configuration.md).
- How scoring works: [architecture](./architecture.md).
- What leaves your infrastructure (nothing): [privacy & security](./privacy-and-security.md).

For the full validated walkthrough (including degraded-mode behavior), see
[`specs/001-related-issue-finder/quickstart.md`](https://github.com/ryancheley/yt-issue-reviewer/blob/main/specs/001-related-issue-finder/quickstart.md).
