# Privacy & Security

This project treats YouTrack data as potentially sensitive (operational or
healthcare-adjacent). The guarantees below are non-negotiable and enforced by the
[project constitution](../.specify/memory/constitution.md).

## What leaves your infrastructure: nothing

- **Self-hosted Ollama only.** All embedding and label generation runs against an Ollama
  instance you control. **No third-party hosted AI API** (OpenAI, Anthropic, etc.) is ever
  contacted — not even as a fallback.
- **Offline-capable AI audit.** The workflow security audit (`zizmor`) runs offline in CI.
- If Ollama is unreachable, the tool **degrades to structural-only scoring** with a warning
  rather than sending issue content anywhere else.

## Read-only against YouTrack

The tool **never** modifies, links, tags, comments on, transitions, or closes issues. There
are no write commands. All YouTrack access goes through the `youtrack_cli` package using
your existing, already-configured credentials — the tool stores none of its own.

## Local-first data

Fetched issues and embeddings are cached in a local SQLite file. Analysis re-runs without
re-contacting YouTrack, and `runs` surfaces how stale the cached data is.

## Reproducibility & transparency

Every surfaced relationship carries human-readable evidence, and each run records the
embedding model name/version and the scoring weights — so results are explainable and
reproducible. Any LLM-generated label is clearly marked as generated and never affects the
computed scores or group membership.

## Supply-chain posture

CI and release workflows use least-privilege permissions and hash-pinned actions, audited
by `zizmor` as a required check. Dependabot keeps those pins current. Releases publish via
PyPI Trusted Publishing (OIDC) — no long-lived token is stored.

See the [constitution](../.specify/memory/constitution.md) for the full set of principles.
