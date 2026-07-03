<!--
Sync Impact Report
==================
Version change: (template / unratified) → 1.0.0
Bump rationale: Initial ratification. First concrete constitution replacing the
  unfilled template; establishes the full governance baseline (MINOR/PATCH
  semantics start applying to subsequent amendments).

Modified principles: N/A (initial adoption)
Added principles:
  - I. Privacy and Data Boundaries (NON-NEGOTIABLE)
  - II. Read-Only by Default
  - III. Build on yt-cli
  - IV. Reproducibility and Transparency
  - V. Local-First Data
  - VI. Simplicity
  - VII. Test-First
Added sections:
  - Technology and Dependency Constraints
  - Development Workflow and Quality Gates
  - Governance

Removed sections: None

Templates requiring updates:
  - .specify/templates/plan-template.md ✅ no change needed (Constitution Check
    gate references the constitution dynamically; gates derived at plan time)
  - .specify/templates/spec-template.md ✅ no change needed (no constitution refs)
  - .specify/templates/tasks-template.md ✅ no change needed (no constitution refs)
  - .specify/extensions/agent-context/* ✅ no change needed (context refresh only)

Follow-up TODOs: None. Ratification date set to today (initial adoption).
-->

# YouTrack Issue Reviewer Constitution

## Core Principles

### I. Privacy and Data Boundaries (NON-NEGOTIABLE)

YouTrack issues may contain sensitive operational or healthcare-adjacent information.
Issue content — including titles, descriptions, and comments — MUST never leave
infrastructure the user controls. All LLM and embedding operations MUST run against a
self-hosted Ollama instance. Third-party hosted AI APIs (OpenAI, Anthropic, and any
other externally hosted inference or embedding service) are PROHIBITED for issue
content, without exception and without fallback. There is no "degraded mode" that ships
issue data to an external provider; if the local Ollama instance is unavailable, the
operation fails loudly rather than falling back to a hosted service.

**Rationale**: The data may be regulated or operationally confidential. A single
exfiltration path — even a well-intentioned fallback — defeats the entire trust model,
so the boundary is absolute rather than best-effort.

### II. Read-Only by Default

This tool analyzes issues; it MUST NOT modify, link, tag, comment on, transition, or
close issues in YouTrack as a side effect of analysis. Any write action MUST be
explicitly requested by the user AND gated behind a distinct confirmation step that
names what will change before it happens. The default execution path — running an
analysis — is guaranteed to leave YouTrack unchanged.

**Rationale**: An analysis tool that silently mutates the system of record erodes trust
and risks corrupting real project data. Making writes opt-in and confirmed keeps the
tool safe to run freely.

### III. Build on yt-cli

All YouTrack API interaction MUST go through the yt-cli package (`youtrack_cli`).
Writing a parallel HTTP client against the YouTrack REST API is PROHIBITED. When yt-cli
lacks a needed capability, the gap MUST be recorded as a candidate upstream
contribution (issue or note) rather than worked around with a bespoke client.

**Rationale**: A single, shared client concentrates authentication, rate-limiting, and
API-compatibility concerns in one maintained place. Divergent clients drift, duplicate
bugs, and fragment the ecosystem; upstreaming improvements benefits everyone.

### IV. Reproducibility and Transparency

Every "relatedness" score MUST be explainable. Embedding similarity scores MUST always
be presented alongside human-readable evidence — shared significant terms, common tags,
and structural signals. When an LLM generates a summary or rationale for a group, that
output MUST be labeled as generated, and the underlying similarity scores and evidence
MUST remain visible next to it. The embedding model name and version MUST be recorded
with every analysis run so that results can be reproduced.

**Rationale**: Opaque scores invite blind trust or blanket dismissal. Pairing numbers
with evidence lets users judge results, and recording the model provenance makes any
run auditable and repeatable.

### V. Local-First Data

Fetched issue data MUST be cached locally (SQLite) so that analysis can be re-run
without re-hitting the YouTrack API. Cache staleness MUST be visible to the user —
runs surface when the underlying data was fetched so the user can decide whether to
refresh.

**Rationale**: Local caching makes iteration fast, keeps the tool usable offline, and
reduces API load. Surfacing staleness prevents silently reasoning over outdated data.

### VI. Simplicity

Prefer the Python standard library and small, well-maintained dependencies over large
frameworks. The project targets Python 3.12+, is managed with uv, tested with pytest,
and linted with ruff. It starts as a CLI; a web layer is only justified AFTER the
analysis core has proven useful, and adding one MUST be explicitly justified against
this principle.

**Rationale**: Every dependency and layer is a maintenance and security liability.
Staying small keeps the tool auditable — which reinforces the privacy boundary — and
avoids building UI before the core delivers value.

### VII. Test-First

Analysis logic — tokenization, similarity scoring, and clustering — MUST be pure and
unit-tested. API and Ollama interactions MUST sit behind interfaces so they can be
faked in tests without network access. Tests for analysis logic SHOULD be written
before or alongside the implementation, and MUST NOT depend on a live YouTrack or
Ollama instance.

**Rationale**: Pure, tested analysis logic is where correctness matters most and where
regressions are easiest to introduce. Interface boundaries keep the test suite fast,
deterministic, and runnable offline — consistent with the local-first, privacy-first
posture.

## Technology and Dependency Constraints

- **Language/runtime**: Python 3.12 or newer.
- **Package/environment management**: uv.
- **Testing**: pytest, with analysis logic covered by fast, offline unit tests.
- **Linting/formatting**: ruff; the type checker is ty (not mypy, not pyright).
- **Data cache**: SQLite, local to the user's machine.
- **AI inference/embeddings**: self-hosted Ollama only (see Principle I).
- **YouTrack access**: the `youtrack_cli` package only (see Principle III).
- New dependencies MUST be small and well-maintained; adding a heavyweight framework or
  a network-dependent AI service requires an explicit exception recorded in the plan's
  Complexity Tracking and MUST NOT violate Principle I.

## Development Workflow and Quality Gates

- Work happens on feature branches; direct pushes to `main` are not permitted.
- Before pushing, ruff (lint/format) and ty (type check) MUST pass; pytest MUST pass.
- Every plan and PR MUST verify compliance with the Core Principles; the plan
  Constitution Check gate is derived from this document and MUST be satisfied before
  Phase 0 research and re-checked after Phase 1 design.
- Any write path to YouTrack MUST demonstrate its explicit-request-plus-confirmation
  design (Principle II) before it can merge.
- Any code path touching issue content MUST demonstrate that content stays within
  user-controlled infrastructure (Principle I) before it can merge.

## Governance

This constitution supersedes other development practices for this project. When a
practice and a principle conflict, the principle wins.

- **Amendments**: Proposed as a change to this file, with rationale, accompanied by any
  updates to dependent templates and docs. Amendments take effect once merged to `main`.
- **Versioning**: Semantic versioning of the constitution itself.
  - MAJOR: backward-incompatible governance changes — removing or redefining a
    principle in a way that invalidates prior compliance.
  - MINOR: adding a principle or section, or materially expanding guidance.
  - PATCH: clarifications, wording, and non-semantic refinements.
- **Compliance review**: Plans, specs, and PRs are reviewed against these principles.
  Principle I (Privacy and Data Boundaries) and Principle II (Read-Only by Default) are
  non-negotiable gates — a violation blocks merge regardless of other considerations.
- **Runtime guidance**: Agent and contributor runtime guidance lives in `CLAUDE.md` and
  the active plan; those documents MUST NOT contradict this constitution.

**Version**: 1.0.0 | **Ratified**: 2026-07-02 | **Last Amended**: 2026-07-02
