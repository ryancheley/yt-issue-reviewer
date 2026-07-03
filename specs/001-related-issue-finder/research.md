# Phase 0 Research: Related Issue Finder

All Technical Context unknowns are resolved below. Each entry records the decision, the
rationale, and the alternatives considered.

## R1. YouTrack integration surface (`youtrack_cli`)

**Decision**: Access YouTrack exclusively through the `youtrack_cli` package by invoking
the `yt` CLI as a subprocess with JSON output, wrapped behind a single
`YouTrackSource` adapter interface. Pin the `youtrack-cli` version.

**Rationale**:
- The package's public API surface is intentionally minimal — `youtrack_cli/__init__.py`
  exports only `__version__`. The internal classes (`AuthManager`, `IssueManager`, etc.)
  are undocumented, fully async, return dict envelopes, and can change between 0.x
  releases. The stable, supported contract is the CLI with JSON output.
- Satisfies Constitution III (all YouTrack access through the package; no parallel REST
  client) while insulating us from internal churn.
- Auth "just works": the CLI reads the existing shared config at
  `~/.config/youtrack-cli/.env` (or `YOUTRACK_BASE_URL` / `YOUTRACK_TOKEN` env vars), so
  we reuse the operator's already-configured authentication with zero extra handling.
- Read-only commands only (`yt issues list`, `yt issues search`) — nothing that mutates
  YouTrack, satisfying Constitution II.

**Field mapping notes** (from the `YouTrackIssue` model):
- `summary` is the **title**; `description` is the body.
- **`state` and `assignee` are NOT top-level fields** — in YouTrack they live inside
  `custom_fields`. The adapter must parse `custom_fields` to extract state/assignee, and
  the CLI convenience filters (`--state`, `--assignee`) can scope queries.
- Available: `id`, `project`, `number`, `created`, `updated`, `reporter`, `summary`,
  `description`, `custom_fields`, `tags`, `links`, plus more.
- Filtering by project/state and full YouTrack query language are supported.

**Alternatives considered**:
- *Import internal `IssueManager`/`AuthManager` directly*: rejected as the default —
  unstable, undocumented, async-forcing. Kept as a possible future fast path behind the
  same adapter interface if subprocess overhead ever matters.
- *Direct YouTrack REST client*: rejected — prohibited by Constitution III.

**Upstream contribution candidates** (per Constitution III, note rather than work
around): a documented, stable programmatic API / typed return objects; a first-class
"dump issues as JSON for a project/state/date-range" command if the current JSON output
proves awkward for bulk export. Record these as issues on `ryancheley/yt-cli`.

## R2. Embedding generation (Ollama)

**Decision**: Use the official `ollama` Python client's `.embed()` method (maps to
`POST /api/embed`), sending issues in **batches** (~50–100 texts per call via the list
`input`). Default model `nomic-embed-text` (768-dim). Embed `title + "\n\n" + description`
with the `search_document:` task prefix required by nomic.

**Rationale**:
- `/api/embed` supersedes the legacy `/api/embeddings` and is the only one that accepts a
  batch (`input: [...]` → `embeddings: [[...], ...]`, order-preserving). Batching is
  essential to keep a ~1,000-issue run within the "minutes" budget.
- `nomic-embed-text` is small, widely used, and 768-dim keeps vectors compact in SQLite.
  Model is configurable so `mxbai-embed-large` (1024-dim) can be swapped in.
- The model name+version is recorded per run and per cached embedding (Constitution IV,
  V), enabling reproducibility and correct cache invalidation.

**Prefix discipline**: nomic requires task prefixes — corpus embedded with
`search_document:`. (If cross-query search is added later, queries use `search_query:`.)
`mxbai-embed-large` needs no document prefix. The chosen prefix is a property of the model
and recorded alongside the model name.

**Alternatives considered**:
- *Legacy `/api/embeddings` one-at-a-time*: rejected — no batching, deprecated.
- *A hosted embedding API*: prohibited by Constitution I.

## R3. Embedding cache & invalidation

**Decision**: Cache embeddings in SQLite keyed on `(issue_id, content_hash, model)`,
where `content_hash` is a hash (e.g. SHA-256) of the exact embedded text. On each run,
compute the hash per issue; reuse the cached vector when `(issue_id, content_hash,
model)` matches, otherwise (re)embed.

**Rationale**: Unchanged issues are never re-embedded (near-instant repeat runs, SC-003);
a changed title/description changes the hash and forces re-embedding (FR-005); switching
models naturally produces new rows without clobbering old ones (reproducibility).

**Alternatives considered**: Keying on `updated` timestamp alone — rejected because it
misses content-equivalent edits and re-embeds on no-op touches; content hash is exact.

## R4. Structural signals (local, no LLM)

**Decision**: Compute three structural signals purely locally:
- **Shared tags/components**: overlap (e.g. Jaccard) of tag/component sets.
- **Reporter overlap**: same reporter, weighted by temporal proximity.
- **Temporal proximity**: closeness of created dates, with a configurable "short window"
  default (issues by the same reporter within a few days score higher).

**Rationale**: These are cheap, deterministic, explainable signals that also provide
human-readable evidence (Constitution IV) and work even when Ollama is unavailable
(degraded mode). All pure functions → directly unit-testable (Constitution VII).

**Alternatives considered**: TF-IDF term overlap as a fourth signal — kept as
evidence-generation (significant shared terms) but not required as a scored signal in
v1; can be promoted if pairwise output is noisy.

