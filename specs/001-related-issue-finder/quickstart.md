# Quickstart & Validation Guide: Related Issue Finder

This guide proves the feature works end-to-end. It covers prerequisites, setup, running
an analysis, and validating each user story's acceptance criteria. Implementation details
live in `plan.md`, `data-model.md`, and `contracts/`.

## Prerequisites

- Python 3.14+ and [uv](https://docs.astral.sh/uv/).
- `youtrack-cli` installed and authenticated (`yt auth login`) — the tool reuses this
  existing configured auth. Verify: `yt issues list --project-id <PROJ> --state Open`.
- A self-hosted Ollama instance reachable from this machine (localhost or a Tailscale
  address). Pull the models:
  ```bash
  ollama pull nomic-embed-text        # embeddings (768-dim)
  ollama pull qwen2.5                  # only needed for --label
  ```

## Setup

```bash
uv sync                      # install deps from pyproject.toml (Python 3.14+)
uv run yt-issue-reviewer doctor \
  --ollama-host http://<tailscale-host>:11434
```

`doctor` must report: `yt` present + authenticated, Ollama reachable, required model(s)
present. This validates connectivity before any analysis.

## Run an analysis (User Story 1 + 2)

```bash
uv run yt-issue-reviewer analyze \
  --project PROJ \
  --state open \
  --since 2026-01-01 \
  --min-score 0.6 \
  --ollama-host http://<tailscale-host>:11434 \
  --db ./yir.db
```

**Expected**: ranked group tables in the terminal. Each group shows a rank, a relatedness
score, member issues (id, project, summary), and human-readable evidence per pair
(shared terms / tags / same reporter / temporal proximity / semantic similarity). All
results are written to `./yir.db`.

## Validation scenarios

### US1 — Surface related groups with evidence (P1)

1. Run `analyze` over a project known to contain near-duplicate issues.
2. **Verify**: at least one group contains the known-related issues (SC-001).
3. **Verify**: every reported pair/group has ≥1 evidence line (SC-004; `evidence` table
   non-empty for each `pairs`/`groups` row).
4. **Verify**: a pair already linked in YouTrack does **not** appear as a new finding
   (FR-007, SC-006) — confirm it's absent from `pairs`.
5. **Verify**: an unrelated issue is not forced into any group (FR-010).

### US1 — Generated labels are marked (P1, flag-gated)

```bash
uv run yt-issue-reviewer analyze --project PROJ --label --label-model qwen2.5 [...]
```

**Verify**: each group shows a one-line label marked "(generated)"; the score and evidence
remain visible alongside it (FR-014). Re-run **without** `--label` and confirm the groups
and scores are **identical** — labels never change the analysis (R7, contract test).

### US2 — Filters (P2)

- Run with `--state open` then `--state all`; **verify** closed issues appear only in the
  `all` run (FR-016).
- Run with two different `--min-score` values; **verify** the higher threshold reports
  fewer/no low-scoring groups (FR-018).
- Run with a narrow `--since/--until`; **verify** only in-range issues are considered
  (FR-017).
- Run with two `--project` flags; **verify** groups may span projects (FR-015).

### US3 — Export / durable artifact (P2)

```bash
uv run yt-issue-reviewer show --db ./yir.db          # re-display latest run
uv run yt-issue-reviewer runs --db ./yir.db          # list runs + settings/staleness
datasette ./yir.db                                   # browse externally (no code we ship)
```

**Verify**: `show` renders the stored groups/evidence/labels **without** contacting
YouTrack or Ollama (SC-008, FR-020). Copy `yir.db` to another machine and repeat — a
teammate sees the same findings.

### US4 — Fast repeat runs (P3)

1. Time a first `analyze` run over ~1,000 issues → completes in minutes, dominated by the
   embedding pass (SC-002).
2. Re-run the identical command over unchanged issues → **verify** it is dramatically
   faster (embedding cache hits on `(issue_id, content_hash, model)`) (SC-003).
3. Edit one issue's title in YouTrack, re-run → **verify** only that issue is re-embedded
   and the change is reflected (FR-005).
4. **Verify**: `runs` shows the age of the reused data (FR-004).

### Degraded mode — Ollama unreachable (Constitution I)

1. Point `--ollama-host` at an unreachable address and run `analyze`.
2. **Verify**: a clear warning is printed, the run completes with **structural-only**
   scoring, `run_metadata.degraded_structural_only = 1`, exit code 0, and **no** issue
   content is sent anywhere (no hosted-AI fallback) (SC-009).

## Automated test entry points

```bash
uv run pytest                          # full suite
uv run pytest tests/unit               # pure analysis logic on fixture corpora
uv run pytest tests/integration        # end-to-end with FakeYouTrackSource + FakeEmbedder
uv run ruff check . && uv run ty check # lint + type-check (must pass before push)
```

Unit tests validate tokenization, structural signals, scoring, clustering, and cosine
similarity against small fixture corpora with known-related sets — no live YouTrack or
Ollama required (Constitution VII).
