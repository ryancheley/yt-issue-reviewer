# CLI Reference

`yt-issue-reviewer [GLOBAL OPTIONS] COMMAND [ARGS]`. This mirrors the command contract in
[`specs/001-related-issue-finder/contracts/cli.md`](../specs/001-related-issue-finder/contracts/cli.md).

## Global options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--db PATH` | `YIR_DB` | `yir.db` | SQLite cache + results file (the durable export) |
| `--config PATH` | — | `~/.config/yt-issue-reviewer/config.toml` | Config file (flag only) |
| `--ollama-host URL` | `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL (Tailscale ok) |
| `-v, --verbose` | — | off | Verbose output to stderr |

## Commands

### `doctor`
Check connectivity (read-only): `yt` present + authenticated, Ollama reachable + model
present. Exits non-zero if a check fails.

### `ingest`
Fetch issues from YouTrack and cache them locally; prints a table of fetched issues.
Options: `-p/--project` (repeatable, required), `--state [open|all]` (default `open`),
`--since DATE`, `--until DATE`.

### `embed`
Ensure issues are cached and embedded; reports how many were embedded vs cache hits.
Options: the `ingest` options plus `--embedding-model TEXT`.

### `analyze`
Run the full pipeline (fetch → embed → score → group → report) and print ranked groups
with evidence. Options:

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --project TEXT` (repeatable) | required | Project(s) to include |
| `--state [open\|all]` | `open` | Issue-state filter |
| `--since DATE` / `--until DATE` | — | Created/updated date range |
| `--min-score FLOAT` | `0.6` | Minimum relatedness threshold |
| `--embedding-model TEXT` | `nomic-embed-text` | Ollama embedding model |
| `--weight-semantic FLOAT` | `0.7` | Weight of the semantic score |
| `--weight-structural FLOAT` | `0.3` | Weight of the structural signals |
| `--label / --no-label` | `--no-label` | Generate group labels (flag-gated) |
| `--label-model TEXT` | `qwen2.5` | Chat model used when `--label` is set |
| `--refresh / --no-refresh` | `--no-refresh` | Ignore cache and re-fetch |

If Ollama is unreachable, `analyze` prints a warning and **degrades to structural-only
scoring** (exit 0) — it never contacts a hosted service.

### `show`
Re-display a stored run from the database with no network access. Options: `--run-id TEXT`
(default: latest), `--min-score FLOAT` (re-filter for display).

### `runs`
List stored runs with their settings (projects, filters, models, weights), issue counts,
and whether the run was degraded — surfacing data staleness.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (including a successful structural-only degraded run) |
| 1 | Usage error (bad flags, no project) |
| 2 | YouTrack access failed (missing/unauthenticated `yt`) |
| 3 | Fatal internal error |

There are **no** write commands — the tool never modifies YouTrack.
