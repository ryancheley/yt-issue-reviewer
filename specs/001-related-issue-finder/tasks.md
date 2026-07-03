---

description: "Task list for Related Issue Finder implementation"
---

# Tasks: Related Issue Finder

**Input**: Design documents from `/specs/001-related-issue-finder/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: INCLUDED. The constitution (Principle VII — Test-First) and plan.md require
pure analysis logic to be unit-tested against fixtures, with YouTrack/Ollama behind
fakeable interfaces. Test tasks are therefore first-class here.

**Organization**: Phases follow the requested technical pipeline — ingest+cache →
embeddings+content-hash cache → similarity scoring → clustering/evidence/report/export →
LLM labels. Each task carries a `[US#]` label for traceability to the spec's user
stories. **Every phase ends with a runnable CLI command**, even before later phases exist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 (surface groups+evidence), US2 (filters), US3 (export), US4 (fast repeat runs)
- Exact file paths are included in every task.

## Path Conventions

Single-project CLI (per plan.md). Source under `src/yt_issue_reviewer/`, tests under
`tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling.

- [X] T001 Create the source/test tree per plan.md: `src/yt_issue_reviewer/{ingest,analyze,embeddings,llm,store,report}/__init__.py` and `tests/{unit,integration,fixtures}/` with `__init__.py` where needed
- [X] T002 Create `pyproject.toml` (uv-managed, Python 3.14+) declaring dependencies `click`, `rich`, `numpy`, `ollama`, and pinned `youtrack-cli`; dev deps `pytest`, `ruff`, `ty`
- [X] T003 [P] Configure `ruff` and `ty` sections in `pyproject.toml` and add `tests/conftest.py` with a fixtures-directory path helper
- [X] T004 [P] Create `README.md` stub describing the tool, privacy posture (Ollama-only, read-only YouTrack), and `uv sync` / `uv run` usage

**Checkpoint / runnable command**: `uv sync && uv run python -c "import yt_issue_reviewer"`
succeeds (package imports).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config, storage schema, domain models, interfaces, error types, and the CLI
skeleton — everything every later phase depends on. The `--label/--no-label` flag is
introduced here **default-off** so labels are flag-gated from the start.

**⚠️ CRITICAL**: No pipeline phase can begin until this is complete.

- [X] T005 [P] [US1] Define domain models `Issue` and `IssueLink` (frozen dataclasses) in `src/yt_issue_reviewer/ingest/models.py` per contracts/youtrack-adapter.md
- [X] T006 [P] [US1] Define shared error types `YouTrackUnavailable` and `OllamaUnavailable` in `src/yt_issue_reviewer/errors.py`
- [X] T007 [US1] Implement config resolution (Ollama host, model names, weights, threshold, db path) from env vars + TOML config in `src/yt_issue_reviewer/config.py` per contracts/cli.md
- [X] T008 [US1] Implement the Datasette-friendly SQLite DDL (tables `issues`, `issue_links`, `embeddings`, `pairs`, `groups`, `group_members`, `evidence`, `run_metadata`) in `src/yt_issue_reviewer/store/schema.py` per data-model.md
- [X] T009 [US1] Implement `Repository` open/create + `run_metadata` create/finish methods in `src/yt_issue_reviewer/store/repository.py` (opens db, applies schema idempotently)
- [X] T010 [P] [US1] Unit test schema+repository round-trip (create db, insert/read a `run_metadata` row) in `tests/unit/test_repository.py`
- [X] T011 [US1] Create the `click` command group with global options (`--db`, `--config`, `--ollama-host`, `-v`) and register empty subcommands `doctor`, `ingest`, `embed`, `analyze` (with `--label/--no-label` default off), `show`, `runs` in `src/yt_issue_reviewer/cli.py` per contracts/cli.md
- [X] T012 [US1] Wire the console entry point `yt-issue-reviewer` in `pyproject.toml` to `cli:main`

**Checkpoint / runnable command**: `uv run yt-issue-reviewer --help` lists all
subcommands; `uv run yt-issue-reviewer runs --db ./yir.db` creates the db and prints an
empty runs table.

---

## Phase 3: Ingest + SQLite Cache (Pipeline Stage 1)

**Goal**: Fetch issues through `youtrack_cli`, persist them to the cache, apply scope
filters, and expose staleness — all before any similarity work.

**Stories**: US1 (issues to analyze), US2 (project/state/date filters), US4 (fetched_at
staleness + reuse-on-unchanged).

**Independent Test**: With `FakeYouTrackSource` over a fixture corpus, `ingest` writes the
expected `issues`/`issue_links` rows, respects filters, and records `fetched_at`; a second
ingest of unchanged issues reuses cached rows.

### Tests for Phase 3

- [X] T013 [P] [US1] Contract tests for `YouTrackSource` (filters honored, `state`/`assignee` parsed, links present, read-only) in `tests/unit/test_youtrack_source.py` using `FakeYouTrackSource`
- [X] T014 [P] [US2] Unit tests for scope filtering (project, `--state open/all`, `--since/--until`) in `tests/unit/test_ingest_filters.py`
- [X] T015 [P] [US4] Unit test that unchanged issues are reused and `fetched_at` staleness is retrievable in `tests/unit/test_ingest_cache.py`
- [X] T016 [P] [US1] Fixture corpus with known-related and unrelated issues (incl. one pre-linked pair) in `tests/fixtures/issues_small.json`

### Implementation for Phase 3

- [X] T017 [US1] Define the `YouTrackSource` Protocol and `FakeYouTrackSource` (fixture-backed, filter-aware) in `src/yt_issue_reviewer/ingest/youtrack.py` per contracts/youtrack-adapter.md
- [X] T018 [US1] Implement `CliYouTrackSource`: invoke `yt issues list/search` as a subprocess with JSON output, parse `custom_fields` for `state`/`assignee`, normalize timestamps, and build `Issue`/`IssueLink` objects in `src/yt_issue_reviewer/ingest/youtrack.py`
- [X] T019 [US2] Apply project/state/date-range filtering in the source layer (query-scoped where possible, client-side for date range) in `src/yt_issue_reviewer/ingest/youtrack.py`
- [X] T020 [US1] Add `Repository` methods to upsert issues + links and compute/store `content_hash` and `fetched_at` in `src/yt_issue_reviewer/store/repository.py` per data-model.md
- [X] T021 [US4] Implement cache-reuse: skip re-fetch/re-write for issues whose content is unchanged unless `--refresh`, in `src/yt_issue_reviewer/store/repository.py`
- [X] T022 [US1] Implement the `doctor` command's YouTrack check (`yt` present + authenticated, read-only probe) in `src/yt_issue_reviewer/cli.py`
- [X] T023 [US1] Implement the `ingest` command: fetch → cache under a new `run_id` → print a `rich` table of fetched issues (id, project, state, summary, fetched_at) in `src/yt_issue_reviewer/cli.py`, rendered via `src/yt_issue_reviewer/report/terminal.py`

**Checkpoint / runnable command**:
`uv run yt-issue-reviewer ingest --project PROJ --state open --since 2026-01-01 --db ./yir.db`
fetches and caches issues and prints them; `uv run yt-issue-reviewer doctor` reports
YouTrack connectivity.

---

## Phase 4: Embedding Pipeline + Content-Hash Cache (Pipeline Stage 2)

**Goal**: Generate embeddings via self-hosted Ollama in batches, cache them keyed on
`(issue_id, content_hash, model)` so unchanged issues are never re-embedded — before any
scoring.

**Stories**: US1 (semantic vectors), US4 (embedding cache = near-instant repeat runs).

**Independent Test**: With `FakeEmbedder`, embedding a fixture corpus writes one
`embeddings` row per issue; re-running is a full cache hit; editing one issue re-embeds
only that issue. `cosine_matrix` is verified numerically.

### Tests for Phase 4

- [X] T024 [P] [US1] Contract test for `Embedder` (one vector per input, order-preserving, length `dim`) in `tests/unit/test_embedder.py` using `FakeEmbedder`
- [X] T025 [P] [US1] Unit test for `cosine_matrix` (symmetric, 1.0 diagonal, known pairs) in `tests/unit/test_cosine.py`
- [X] T026 [P] [US4] Unit test for embedding cache hit/miss on `(issue_id, content_hash, model)` incl. re-embed after content change in `tests/unit/test_embedding_cache.py`

### Implementation for Phase 4

- [X] T027 [US1] Define the `Embedder` Protocol, `FakeEmbedder` (deterministic vectors), and the pure `cosine_matrix` helper in `src/yt_issue_reviewer/embeddings/ollama.py` per contracts/ollama-client.md
- [X] T028 [US1] Implement `OllamaEmbedder`: `ollama.Client(host=...)` + batched `.embed()` (`/api/embed`), model task-prefix (nomic `search_document:`), and `check_available` via `client.list()` in `src/yt_issue_reviewer/embeddings/ollama.py`
- [X] T029 [US4] Add `Repository` methods to read/write cached vectors keyed on `(issue_id, content_hash, model)` and to select only cache-miss issues in `src/yt_issue_reviewer/store/repository.py`
- [X] T030 [US1] Implement the batching orchestration (chunk cache-miss issues, embed in batches, persist vectors + `model`/`model_version`/`dim`) in `src/yt_issue_reviewer/embeddings/ollama.py`
- [X] T031 [US1] Extend `doctor` with the Ollama reachability + required-model check (`/api/tags`) and actionable "run `ollama pull ...`" messaging in `src/yt_issue_reviewer/cli.py`
- [X] T032 [US1] Implement the `embed` command: ensure issues cached → embed missing → print a `rich` summary (embedded N, cache hits M, model) in `src/yt_issue_reviewer/cli.py`

**Checkpoint / runnable command**:
`uv run yt-issue-reviewer embed --project PROJ --db ./yir.db --ollama-host http://<host>:11434`
embeds issues and reports cache hits; a second run reports ~all cache hits.

---

## Phase 5: Similarity Scoring + Structural Signals (Pipeline Stage 3)

**Goal**: Produce ranked, threshold-filtered **pairs** with combined scores and evidence,
excluding already-linked pairs — testable against fixtures before any clustering.

**Stories**: US1 (relatedness scoring + evidence), US2 (`--min-score` threshold).

**Independent Test**: Over the fixture corpus with `FakeEmbedder`, known-related pairs
score above unrelated pairs; already-linked pairs are excluded; weights are recorded; each
pair has ≥1 evidence row.

### Tests for Phase 5

- [X] T033 [P] [US1] Unit tests for term extraction / significant shared terms in `tests/unit/test_terms.py`
- [X] T034 [P] [US1] Unit tests for structural signals (shared tags, reporter overlap, temporal proximity) in `tests/unit/test_structural.py`
- [X] T035 [P] [US1] Unit tests for the weighted blend + threshold filtering + link exclusion in `tests/unit/test_scoring.py`
- [X] T036 [P] [US1] Unit test that every retained pair yields ≥1 evidence item in `tests/unit/test_evidence.py`

### Implementation for Phase 5

- [X] T037 [P] [US1] Implement tokenization + significant-term extraction (pure) in `src/yt_issue_reviewer/analyze/terms.py`
- [X] T038 [P] [US1] Implement structural signals (pure): shared tags/components, reporter overlap, temporal proximity with configurable window, in `src/yt_issue_reviewer/analyze/structural.py`
- [X] T039 [US1] Implement the combined weighted scorer (pure) blending semantic cosine + structural signals in `src/yt_issue_reviewer/analyze/scoring.py`
- [X] T040 [US1] Implement evidence assembly (pure): map each contributing signal to a human-readable `evidence` record in `src/yt_issue_reviewer/analyze/evidence.py`
- [X] T041 [US1] Implement pair generation: vectorized cosine over the embedding matrix, apply `--min-score`, exclude pairs present in `issue_links`, in `src/yt_issue_reviewer/analyze/scoring.py`
- [X] T042 [US1] Add `Repository` methods to persist `pairs` and `evidence`, and record weights + models in `run_metadata`, in `src/yt_issue_reviewer/store/repository.py`
- [X] T043 [US1] Implement Ollama-unreachable degradation: catch `OllamaUnavailable`, set `degraded_structural_only=1`, score structural-only, warn to stderr (never a hosted fallback) in `src/yt_issue_reviewer/cli.py`
- [X] T044 [US1] Implement an interim `analyze` (no grouping yet): fetch → embed → score → persist → print a `rich` table of ranked pairs with scores + evidence in `src/yt_issue_reviewer/cli.py`

**Checkpoint / runnable command**:
`uv run yt-issue-reviewer analyze --project PROJ --min-score 0.6 --db ./yir.db --ollama-host http://<host>:11434`
prints ranked related **pairs** with evidence; pointing `--ollama-host` at a dead address
still completes with a structural-only warning.

---

## Phase 6: Clustering, Grouping, Evidence Report & Export (Pipeline Stage 4)

**Goal**: Group pairs into ranked related groups, render the full report, and make the
SQLite artifact a self-contained, re-displayable export.

**Stories**: US1 (ranked groups with evidence), US3 (durable export via `show`/`runs`).

**Independent Test**: Fixture pairs form the expected connected-component groups, ranked by
score; `show` re-renders a stored run with no network; unrelated issues stay ungrouped.

### Tests for Phase 6

- [X] T045 [P] [US1] Unit tests for union-find grouping (connected components, ranking, ungrouped singletons) in `tests/unit/test_clustering.py`
- [X] T046 [P] [US3] Unit test that `show` reconstructs groups/members/evidence from the db without any YouTrack/Ollama calls in `tests/unit/test_show_offline.py`
- [X] T047 [US1] Integration test: end-to-end `analyze` over the fixture corpus with `FakeYouTrackSource` + `FakeEmbedder` produces expected ranked groups, excludes pre-linked pair, every group has evidence, in `tests/integration/test_analyze_end_to_end.py`

### Implementation for Phase 6

- [X] T048 [US1] Implement threshold-based pairwise grouping via union-find (pure) producing ranked groups + members in `src/yt_issue_reviewer/analyze/clustering.py`
- [X] T049 [US1] Add `Repository` methods to persist `groups` and `group_members` and to read a full run back for display in `src/yt_issue_reviewer/store/repository.py`
- [X] T050 [US1] Implement the grouped report renderer (ranked groups: rank, score, members, per-pair evidence) in `src/yt_issue_reviewer/report/terminal.py`
- [X] T051 [US1] Upgrade `analyze` to run the full pipeline (fetch → embed → score → group → persist → render grouped report) in `src/yt_issue_reviewer/cli.py`
- [X] T052 [US3] Implement the `show` command (re-render a stored run from the db, optional display `--min-score`, no network) in `src/yt_issue_reviewer/cli.py`
- [X] T053 [US3] Implement the `runs` command (list `run_metadata`: id, started_at, projects, filters, models, weights, issue_count, degraded flag) exposing settings + staleness in `src/yt_issue_reviewer/cli.py`

**Checkpoint / runnable command**:
`uv run yt-issue-reviewer analyze --project PROJ --db ./yir.db` prints ranked **groups**
with evidence; `uv run yt-issue-reviewer show --db ./yir.db` re-renders offline;
`datasette ./yir.db` browses the tables.

---

## Phase 7: LLM-Generated Group Labels (Final Pipeline Stage, Flag-Gated)

**Goal**: When `--label` is passed, generate a one-line theme label + short rationale per
group via Ollama chat — marked generated, presentation-only, never affecting scores or
membership.

**Stories**: US1 (generated labels marked as generated).

**Independent Test**: Running `analyze` with and without `--label` over the same fixtures
yields identical groups/scores; labels are stored with `label_is_generated=1`; if the chat
model is unreachable, labeling is skipped with a warning and the run still succeeds.

### Tests for Phase 7

- [X] T054 [P] [US1] Contract test that `Labeler` output never changes groups/scores (compare `analyze` with vs without `--label` on fixtures) in `tests/unit/test_labeler_isolation.py`
- [X] T055 [P] [US1] Unit test that labels persist with `label_is_generated=1` and that an unreachable label model degrades to no-label-with-warning in `tests/unit/test_labeler.py`

### Implementation for Phase 7

- [X] T056 [US1] Define the `Labeler` Protocol, `GroupLabel` (always `is_generated=True`), and `FakeLabeler` in `src/yt_issue_reviewer/llm/labeler.py` per contracts/ollama-client.md
- [X] T057 [US1] Implement `OllamaLabeler`: `.chat()` with `stream=False` + temperature option (`/api/chat`), invoked only when `--label` is set, in `src/yt_issue_reviewer/llm/labeler.py`
- [X] T058 [US1] Add `Repository` methods to persist `label`/`rationale`/`label_is_generated` onto `groups` and record `label_model` in `run_metadata` in `src/yt_issue_reviewer/store/repository.py`
- [X] T059 [US1] Wire `--label`/`--label-model` into `analyze` (post-grouping, presentation-only) with skip-on-unreachable warning, and render labels marked "(generated)" alongside scores/evidence in `src/yt_issue_reviewer/cli.py` and `src/yt_issue_reviewer/report/terminal.py`

**Checkpoint / runnable command**:
`uv run yt-issue-reviewer analyze --project PROJ --label --label-model qwen2.5 --db ./yir.db --ollama-host http://<host>:11434`
prints groups with generated labels marked "(generated)"; the same run `--no-label`
produces identical groups.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, docs, and full validation.

- [X] T060 [P] Run `quickstart.md` validation scenarios end-to-end (all user stories + degraded mode) and record results
- [X] T061 [P] Update `README.md` with usage, config, models, and the Datasette export workflow
- [X] T062 [P] Add a `docs/` note listing yt-cli upstream-contribution candidates from research.md
- [X] T063 Ensure `uv run ruff check .`, `uv run ruff format --check .`, and `uv run ty check` all pass; fix findings
- [X] T064 Verify `uv run pytest` is green and that no test contacts a live YouTrack or Ollama (fakes only)

---

## Dependencies & Execution Order

### Phase (pipeline) dependencies — STRICT, per requested sequencing

- **Phase 1 (Setup)** → no deps.
- **Phase 2 (Foundational)** → after Phase 1. BLOCKS all pipeline phases.
- **Phase 3 (Ingest + cache)** → after Phase 2. MUST be complete + testable before Phase 4.
- **Phase 4 (Embeddings + content-hash cache)** → after Phase 3. MUST be complete +
  testable before Phase 5.
- **Phase 5 (Similarity scoring)** → after Phase 4. MUST be testable against fixtures
  before Phase 6.
- **Phase 6 (Clustering / report / export)** → after Phase 5.
- **Phase 7 (LLM labels)** → LAST. Flag-gated from Phase 2 (flag defined default-off),
  implemented only here.
- **Phase 8 (Polish)** → after Phase 7.

### User-story traceability

- **US1** (surface groups + evidence): spans Phases 3–7 (the core pipeline).
- **US2** (filters): ingest filters (Phase 3) + `--min-score` (Phase 5).
- **US3** (export): `show`/`runs` + durable artifact (Phase 6).
- **US4** (fast repeat runs): cache reuse (Phase 3) + embedding cache (Phase 4).

### Within each phase

- Tests are written first and expected to fail before implementation (Constitution VII).
- Pure analysis modules (`terms`, `structural`, `scoring`, `clustering`, `evidence`,
  `cosine`) have no I/O and can be built/tested independently.
- Repository persistence methods precede the CLI command that uses them.

---

## Parallel Opportunities

- Setup: T003, T004 in parallel.
- Foundational: T005, T006 in parallel; T010 parallel with CLI skeleton work.
- Each phase's test tasks (marked [P]) run in parallel before implementation.
- Pure analysis modules in Phase 5 (T037, T038) are independent files → parallel.

### Parallel Example: Phase 5 (Scoring)

```bash
# Tests first (parallel):
Task: "Unit tests for term extraction in tests/unit/test_terms.py"
Task: "Unit tests for structural signals in tests/unit/test_structural.py"
Task: "Unit tests for weighted blend + threshold in tests/unit/test_scoring.py"

# Then independent pure modules (parallel):
Task: "Implement term extraction in src/yt_issue_reviewer/analyze/terms.py"
Task: "Implement structural signals in src/yt_issue_reviewer/analyze/structural.py"
```

---

## Implementation Strategy

### MVP scope

The MVP is **US1 delivered through Phase 6** — a run that ingests, embeds (with cache),
scores, groups, and reports related issues with evidence, plus offline `show`/`runs`
export. Phase 7 (LLM labels) is a presentation-only enhancement layered on top.

### Incremental delivery (each ends with a runnable command)

1. Phases 1–2 → `--help` / empty `runs` table.
2. Phase 3 → `ingest` + `doctor` (issues cached, filters, staleness).
3. Phase 4 → `embed` (batched embeddings, cache hits on repeat).
4. Phase 5 → `analyze` prints ranked **pairs** with evidence (+ degraded mode).
5. Phase 6 → `analyze` prints ranked **groups**; `show`/`runs` export (MVP!).
6. Phase 7 → `analyze --label` adds generated labels.
7. Phase 8 → validate + lint/type/test green.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks.
- Constitution gates enforced by tasks: read-only YouTrack (no write subcommands),
  Ollama-only with structural-only degradation (T043), evidence on every relationship
  (T036/T040), recorded model+weights (T042), labels marked generated (T056–T059).
- Commit after each task or logical group; run `ruff` + `ty` + `pytest` before pushing
  (per project workflow).
- This repo is not yet under git — initialize and create the `001-related-issue-finder`
  feature branch before implementation begins.
