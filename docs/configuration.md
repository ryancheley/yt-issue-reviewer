# Configuration

Settings resolve in this precedence order (highest first):

1. Explicit CLI option (e.g. `--ollama-host`, `--min-score`)
2. Environment variable
3. Config file (`config.toml`)
4. Built-in default

## Environment variables

| Variable | Affects | Default |
|----------|---------|---------|
| `OLLAMA_HOST` | Ollama base URL | `http://127.0.0.1:11434` |
| `YIR_DB` | SQLite cache/results path | `yir.db` |

YouTrack auth is inherited from `youtrack-cli` (`~/.config/youtrack-cli/.env` or
`YOUTRACK_BASE_URL` / `YOUTRACK_TOKEN`) — this tool holds no YouTrack credentials.

## Config file (`config.toml`)

The config file is read from `~/.config/yt-issue-reviewer/config.toml` by default, or from
the path given with the global `--config PATH` option (there is no environment variable for
it). All keys are optional; unset keys fall back to the defaults below.

```toml
db_path = "yir.db"
ollama_host = "http://127.0.0.1:11434"
embedding_model = "nomic-embed-text"
label_model = "qwen2.5"
weight_semantic = 0.7
weight_structural = 0.3
min_score = 0.6
temporal_window_days = 7

[structural_weights]
shared_tags = 0.5
same_reporter = 0.2
temporal_proximity = 0.3
```

## Settings reference

| Setting | Default | Meaning |
|---------|---------|---------|
| `db_path` | `yir.db` | SQLite cache + results file |
| `ollama_host` | `http://127.0.0.1:11434` | Ollama base URL (localhost or Tailscale) |
| `embedding_model` | `nomic-embed-text` | Embedding model (768-dim); `mxbai-embed-large` also works |
| `label_model` | `qwen2.5` | Chat model for `--label` group labels |
| `weight_semantic` | `0.7` | Blend weight for cosine similarity |
| `weight_structural` | `0.3` | Blend weight for structural signals |
| `min_score` | `0.6` | Threshold below which pairs/groups are dropped |
| `temporal_window_days` | `7` | Window for the temporal-proximity signal |
| `structural_weights.shared_tags` | `0.5` | Sub-weight: shared tags/components |
| `structural_weights.same_reporter` | `0.2` | Sub-weight: same reporter |
| `structural_weights.temporal_proximity` | `0.3` | Sub-weight: created close in time |

The embedding model name + version and the weights are recorded per run (see
`runs`), so any analysis is reproducible. See [architecture](./architecture.md) for how
these combine into the relatedness score.