## R5. Combined scoring

**Decision**: Final score = weighted blend of the semantic (cosine) score and the
structural signals. Weights are configurable and **recorded per run** in `run_metadata`.
When Ollama is unavailable, the semantic weight is dropped and the score is
structural-only, flagged in `run_metadata`.

**Rationale**: A configurable, recorded blend keeps runs reproducible and lets the
operator tune precision/recall. Graceful degradation satisfies the fail-soft constraint
without ever egressing content.

**Alternatives considered**: A fixed hardcoded blend — rejected; Constitution IV requires
weights be recorded and the spec calls for tunability.

## R6. Clustering / grouping

**Decision**: Start with **threshold-based pairwise grouping**: compute pairwise scores,
keep pairs at or above the minimum threshold, then group via union-find (connected
components) into related groups. Exclude pairs already connected by an explicit YouTrack
link from *new* findings.

**Rationale**: Simplest thing that works (Constitution VI); fully deterministic and
testable. Union-find is trivial and pure.

**Alternatives considered**: Agglomerative/hierarchical clustering — deferred. Only
adopt if pairwise output proves noisy in real use (explicitly flagged as a follow-up, not
built speculatively). Recorded here so the evaluation criterion is on record.

**Pairwise cost note**: ~1,000 issues → ~500k pairs, well within memory/time using
vectorized numpy cosine over the embedding matrix; no approximate-NN index needed at this
scale.

## R7. LLM-assisted labels (flag-gated, presentation-only)

**Decision**: Behind an explicit flag, call Ollama `/api/chat` (`stream: false`) with a
small chat model (e.g. `qwen2.5` / `llama3.x` class) to generate a one-line label + short
rationale per surfaced group. Store labels in their own table, marked as generated. They
**never** feed back into scores or group membership.

**Rationale**: Keeps a flaky/absent model from changing the analysis (determinism of
findings preserved); labels are pure presentation sugar. Marking as generated and keeping
scores/evidence visible alongside satisfies Constitution IV.

**Alternatives considered**: Always-on labeling — rejected; it would make every run
depend on chat-model availability and slow the common path. Flag-gated is opt-in.

## R8. Ollama connectivity & graceful degradation

**Decision**: Ollama base URL is configurable via `OLLAMA_HOST` env var or the tool's
config file (Tailscale addresses supported); the client is constructed with an explicit
`host=`. On startup for any Ollama-dependent step, probe reachability via `client.list()`
(`GET /api/tags`) and verify the required model is present. If unreachable: emit a clear
error and **degrade to structural-signals-only scoring with a warning**; if the labeling
model is unreachable, skip labels with a warning. Never fall back to a hosted service.

**Rationale**: Directly implements the plan constraint and Constitution I. Probing
`/api/tags` lets us fail fast with an actionable message ("model not pulled: run `ollama
pull ...`") instead of mid-run.

**Alternatives considered**: Hard failure when Ollama is down — rejected; the spec wants
graceful degradation to structural-only, and structural signals still deliver value.

## R9. Storage schema (Datasette-friendly SQLite)

**Decision**: Plain SQLite tables (`issues`, `issue_links`, `embeddings`, `pairs`,
`groups`, `group_members`, `evidence`, `run_metadata`) with only TEXT/INTEGER/REAL
columns. Embedding vectors stored as JSON text (portable, inspectable) — no exotic types,
no extensions required, so a self-hosted Datasette can browse everything directly. The
same file is the cache and the durable export (Constitution V; FR-019/FR-020).

**Rationale**: Datasette compatibility and zero-dependency portability. JSON-encoded
vectors are trivially decoded to numpy at load; at 1k issues the storage cost is
negligible.

**Alternatives considered**: A vector extension (sqlite-vec) or float BLOBs — rejected for
v1 as unnecessary complexity (Constitution VI) and potentially not Datasette-friendly;
revisit only if scale grows well beyond a few thousand issues.

## R10. CLI framework & output

**Decision**: `click` for the CLI (consistent with yt-cli conventions), `rich` for
terminal tables. Subcommands cover running an analysis (with `--project`, `--state`,
`--since/--until`, `--min-score`, `--label` flags) and re-displaying a stored run from the
SQLite artifact.

**Rationale**: Matches the ecosystem the operator already uses; `rich` gives readable
ranked-group tables. Both are small, well-maintained (Constitution VI).

**Alternatives considered**: `typer` — acceptable per constraints, but `click` matches
yt-cli directly and avoids an extra abstraction layer.

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| yt-cli integration path | Subprocess `yt ... --format json` behind a `YouTrackSource` adapter |
| Reusing auth | Shared `~/.config/youtrack-cli/.env` / env vars — no extra handling |
| state/assignee location | Inside `custom_fields`; adapter parses them out |
| Embedding endpoint | `/api/embed` (batch) via official `ollama` client `.embed()` |
| Default embedding model | `nomic-embed-text` (768-dim, `search_document:` prefix), configurable |
| Cache key | `(issue_id, content_hash, model)` |
| Clustering | Threshold pairwise + union-find; agglomerative deferred |
| Labels | Flag-gated `/api/chat`, presentation-only, marked generated |
| Ollama down | Clear error + degrade to structural-only; never egress to hosted AI |
| Storage | Plain Datasette-friendly SQLite; vectors as JSON text |
