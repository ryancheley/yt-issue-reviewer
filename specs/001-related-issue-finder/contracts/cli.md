# CLI Contract: `yt-issue-reviewer`

The tool exposes a `click` command group. This contract defines commands, flags, exit
codes, and behavior. It is the user-facing interface for the feature.

## Command group

```text
yt-issue-reviewer [OPTIONS] COMMAND [ARGS]...
```

Global options:

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--db PATH` | `YIR_DB` | `./yir.db` | SQLite cache/results file (the durable export) |
| `--config PATH` | `YIR_CONFIG` | `~/.config/yt-issue-reviewer/config.toml` | Config file |
| `--ollama-host URL` | `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama base URL (Tailscale ok) |
| `-v, --verbose` | — | off | Verbose logging to stderr |

## `analyze` — run an on-demand analysis (US1, US2, US4)

```text
yt-issue-reviewer analyze [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `-p, --project TEXT` (repeatable) | required (≥1) | Project(s) to include (FR-015) |
| `--state [open\|all]` | `open` | Issue state filter (FR-016) |
| `--since DATE` | none | Only issues created/updated on/after DATE (FR-017) |
| `--until DATE` | none | Only issues created/updated on/before DATE (FR-017) |
| `--min-score FLOAT` | `0.6` | Minimum relatedness threshold (FR-018) |
| `--embedding-model TEXT` | `nomic-embed-text` | Ollama embedding model |
| `--weight-semantic FLOAT` | `0.7` | Weight of semantic score (recorded per run) |
| `--weight-structural FLOAT` | `0.3` | Weight of structural signals (recorded per run) |
| `--label / --no-label` | `--no-label` | Flag-gate LLM label+rationale (US1, R7) |
| `--label-model TEXT` | `qwen2.5` | Chat model used when `--label` is set |
| `--refresh / --no-refresh` | `--no-refresh` | Force re-fetch from YouTrack ignoring cache |

**Behavior**:
1. Resolve scope; fetch issues via the YouTrack adapter (subprocess `yt`), reusing cached
   rows whose content is unchanged unless `--refresh`.
2. Embed issues via Ollama in batches, reusing cached vectors keyed on
   `(issue_id, content_hash, model)`.
3. Compute structural signals; blend into `combined_score`; drop pairs below `--min-score`
   and pairs already linked in YouTrack.
4. Group via union-find; rank groups; if `--label`, generate labels (marked generated).
5. Persist everything under a new `run_id`; render ranked groups as rich tables.

**Ollama-unreachable behavior**: print a clear warning to stderr, set
`degraded_structural_only=1`, score with structural signals only, and continue (exit 0
with warning). Never contact any hosted AI service. If `--label` was requested but the
chat model is unreachable, skip labels with a warning.

**Output (stdout)**: ranked group tables — for each group: rank, score, generated label
(if any, marked "(generated)"), and member rows with issue id, project, summary, and the
evidence per member/pair.

## `show` — re-display a stored run (US3)

```text
yt-issue-reviewer show [OPTIONS]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--run-id TEXT` | latest | Which stored run to display |
| `--min-score FLOAT` | none | Optional re-filter of stored groups for display |

**Behavior**: reads groups/members/evidence/labels from the SQLite file and renders them
without contacting YouTrack or Ollama (FR-020, SC-008). Proves the durable artifact is
self-contained.

## `runs` — list stored runs

```text
yt-issue-reviewer runs
```

Lists `run_metadata` rows: run id, started_at, projects, filters, models, weights,
issue_count, and whether degraded — so staleness and settings are visible (FR-004,
Constitution IV/V).

## `doctor` — check connectivity

```text
yt-issue-reviewer doctor
```

Checks: `yt` CLI present and authenticated (read-only probe); Ollama reachable at
configured host (`/api/tags`) and required models present. Prints actionable messages
(e.g. "run `ollama pull nomic-embed-text`"). Never writes to YouTrack.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (including successful degraded-mode run) |
| 1 | Usage error (bad flags, no project given) |
| 2 | YouTrack access failed (auth/CLI missing) — no partial writes to DB |
| 3 | Fatal internal error |

Note: Ollama being unreachable is **not** a fatal error for `analyze` — it degrades to
structural-only and exits 0 with a warning.

## Invariants (constitution-aligned)

- No subcommand ever performs a YouTrack write (Constitution II). There is no `link`,
  `merge`, `tag`, or `close` command in this version.
- No subcommand ever sends issue content to a non-Ollama, non-user-controlled service
  (Constitution I).
