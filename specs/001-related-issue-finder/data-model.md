# Phase 1 Data Model: Related Issue Finder

The SQLite database is both the local cache and the durable, shareable export. All tables
are **Datasette-friendly**: only `TEXT`, `INTEGER`, and `REAL` columns; embedding vectors
are stored as JSON-encoded text; no extensions or exotic types. All timestamps are stored
as ISO-8601 UTC strings.

Entities map to the spec's Key Entities: Issue, Existing Link, Related Group, Evidence,
Analysis Run, Export Artifact (the DB file itself).

## Table: `issues`

The locally cached issues (Constitution V). One row per issue per fetch.

| Column | Type | Notes |
|--------|------|-------|
| `issue_id` | TEXT PK | YouTrack readable id, e.g. `PROJ-123` |
| `project` | TEXT | Project short name |
| `number` | INTEGER | Issue number within project |
| `summary` | TEXT | Title (YouTrack `summary`) |
| `description` | TEXT | Body (may be empty) |
| `state` | TEXT | Extracted from `custom_fields` |
| `assignee` | TEXT | Extracted from `custom_fields`; nullable |
| `reporter` | TEXT | Reporter login/name |
| `tags` | TEXT | JSON array of tag/component names |
| `created` | TEXT | ISO-8601 UTC |
| `updated` | TEXT | ISO-8601 UTC |
| `content_hash` | TEXT | Hash of the exact embedded text (title+description) |
| `fetched_at` | TEXT | ISO-8601 UTC — when this row was fetched (staleness, FR-004) |
| `run_id` | TEXT FK→run_metadata.run_id | Run that fetched/refreshed this issue |

**Validation**: `issue_id` unique; `summary` required (may be short); `tags` valid JSON
array; `created`/`updated` parseable ISO-8601.

## Table: `issue_links`

Existing explicit YouTrack links — known relationships excluded from new findings
(FR-007).

| Column | Type | Notes |
|--------|------|-------|
| `source_id` | TEXT FK→issues.issue_id | |
| `target_id` | TEXT FK→issues.issue_id | |
| `link_type` | TEXT | e.g. `duplicates`, `relates to`, `depends on` |
| `run_id` | TEXT FK→run_metadata.run_id | |

**Validation**: `(source_id, target_id, link_type)` unique per run. Direction normalized
(store the pair as reported by YouTrack). A pair present here is suppressed from `pairs`
as a *new* finding.

## Table: `embeddings`

Cached embedding vectors (Constitution V; R3). Keyed to make unchanged issues
never re-embed.

| Column | Type | Notes |
|--------|------|-------|
| `issue_id` | TEXT | |
| `content_hash` | TEXT | Hash of embedded text |
| `model` | TEXT | Embedding model name |
| `model_version` | TEXT | Model digest/version if available (reproducibility, FR-011) |
| `dim` | INTEGER | Vector dimension (e.g. 768) |
| `vector` | TEXT | JSON array of floats |
| `created_at` | TEXT | ISO-8601 UTC |

**Primary key**: `(issue_id, content_hash, model)`. A cache hit requires all three to
match the current run's values.

## Table: `run_metadata`

One row per analysis run — captures scope, weights, models, and degradation state so a run
is reproducible and its staleness/settings are visible (Constitution IV, V).

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | TEXT PK | Unique run identifier (e.g. ULID/UUID) |
| `started_at` | TEXT | ISO-8601 UTC |
| `finished_at` | TEXT | ISO-8601 UTC; nullable until complete |
| `projects` | TEXT | JSON array of project filters |
| `state_filter` | TEXT | e.g. `open`, `all`; nullable |
| `date_from` | TEXT | ISO-8601 date; nullable |
| `date_to` | TEXT | ISO-8601 date; nullable |
| `min_score` | REAL | Minimum relatedness threshold applied |
| `embedding_model` | TEXT | Model name used for semantic similarity |
| `embedding_model_version` | TEXT | Digest/version; nullable |
| `weight_semantic` | REAL | Weight of semantic score in the blend |
| `weight_structural` | TEXT | JSON object of per-signal structural weights |
| `label_model` | TEXT | Chat model used for labels; null if labeling disabled |
| `degraded_structural_only` | INTEGER | 1 if Ollama was unreachable and semantic was skipped |
| `issue_count` | INTEGER | Number of issues considered |
| `tool_version` | TEXT | Version of this tool |

