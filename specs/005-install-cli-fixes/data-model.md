# Phase 1 Data Model: Cross-Platform Install and CLI Robustness Fixes

**No new domain entities.** This feature changes packaging, subprocess invocation, and CLI option
wiring. It introduces, removes, or alters **no** persisted data, schema, or domain model.

Existing structures that are *touched but not changed in shape*:

- **`Config`** (`config.py`) — resolved runtime configuration. This feature reuses its existing
  `db_path` / `ollama_host` fields and `Config.load(...)` precedence (explicit > env > TOML >
  default). No field is added or removed; only *when* it is loaded changes (per-command instead of
  once at the group). See [contracts/cli-options.md](./contracts/cli-options.md).
- **`Issue`** / SQLite cache schema — untouched.

Confirmed against FR-010: analysis output (scoring, evidence, embeddings) is unchanged.
