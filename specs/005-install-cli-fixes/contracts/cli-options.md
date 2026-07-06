# Contract: CLI Option Placement

Covers FR-005, FR-006, FR-007. Defines where `--db`, `--ollama-host`, and `--config` are accepted
and how their values resolve.

## Options in scope

| Option | Aliased to Config | Notes |
|--------|-------------------|-------|
| `--db PATH` | `Config.db_path` | SQLite cache/results file |
| `--ollama-host URL` | `Config.ollama_host` | Ollama base URL |
| `--config PATH` | (selects TOML file) | Path to the TOML config file |

## Placement contract

Each option MUST be accepted in **both** positions:

```
yt-issue-reviewer --db ./yir.db analyze --project P        # before subcommand (existing)
yt-issue-reviewer analyze --project P --db ./yir.db        # after subcommand  (NEW — documented)
```

Commands that MUST accept post-subcommand placement (every command the docs show them with):
`doctor`, `ingest`, `embed`, `analyze`, `show`, `runs`.

## Resolution precedence (unchanged behavior, FR-006)

For each option, the effective value is the first that is set:

1. Subcommand-level value (e.g. `analyze --db X`)
2. Group-level value (e.g. `--db X analyze`)
3. Environment variable (`YIR_DB`, `OLLAMA_HOST`)
4. TOML config file value
5. Built-in default

When the same option is given at both the group and subcommand level, the **subcommand-level value
wins** (rule 1 over rule 2). All other precedence (env > TOML > default) is exactly as today via
`Config.load(...)`.

## Acceptance checks

- `analyze --project P --db ./x.db --ollama-host http://h:11434` runs; the run uses `./x.db` and
  `http://h:11434`.
- `doctor --ollama-host http://h:11434` and `show --db ./x.db` are accepted (no "No such option").
- `--db A analyze --db B` resolves to `B`.
- With no `--db` anywhere and `YIR_DB` unset, the default `yir.db` is used (precedence intact).
- Every option-placement example in `README.md` and `docs/` executes without a "No such option"
  error.