## Table: `pairs`

Scored candidate relationships between two issues, above threshold, excluding
already-linked pairs.

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | TEXT FK→run_metadata.run_id | |
| `issue_a` | TEXT FK→issues.issue_id | Ordered so `issue_a < issue_b` lexically |
| `issue_b` | TEXT FK→issues.issue_id | |
| `semantic_score` | REAL | Cosine similarity; null in degraded mode |
| `structural_score` | REAL | Blended structural signal score |
| `combined_score` | REAL | Final relatedness score used for ranking (FR-008) |

**Primary key**: `(run_id, issue_a, issue_b)`. Only pairs with `combined_score >=
min_score` and not present in `issue_links` are stored (FR-007, FR-018).

## Table: `groups`

Related groups formed from pairs via union-find (connected components).

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | TEXT FK→run_metadata.run_id | |
| `group_id` | TEXT | Unique within run |
| `rank` | INTEGER | 1 = highest group score (FR-012) |
| `group_score` | REAL | Representative relatedness score for the group |
| `size` | INTEGER | Number of member issues |
| `label` | TEXT | Generated one-line theme label; nullable |
| `label_is_generated` | INTEGER | 1 when `label`/`rationale` came from the LLM (FR-014) |
| `rationale` | TEXT | Short generated rationale; nullable |

**Primary key**: `(run_id, group_id)`. `label`/`rationale` populated only when labeling is
enabled and available; `label_is_generated=1` whenever they are LLM-produced.

## Table: `group_members`

Membership of issues in groups (a group has ≥2 members; an issue may appear in more than
one group only if the assignment rule allows — v1 uses connected components, so each
issue belongs to exactly one group per run).

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | TEXT FK→run_metadata.run_id | |
| `group_id` | TEXT FK→groups.group_id | |
| `issue_id` | TEXT FK→issues.issue_id | |

**Primary key**: `(run_id, group_id, issue_id)`.

## Table: `evidence`

Human-readable evidence for a pair and/or group — the transparency backbone
(Constitution IV; FR-009). Every reported relationship has ≥1 evidence row (SC-004).

| Column | Type | Notes |
|--------|------|-------|
| `run_id` | TEXT FK→run_metadata.run_id | |
| `group_id` | TEXT | Group this evidence supports; nullable if pair-scoped |
| `issue_a` | TEXT | First issue of the pair the evidence relates to |
| `issue_b` | TEXT | Second issue; nullable for group-wide evidence |
| `signal` | TEXT | One of: `shared_terms`, `shared_tags`, `same_reporter`, `temporal_proximity`, `semantic_similarity` |
| `detail` | TEXT | Human-readable text, e.g. "shared terms: login, timeout, 500" |
| `weight` | REAL | Contribution of this signal to the score; nullable |

**Validation**: `signal` from the enumerated set. At least one `evidence` row must exist
for every `pairs` row and every `groups` row that is reported.

## Relationships

```text
run_metadata 1───* issues
run_metadata 1───* issue_links
run_metadata 1───* pairs
run_metadata 1───* groups 1───* group_members *───1 issues
run_metadata 1───* evidence
issues       1───* embeddings   (by issue_id + content_hash + model)
groups       1───* evidence     (group_id)
pairs        1───* evidence     (issue_a, issue_b)
```

## Derived / in-memory types (not persisted as-is)

- **Issue** (`ingest/models.py`): dataclass mirroring the `issues` row plus parsed
  `links` list; the pure analysis layer consumes these, never the DB directly.
- **EmbeddingMatrix**: numpy array assembled from cached/fresh vectors for vectorized
  cosine similarity; ephemeral to a run.

## Notes on staleness & reproducibility

- `issues.fetched_at` + `run_metadata.started_at` make cache age visible (FR-004, SC-003).
- `embeddings.model`/`model_version` and `run_metadata.embedding_model*` + weights make any
  run reproducible (FR-011, Constitution IV).
- `groups.label_is_generated` guarantees generated text is always distinguishable from
  computed scores/evidence (FR-014).
